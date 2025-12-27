let CONFIG = {};
let currentType = "all";
const fallbackImage =
  "data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='500' height='750' viewBox='0 0 500 750'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' stop-color='%232a2a32'/%3E%3Cstop offset='100%25' stop-color='%23121214'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='500' height='750' fill='url(%23g)'/%3E%3Ctext x='50%25' y='90%25' fill='white' opacity='0.3' font-family='sans-serif' font-size='20' text-anchor='middle'%3EIMAGE UNAVAILABLE%3C/text%3E%3C/svg%3E";

// --- Infinite Scroll State ---
let currentPage = 1;
let isLoading = false;
let noMoreData = false;
let currentView = ''; // 'trending' or 'search'
let currentQuery = '';
let currentTrendingType = '';
let lastScrollY = window.scrollY;
// -------------------------

async function loadConfig() {
  const res = await fetch("/config");
  CONFIG = await res.json();
}

async function loadTrending(type, containerId) {
  const list = document.getElementById(containerId);
  if (!list) return;
  list.innerHTML = '<div class="loader"></div>';

  try {
    const res = await fetch(`/trending?type=${type}&limit=5`);
    const data = await res.json();
    renderCards(data.results, list, true, false); // Not appending here
  } catch (err) {
    list.innerHTML = "<p>Error loading trending items.</p>";
  }
}

window.onload = async () => {
  await loadConfig();
  loadTrending("movie", "trendingMovies");
  loadTrending("music", "trendingMusic");
};

let currentPlayingAudio = null; // Global variable to track the currently playing audio
let audioCounter = 0; // To generate unique IDs for audio elements

async function renderCards(
  results,
  container,
  isTrending,
  append = false
) {
  if (!append) {
    container.innerHTML = "";
  }

  // Remove loader if it exists
  const loader =
    container.querySelector(".loader");
  if (loader) loader.remove();

  if (!results || results.length === 0) {
    if (!append) {
      container.innerHTML =
        "<p>No matches found.</p>";
    }
    noMoreData = true; // Stop fetching if no results
    return;
  }

  for (const item of results) {
    const imageUrl = await fetchImage(
      item.title,
      item.type
    );
    const genreDisplay = item.genre || "Media";

    const metaLabel =
      item.year && item.year !== ""
        ? `(${item.year})`
        : "";

    const badge = isTrending
      ? `<span class="type-tag">${item.type}</span>`
      : `<span class="score-badge">${Math.round(
          item.score * 100
        )}% Match</span>`;

    const truncatedDescription =
      item.description &&
      item.description.length > 260
        ? item.description.substring(0, 260) +
          "..."
        : item.description || "";

    let mediaHtml = "";
    if (
      item.type === "movie" &&
      item.trailer_url
    ) {
      mediaHtml = `<a href="${item.trailer_url}" target="_blank" class="play-trailer-btn">▶ Play Trailer</a>`;
    } else if (
      item.type === "music" &&
      item.preview_url
    ) {
      audioCounter++;
      const audioId = `audio-${audioCounter}`;
      mediaHtml = `
            <div class="audio-player-container">
                <audio src="${item.preview_url}" id="${audioId}" class="audio-preview-element"></audio>
                <button class="custom-play-btn" data-audio-id="${audioId}">▶ Play Preview</button>
            </div>
        `;
    }

    container.innerHTML += `
      <div class="card">
        <div class="poster-container">
          <img src="${imageUrl}" class="poster-img" onerror="this.src='${fallbackImage}';">
        </div>
        <div class="card-content">
          ${badge}
          <h3>${item.title} <span class="year-label">${metaLabel}</span></h3>
          <div class="genre-badge">${genreDisplay}</div>
                    <div class="description-and-media">
                      <p class="description-text">${truncatedDescription}</p>
                      ${mediaHtml}
                    </div>
        </div>
      </div>
    `;
  }
  // Attach event listeners after all cards are rendered
  attachAudioPlayerListeners();
}

// Update this function in your script.js
function attachAudioPlayerListeners() {
  document
    .querySelectorAll(".custom-play-btn")
    .forEach((button) => {
      // We use an async function to handle the Play Promise
      button.onclick = async (event) => {
        const audioId = button.dataset.audioId;
        const audio =
          document.getElementById(audioId);

        if (!audio) return;

        // 1. Pause existing audio safely
        if (
          currentPlayingAudio &&
          currentPlayingAudio !== audio
        ) {
          currentPlayingAudio.pause();
          const prevButton =
            document.querySelector(
              `.custom-play-btn[data-audio-id="${currentPlayingAudio.id}"]`
            );
          if (prevButton)
            prevButton.textContent =
              "▶ Play Preview";
        }

        // 2. Toggle Play/Pause
        if (audio.paused) {
          try {
            const playPromise = audio.play();
            if (playPromise !== undefined) {
              button.textContent =
                "⌛ Loading...";
              await playPromise; // Wait for playback to actually start
              button.textContent =
                "⏸ Pause Preview";
              currentPlayingAudio = audio;
            }
          } catch (error) {
            if (error.name === "AbortError") {
              console.log(
                "Playback interrupted safely."
              );
            } else {
              console.error(
                "Playback failed:",
                error
              );
            }
          }
        } else {
          audio.pause();
          button.textContent = "▶ Play Preview";
          currentPlayingAudio = null;
        }

        audio.onended = () => {
          button.textContent = "▶ Play Preview";
          currentPlayingAudio = null;
        };
      };
    });
}

function attachAudioPlayerListeners() {
  document
    .querySelectorAll(".custom-play-btn")
    .forEach((button) => {
      button.onclick = (event) => {
        const audioId = button.dataset.audioId;
        const audio =
          document.getElementById(audioId);

        if (!audio) return;

        // If another audio is playing, pause it
        if (
          currentPlayingAudio &&
          currentPlayingAudio !== audio
        ) {
          currentPlayingAudio.pause();
          const prevButton =
            document.querySelector(
              `.custom-play-btn[data-audio-id="${currentPlayingAudio.id}"]`
            );
          if (prevButton) {
            prevButton.textContent =
              "▶ Play Preview";
          }
        }

        if (audio.paused) {
          audio.play();
          button.textContent =
            "⏸ Pause Preview";
          currentPlayingAudio = audio;
        } else {
          audio.pause();
          button.textContent = "▶ Play Preview";
          currentPlayingAudio = null;
        }

        audio.onended = () => {
          button.textContent = "▶ Play Preview";
          currentPlayingAudio = null;
        };
      };
    });
}

// Ensure listeners are re-attached when new content is loaded via infinite scroll
const originalLoadMoreData = loadMoreData;
loadMoreData = async () => {
  await originalLoadMoreData();
  attachAudioPlayerListeners();
};

async function fetchImage(title, type) {
  const cacheKey = `img_v4_${title.replaceAll(/\s+/g, "_").toLowerCase()}`;
  const cached = localStorage.getItem(cacheKey);
  if (cached) return cached;

  try {
    if (type === "movie" && CONFIG.TMDB_API_KEY) {
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
        `https://itunes.apple.com/search?term=${encodeURIComponent(title)}&entity=song&limit=1`
      );
      const data = await res.json();
      if (data.results?.[0]?.artworkUrl100) {
        const url = data.results[0].artworkUrl100.replace("100x100bb", "600x600bb");
        localStorage.setItem(cacheKey, url);
        return url;
      }
    }
  } catch (e) {}
  return fallbackImage;
}

document.querySelectorAll(".filter-btn").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
    e.target.classList.add("active");
    currentType = e.target.dataset.type;
    const query = document.getElementById("userInput").value;

    if (query.length >= 3) {
      runSearch();
    } else {
      if (currentType === 'all') {
        document.querySelector('.trending-section').style.display = 'block';
        document.querySelector('.search-results-container').style.display = 'none';
      } else {
        loadAllTrending(currentType);
      }
    }
  });
});

document.querySelectorAll(".see-more-btn").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    const type = e.target.dataset.type;
    document.querySelectorAll(".filter-btn").forEach(b => {
      b.classList.remove("active");
      if(b.dataset.type === type) b.classList.add('active');
    })
    currentType = type;
    loadAllTrending(type);
  });
});

function resetInfiniteScroll() {
    currentPage = 1;
    noMoreData = false;
    isLoading = false;
}

async function loadAllTrending(type) {
    resetInfiniteScroll();
    currentView = 'trending';
    currentTrendingType = type;

    document.querySelector('.trending-section').style.display = 'none';
    document.querySelector('.search-results-container').style.display = 'block';

    const list = document.getElementById("searchResultsList");
    const title = document.getElementById("searchResultsTitle");
    title.innerText = `🔥 Trending ${type === 'movie' ? 'Movies' : 'Music'}`;
    list.innerHTML = '<div class="loader"></div>';

    await loadMoreData();
}

async function runSearch() {
    resetInfiniteScroll();
    currentView = 'search';
    currentQuery = document.getElementById("userInput").value;

    document.querySelector('.trending-section').style.display = 'none';
    document.querySelector('.search-results-container').style.display = 'block';
    
    const list = document.getElementById("searchResultsList");
    const title = document.getElementById("searchResultsTitle");
    title.innerText = `🔍 Results for "${currentQuery}"`;
    list.innerHTML = '<div class="loader"></div>';
    
    await loadMoreData();
}

async function loadMoreData() {
    if (isLoading || noMoreData) return;
    isLoading = true;

    const list = document.getElementById("searchResultsList");
    const loader = document.createElement('div');
    loader.className = 'loader';
    list.appendChild(loader);

    let url = '';
    if (currentView === 'trending') {
        url = `/trending?type=${currentTrendingType}&page=${currentPage}`;
    } else if (currentView === 'search') {
        url = `/search?q=${encodeURIComponent(currentQuery)}&type=${currentType}&page=${currentPage}`;
    } else {
        isLoading = false;
        return;
    }
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        
        if (data.results && data.results.length > 0) {
            renderCards(data.results, list, currentView === 'trending', true);
            currentPage++;
        } else {
            noMoreData = true;
            const endMsg = document.createElement('p');
            endMsg.innerText = "You've reached the end!";
            endMsg.style.textAlign = 'center';
            list.appendChild(endMsg);
        }
    } catch (err) {
        // Handle error, maybe show a message
    } finally {
        isLoading = false;
        const loader = list.querySelector('.loader');
        if(loader) loader.remove();
    }
}


window.addEventListener('scroll', () => {
    const searchSection = document.querySelector('.search-section');
    const scrollY = window.scrollY;

    if (scrollY > lastScrollY && scrollY > 10) { // Added a buffer
        searchSection.classList.add('hidden');
    } else {
        searchSection.classList.remove('hidden');
    }
    lastScrollY = scrollY;

    // Don't trigger on main trending page
    if (document.querySelector('.search-results-container').style.display !== 'block') {
        return;
    }

    if ((window.innerHeight + scrollY) >= document.body.offsetHeight - 200) {
        loadMoreData();
    }
});


function clearSearch() {
  const input = document.getElementById("userInput");
  input.value = "";
  document.getElementById("clearBtn").style.display = "none";
  
  document.querySelector('.trending-section').style.display = 'block';
  document.querySelector('.search-results-container').style.display = 'none';
  
  document.querySelectorAll(".filter-btn").forEach(b => {
    b.classList.remove("active");
    if(b.dataset.type === 'all') b.classList.add('active');
  });
  currentType = 'all';
  currentView = ''; // Reset view
  input.focus();
}

let debounceTimer;
function debouncedSearch() {
  const query = document.getElementById("userInput").value;
  const clearBtn = document.getElementById("clearBtn");
  clearBtn.style.display = query.length > 0 ? "block" : "none";

  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    if (query.length >= 3) {
      runSearch();
    } else if (query.length === 0) {
      clearSearch();
    }
  }, 800);
}

document.getElementById("userInput").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        runSearch();
    }
});
