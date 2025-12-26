let CONFIG = {};
let currentType = "all";
const fallbackImage =
  "data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='500' height='750' viewBox='0 0 500 750'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%232a2a32'/%3E%3Cstop offset='100%25' stop-color='%23121214'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='500' height='750' fill='url(%23g)'/%3E%3Ctext x='50%25' y='90%25' fill='white' opacity='0.3' font-family='sans-serif' font-size='20' text-anchor='middle'%3EIMAGE UNAVAILABLE%3C/text%3E%3C/svg%3E";

// Initial Load
window.onload = async () => {
  await loadConfig();
  loadTrending(); // Show trending items on startup
};

async function loadConfig() {
  const res = await fetch("/config");
  CONFIG = await res.json();
}

// Logic to load Trending items from the backend
async function loadTrending() {
  const list = document.getElementById(
    "resultsList"
  );
  const title = document.getElementById(
    "resultTitle"
  );

  title.innerText = "🔥 Trending Now";
  list.innerHTML = '<div class="loader"></div>';

  try {
    const res = await fetch("/trending");
    const data = await res.json();
    renderCards(data.results, true);
  } catch (err) {
    list.innerHTML =
      "<p>Error loading trending items.</p>";
  }
}

let debounceTimer;
function debouncedSearch() {
  const query =
    document.getElementById("userInput").value;
  const clearBtn =
    document.getElementById("clearBtn");

  clearBtn.style.display =
    query.length > 0 ? "block" : "none";

  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    if (query.length >= 3) {
      runSearch();
    } else if (query.length === 0) {
      loadTrending(); // Revert to trending if input is empty
    }
  }, 800);
}

async function runSearch() {
  const query =
    document.getElementById("userInput").value;
  const list = document.getElementById(
    "resultsList"
  );
  const title = document.getElementById(
    "resultTitle"
  );

  title.innerText = `🔍 Results for "${query}"`;
  list.innerHTML = '<div class="loader"></div>';

  try {
    const response = await fetch(
      `/search?q=${encodeURIComponent(
        query
      )}&type=${currentType}`
    );
    const data = await response.json();
    renderCards(data.results, false);
  } catch (err) {
    list.innerHTML =
      "<p>Error connecting to server.</p>";
  }
}

// SHARED RENDERER for both Search and Trending
// UPDATED RENDERER: Handles Artist fallback for music and shows full descriptions
async function renderCards(
  results,
  isTrending
) {
  const list = document.getElementById(
    "resultsList"
  );
  list.innerHTML = "";

  if (!results || results.length === 0) {
    list.innerHTML = "<p>No matches found.</p>";
    return;
  }

  for (const item of results) {
    const imageUrl = await fetchImage(
      item.title,
      item.type
    );
    const genreDisplay = item.genre || "Media";

    // 1. FIX: Format the Year/Artist label
    // If it's music, 'item.year' actually contains the Artist name from your new database.py
    const metaLabel =
      item.year && item.year !== ""
        ? `(${item.year})`
        : "";

    // 2. Format the badge (Trending vs Search Match)
    const badge = isTrending
      ? `<span class="type-tag">${item.type}</span>`
      : `<span class="score-badge">${Math.round(
          item.score * 100
        )}% Match</span>`;

    list.innerHTML += `
            <div class="card">
                <div class="poster-container">
                    <img src="${imageUrl}" class="poster-img" onerror="this.src='${fallbackImage}';">
                </div>
                <div class="card-content">
                    ${badge}
                    <h3>${item.title} <span class="year-label">${metaLabel}</span></h3>
                    <div class="genre-badge">${genreDisplay}</div>
                    
                    <p class="description-text">${item.description}</p>
                </div>
            </div>
        `;
  }
}

async function fetchImage(title, type) {
  const cacheKey = `img_v4_${title
    .replaceAll(/\s+/g, "_")
    .toLowerCase()}`;
  const cached = localStorage.getItem(cacheKey);
  if (cached) return cached;

  try {
    if (
      type === "movie" &&
      CONFIG.TMDB_API_KEY
    ) {
      const res = await fetch(
        `https://api.themoviedb.org/3/search/movie?api_key=${
          CONFIG.TMDB_API_KEY
        }&query=${encodeURIComponent(title)}`
      );
      const data = await res.json();
      if (data.results?.[0]?.poster_path) {
        const url = `https://image.tmdb.org/t/p/w500${data.results[0].poster_path}`;
        localStorage.setItem(cacheKey, url);
        return url;
      }
    } else {
      const res = await fetch(
        `https://itunes.apple.com/search?term=${encodeURIComponent(
          title
        )}&entity=song&limit=1`
      );
      const data = await res.json();
      if (data.results?.[0]?.artworkUrl100) {
        const url =
          data.results[0].artworkUrl100.replace(
            "100x100bb",
            "600x600bb"
          );
        localStorage.setItem(cacheKey, url);
        return url;
      }
    }
  } catch (e) {}
  return fallbackImage;
}

// Filter button logic
document
  .querySelectorAll(".filter-btn")
  .forEach((btn) => {
    btn.addEventListener("click", (e) => {
      document
        .querySelectorAll(".filter-btn")
        .forEach((b) =>
          b.classList.remove("active")
        );
      e.target.classList.add("active");
      currentType = e.target.dataset.type;

      const query =
        document.getElementById(
          "userInput"
        ).value;
      if (query.length >= 3) runSearch();
      else loadTrending();
    });
  });

function clearSearch() {
  const input =
    document.getElementById("userInput");
  input.value = "";
  document.getElementById(
    "clearBtn"
  ).style.display = "none";
  loadTrending();
  input.focus();
}