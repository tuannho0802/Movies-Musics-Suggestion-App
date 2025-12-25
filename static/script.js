let CONFIG = {};

// 1. Fetch keys from backend on load
async function loadConfig() {
  const res = await fetch("/config");
  CONFIG = await res.json();
}
loadConfig();

let debounceTimer;

// This fixes the 'debouncedSearch is not defined' error
function debouncedSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    // Only auto-search if the user has typed at least 4 characters
    const query =
      document.getElementById(
        "userInput"
      ).value;
    if (query.length > 3) {
      runSearch();
    }
  }, 2000); // Increase to 2 seconds to be safe with API limits
}
// Local SVG fallback so you don't rely on external placeholder sites
// This is a built-in image that requires no internet to load
const fallbackImage =
  "data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='500' height='750' viewBox='0 0 500 750'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%232a2a32'/%3E%3Cstop offset='100%25' stop-color='%23121214'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='500' height='750' fill='url(%23g)'/%3E%3Cpath fill='%236200ee' opacity='0.2' d='M250 300c-60 0-110 50-110 110s50 110 110 110 110-50 110-110-50-110-110-110zm0 180c-38 0-70-32-70-70s32-70 70-70 70 32 70 70-32 70-70 70z'/%3E%3Ctext x='50%25' y='90%25' fill='white' opacity='0.3' font-family='sans-serif' font-size='20' text-anchor='middle'%3EIMAGE UNAVAILABLE%3C/text%3E%3C/svg%3E";

async function fetchImage(title, type) {
  // 1. Check LocalStorage Cache first
  const cacheKey = `img_v3_${title
    .replace(/\s+/g, "_")
    .toLowerCase()}`;
  const cached = localStorage.getItem(cacheKey);
  if (cached) return cached;

  try {
    if (type === "movie") {
      // Use the key from CONFIG (loaded from the backend)
      const apiKey = CONFIG.TMDB_API_KEY;
      if (!apiKey) return fallbackImage;

      const res = await fetch(
        `https://api.themoviedb.org/3/search/movie?api_key=${apiKey}&query=${encodeURIComponent(
          title
        )}`
      );
      const data = await res.json();

      if (data.results?.[0]?.poster_path) {
        const url = `https://image.tmdb.org/t/p/w500${data.results[0].poster_path}`;
        localStorage.setItem(cacheKey, url);
        return url;
      }
    } else {
      // iTunes API for Music - No Key Needed & No strict daily limit
      const res = await fetch(
        `https://itunes.apple.com/search?term=${encodeURIComponent(
          title
        )}&entity=song&limit=1`
      );
      const data = await res.json();

      if (data.results?.[0]?.artworkUrl100) {
        // High-resolution conversion
        const url =
          data.results[0].artworkUrl100.replace(
            "100x100bb",
            "600x600bb"
          );
        localStorage.setItem(cacheKey, url);
        return url;
      }
    }
  } catch (e) {
    console.error("Image fetch failed", e);
  }
  return fallbackImage;
}

//  fixes the ReferenceError
async function runSearch() {
  const query =
    document.getElementById("userInput").value;
  const list = document.getElementById(
    "resultsList"
  );

  if (query.length < 3) return; // Don't search for tiny queries

  // Show the spinner while waiting
  list.innerHTML = '<div class="loader"></div>';
  if (!query) return;

  try {
    const response = await fetch(
      `/search?q=${encodeURIComponent(query)}`
    );
    const data = await response.json();
    list.innerHTML = "";

    for (const item of data.results) {
      // Start with a local fallback immediately
      const imageUrl = await fetchImage(
        item.title,
        item.type
      );

      list.innerHTML += `
    <div class="card">
        <div class="poster-container" style="background-color: #1a1a1e; height: 300px;">
            <img src="${imageUrl}" 
                 class="poster-img" 
                 style="width: 100%; height: 100%; object-fit: cover;"
                 onerror="this.src='${fallbackImage}';">
        </div>
        <div class="card-content">
            <span class="score-badge">${Math.round(
              item.score * 100
            )}% Match</span>
            <span class="type-tag">${
              item.type
            }</span>
            <h3 style="margin: 10px 0; font-size: 1.1rem;">${
              item.title
            }</h3>
            <p style="font-size: 0.85rem; opacity: 0.8;">${item.description.substring(
              0,
              60
            )}...</p>
        </div>
    </div>
`;
    }
  } catch (err) {
    list.innerHTML =
      "<p>Error connecting to server.</p>";
  }
}
