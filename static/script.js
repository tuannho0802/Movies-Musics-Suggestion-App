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
let currentTrendingType = "";
// -------------------------

// --- Autocomplete State ---
const autocompleteCache = new Map();
let focusedIndex = -1;
let autocompleteSuggestions = [];
// -------------------------

function highlightMatch(text, query) {
  if (!query) return text;
  const regex = new RegExp(`(${query})`, 'gi');
  return text.replace(regex, '<span class="highlight-match">$1</span>');
}

async function loadConfig() {
  const res = await fetch("/config");
  CONFIG = await res.json();
}

async function loadTrending(type, containerId) {
  const list =
    document.getElementById(containerId);
  if (!list) return;
  list.innerHTML = '<div class="loader"></div>';

  try {
    const res = await fetch(
      `/trending?type=${type}&limit=5`
    );
    const data = await res.json();
    renderCards(
      data.results,
      list,
      true,
      false
    ); // Not appending here
  } catch (err) {
    list.innerHTML =
      "<p>Error loading trending items.</p>";
  }
}

window.onload = async () => {
  await loadConfig();
  loadTrending("movie", "trendingMovies");
  loadTrending("music", "trendingMusic");
};

let currentPlayingAudio = null; // Global variable to track the currently playing audio
let audioCounter = 0; // To generate unique IDs for audio elements


async function fetchImage(
  item_image_url,
  title
) {
  // item_image_url is the image URL provided by the backend
  const cacheKey = `img_v4_${title
    .replaceAll(/\s+/g, "_")
    .toLowerCase()}`;
  const cached = localStorage.getItem(cacheKey);
  if (cached) return cached;

  if (item_image_url) {
    localStorage.setItem(
      cacheKey,
      item_image_url
    );
    return item_image_url;
  }

  return fallbackImage;
}


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
      item.image_url,
      item.title
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
    if (item.type === "movie") {
      if (item.trailer_url) {
        mediaHtml = `<a href="${item.trailer_url}" target="_blank" class="play-trailer-btn">▶ Play Trailer</a>`;
      } else {
        mediaHtml = `<button class="play-trailer-btn disabled" disabled>🚫 Trailer N/A</button>`;
      }
    } else if (item.type === "music") {
      // LAZY LOADING: We don't add the src here anymore.
      // We add data attributes to the button to fetch the URL on-demand.
      audioCounter++;
      const audioId = `audio-${audioCounter}`;
      mediaHtml = `
            <div class="audio-player-container">
                <button class="custom-play-btn"
                        data-audio-id="${audioId}"
                        data-title="${item.title}"
                        data-artist="${item.year}">
                    ▶ Play Preview
                </button>
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
  // Attach event listeners and animations after all cards are rendered
  attachAudioPlayerListeners();
  initCardObserver();
}

function initCardObserver() {
  const cards = document.querySelectorAll('.card');
  const observer = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  cards.forEach(card => {
    observer.observe(card);
  });
}

function attachAudioPlayerListeners() {
  document
    .querySelectorAll(".custom-play-btn")
    .forEach((button) => {
      button.onclick = async (event) => {
        // Add a loading guard to prevent multiple clicks
        if (
          button.textContent.includes("Loading")
        ) {
          return;
        }

        const audioId = button.dataset.audioId;
        let audio =
          document.getElementById(audioId);

        // --- Pause any other playing audio ---
        if (
          currentPlayingAudio &&
          currentPlayingAudio.id !== audioId
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

        // --- Handle the clicked button's audio ---
        if (audio && !audio.paused) {
          // If it's already playing, pause it
          audio.pause();
          button.textContent = "▶ Play Preview";
          currentPlayingAudio = null;
        } else if (audio && audio.paused) {
          // If it's paused, play it
          try {
            await audio.play();
            button.textContent =
              "⏸ Pause Preview";
            currentPlayingAudio = audio;
          } catch (e) {
            console.error(
              "Playback failed:",
              e
            );
          }
        } else {
          // If there's no audio element yet, create and play it
          button.textContent = "⌛ Loading...";
          try {
            const title = button.dataset.title;
            const artist =
              button.dataset.artist;
            const res = await fetch(
              `/preview?title=${encodeURIComponent(
                title
              )}&artist=${encodeURIComponent(
                artist
              )}`
            );
            const data = await res.json();

            if (data.url) {
              audio = new Audio(data.url);
              audio.id = audioId;
              // Append it to the container so it's part of the DOM
              button.parentElement.appendChild(
                audio
              );

              await audio.play();
              button.textContent =
                "⏸ Pause Preview";
              currentPlayingAudio = audio;

              audio.onended = () => {
                button.textContent =
                  "▶ Play Preview";
                currentPlayingAudio = null;
              };
            } else {
              button.textContent =
                "🚫 Preview N/A";
              button.disabled = true;
            }
          } catch (error) {
            console.error(
              "Failed to fetch or play preview:",
              error
            );
            button.textContent = "⚠️ Error";
            button.disabled = true;
          }
        }
      };
    });
}


// --- Autocomplete Logic ---
function renderSuggestions(data, query) {
  const suggestionsList = document.getElementById('suggestions-list');
  suggestionsList.innerHTML = ''; // Clear previous suggestions
  focusedIndex = -1; // Reset focused item

  if (!data || (data.movies.length === 0 && data.music.length === 0)) {
    suggestionsList.style.display = 'none';
    autocompleteSuggestions = [];
    return;
  }

  autocompleteSuggestions = []; // Reset global suggestions list for keyboard nav

  // Render Movies
  if (data.movies.length > 0) {
    const movieHeader = document.createElement('div');
    movieHeader.className = 'suggestion-group-header';
    movieHeader.textContent = '🎬 Movies';
    suggestionsList.appendChild(movieHeader);
    data.movies.forEach(item => {
      const suggestionItem = document.createElement('div');
      suggestionItem.className = 'suggestion-item';
      suggestionItem.innerHTML = `
        <img src="${item.image_url || fallbackImage}" alt="${item.title}" class="suggestion-thumbnail">
        <div class="suggestion-text">
          <div class="suggestion-title">${highlightMatch(item.title, query)}</div>
          <div class="suggestion-meta">${item.year}</div>
        </div>
      `;
      suggestionItem.dataset.type = item.type;
      suggestionItem.dataset.title = item.title;
      // Store the full item in autocompleteSuggestions and pass its index
      autocompleteSuggestions.push(item);
      suggestionItem.dataset.index = autocompleteSuggestions.length - 1;
      suggestionItem.addEventListener('click', (event) => selectSuggestion(event.currentTarget.dataset.index));
      suggestionsList.appendChild(suggestionItem);
    });
  }

  // Render Music
  if (data.music.length > 0) {
    const musicHeader = document.createElement('div');
    musicHeader.className = 'suggestion-group-header';
    musicHeader.textContent = '🎶 Music';
    suggestionsList.appendChild(musicHeader);
    data.music.forEach(item => {
      const suggestionItem = document.createElement('div');
      suggestionItem.className = 'suggestion-item';
      suggestionItem.innerHTML = `
        <img src="${item.image_url || fallbackImage}" alt="${item.title}" class="suggestion-thumbnail">
        <div class="suggestion-text">
          <div class="suggestion-title">${highlightMatch(item.title, query)}</div>
          <div class="suggestion-meta">${item.year}</div>
        </div>
      `;
      suggestionItem.dataset.type = item.type;
      suggestionItem.dataset.title = item.title;
      // Store the full item in autocompleteSuggestions and pass its index
      autocompleteSuggestions.push(item);
      suggestionItem.dataset.index = autocompleteSuggestions.length - 1;
      suggestionItem.addEventListener('click', (event) => selectSuggestion(event.currentTarget.dataset.index));
      suggestionsList.appendChild(suggestionItem);
    });
  }

  suggestionsList.style.display = 'block';
}

async function autocomplete(query) {
  const suggestionsList = document.getElementById('suggestions-list');
  const userInput = document.getElementById('userInput');

  if (query.length < 3) {
    suggestionsList.style.display = 'none';
    autocompleteSuggestions = [];
    return;
  }

  // Check cache first
  if (autocompleteCache.has(query)) {
    renderSuggestions(autocompleteCache.get(query), query);
    return;
  }

  // Show skeleton loader
  suggestionsList.innerHTML = `
    <div class="suggestion-group-header">🎬 Movies</div>
    <div class="suggestion-item skeleton-loader"><div class="skeleton-thumbnail"></div><div class="skeleton-text-content"></div></div>
    <div class="suggestion-item skeleton-loader"><div class="skeleton-thumbnail"></div><div class="skeleton-text-content"></div></div>
    <div class="suggestion-item skeleton-loader"><div class="skeleton-thumbnail"></div><div class="skeleton-text-content"></div></div>
    <div class="suggestion-group-header">🎶 Music</div>
    <div class="suggestion-item skeleton-loader"><div class="skeleton-thumbnail"></div><div class="skeleton-text-content"></div></div>
    <div class="suggestion-item skeleton-loader"><div class="skeleton-thumbnail"></div><div class="skeleton-text-content"></div></div>
    <div class="suggestion-item skeleton-loader"><div class="skeleton-thumbnail"></div><div class="skeleton-text-content"></div></div>
  `;
  suggestionsList.style.display = 'block';


  try {
    const res = await fetch(`/autocomplete?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    autocompleteCache.set(query, data); // Cache results
    renderSuggestions(data, query);
  } catch (error) {
    console.error('Error fetching autocomplete suggestions:', error);
    suggestionsList.innerHTML = '<div class="suggestion-item">Error loading suggestions.</div>';
    suggestionsList.style.display = 'block';
  }
}

function selectSuggestion(index) { // Changed parameter to index
  const item = autocompleteSuggestions[index]; // Get the full item from the array
  document.getElementById('userInput').value = item.title;
  document.getElementById('suggestions-list').style.display = 'none';
  clearSuggestions(); // Clear suggestions after selection
  displaySingleMediaCard(item); // Call the new function
}

function clearSuggestions() {
  document.getElementById('suggestions-list').innerHTML = '';
  document.getElementById('suggestions-list').style.display = 'none';
  autocompleteSuggestions = [];
  focusedIndex = -1;
}

async function displaySingleMediaCard(item) {
  // Hide other sections
  document.querySelector('.trending-section').style.display = 'none';
  document.querySelector('.search-results-container').style.display = 'none';

  const singleResultDisplay = document.getElementById('single-result-display');
  singleResultDisplay.innerHTML = '<div class="loader"></div>';
  singleResultDisplay.style.display = 'block';

  try {
    const res = await fetch(`/search?q=${encodeURIComponent(item.title)}&type=${item.type}`);
    const data = await res.json();
    const fullItem = data.results[0]; // Assuming the first result is the one we want

    if (fullItem) {
      const imageUrl = await fetchImage(
        fullItem.image_url,
        fullItem.title
      );
      const genreDisplay = fullItem.genre || "Media";

      const metaLabel =
        fullItem.year && fullItem.year !== ""
          ? `(${fullItem.year})`
          : "";

      let mediaHtml = "";
      if (fullItem.type === "movie") {
        if (fullItem.trailer_url) {
          mediaHtml = `<a href="${fullItem.trailer_url}" target="_blank" class="play-trailer-btn">▶ Play Trailer</a>`;
        } else {
          mediaHtml = `<button class="play-trailer-btn disabled" disabled>🚫 Trailer N/A</button>`;
        }
      } else if (fullItem.type === "music") {
        audioCounter++;
        const audioId = `audio-${audioCounter}`;
        mediaHtml = `
              <div class="audio-player-container">
                  <button class="custom-play-btn"
                          data-audio-id="${audioId}"
                          data-title="${fullItem.title}"
                          data-artist="${fullItem.year}">
                      ▶ Play Preview
                  </button>
              </div>
          `;
      }
      
      singleResultDisplay.innerHTML = `
        <div class="single-card-view">
          <p class="you-looking-for-message">Hey, this is what you're looking for!</p>
          <div class="card">
            <div class="poster-container">
              <img src="${imageUrl}" class="poster-img" onerror="this.src='${fallbackImage}';">
            </div>
            <div class="card-content">
              <h3>${fullItem.title} <span class="year-label">${metaLabel}</span></h3>
              <div class="genre-badge">${genreDisplay}</div>
              <p class="description-text">${fullItem.description || ""}</p>
              ${mediaHtml}
            </div>
          </div>
          <button onclick="clearSingleResultAndRunSearch()" class="back-to-search-btn">Back to Search Results</button>
        </div>
      `;
      attachAudioPlayerListeners(); // Re-attach listeners for the new audio button
    } else {
      singleResultDisplay.innerHTML = `<p class="error-message">Could not find details for "${item.title}".</p>`;
    }
  } catch (error) {
    console.error('Error displaying single media card:', error);
    singleResultDisplay.innerHTML = `<p class="error-message">Error loading details for "${item.title}".</p>`;
  }
}

function clearSingleResultAndRunSearch() {
  document.getElementById('single-result-display').style.display = 'none';
  runSearch(); // Go back to the general search results
}

// --- Event Listeners and Infinite Scroll ---

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

      if (query.length >= 3) {
        runSearch();
      } else {
        if (currentType === "all") {
          document.querySelector(
            ".trending-section"
          ).style.display = "block";
          document.querySelector(
            ".search-results-container"
          ).style.display = "none";
        } else {
          loadAllTrending(currentType);
        }
      }
      clearSuggestions(); // Clear suggestions when filter changes
      document.getElementById('single-result-display').style.display = 'none'; // Hide single result on filter change
    });
  });

document
  .querySelectorAll(".see-more-btn")
  .forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const type = e.target.dataset.type;
      document
        .querySelectorAll(".filter-btn")
        .forEach((b) => {
          b.classList.remove("active");
          if (b.dataset.type === type)
            b.classList.add("active");
        });
      currentType = type;
      loadAllTrending(type);
      clearSuggestions(); // Clear suggestions when "see more" is clicked
      document.getElementById('single-result-display').style.display = 'none'; // Hide single result on "see more" click
    });
  });

function resetInfiniteScroll() {
  currentPage = 1;
  noMoreData = false;
  isLoading = false;
}

async function loadAllTrending(type) {
  resetInfiniteScroll();
  currentView = "trending";
  currentTrendingType = type;

  document.querySelector(
    ".trending-section"
  ).style.display = "none";
  document.querySelector(
    ".search-results-container"
  ).style.display = "none"; // Hide main search results
  document.getElementById('single-result-display').style.display = 'none'; // Hide single result

  const list = document.getElementById(
    "searchResultsList"
  );
  const title = document.getElementById(
    "searchResultsTitle"
  );
  title.innerText = `🔥 Trending ${
    type === "movie" ? "Movies" : "Music"
  }`;
  list.innerHTML = '<div class="loader"></div>';

  await loadMoreData();
}

async function runSearch() {
  resetInfiniteScroll();
  currentView = "search";
  currentQuery =
    document.getElementById("userInput").value;

  document.querySelector(
    ".trending-section"
  ).style.display = "none";
  document.getElementById('single-result-display').style.display = 'none'; // Hide single result
  document.querySelector(
    ".search-results-container"
  ).style.display = "block";

  const list = document.getElementById(
    "searchResultsList"
  );
  const title = document.getElementById(
    "searchResultsTitle"
  );
  title.innerText = `🔍 Results for "${currentQuery}"`;
  list.innerHTML = '<div class="loader"></div>';

  await loadMoreData();
}

async function loadMoreData() {
  if (isLoading || noMoreData) return;
  isLoading = true;

  const list = document.getElementById(
    "searchResultsList"
  );
  const loader = document.createElement("div");
  loader.className = "loader";
  list.appendChild(loader);

  let url = "";
  if (currentView === "trending") {
    url = `/trending?type=${currentTrendingType}&page=${currentPage}`;
  } else if (currentView === "search") {
    url = `/search?q=${encodeURIComponent(
      currentQuery
    )}&type=${currentType}&page=${currentPage}`;
  } else {
    isLoading = false;
    return;
  }

  try {
    const res = await fetch(url);
    const data = await res.json();

    if (
      data.results &&
      data.results.length > 0
    ) {
      renderCards(
        data.results,
        list,
        currentView === "trending",
        true
      );
      currentPage++;
    } else {
      noMoreData = true;
      const endMsg =
        document.createElement("p");
      endMsg.innerText =
        "You've reached the end!";
      endMsg.style.textAlign = "center";
      list.appendChild(endMsg);
    }
  } catch (err) {
    // Handle error, maybe show a message
  } finally {
    isLoading = false;
    const loader =
      list.querySelector(".loader");
    if (loader) loader.remove();
  }
}

// --- Enhanced Smart Scroll Logic ---
let lastScrollY = window.scrollY;
const scrollDelta = 5; // How many pixels to scroll before the bar reacts
const hideThreshold = 80; // Don't hide until user scrolls this far down

window.addEventListener(
  "scroll",
  () => {
    const searchSection =
      document.querySelector(".search-section");
    const currentScrollY = window.scrollY;

    // 1. Logic to show/hide the header
    if (currentScrollY <= 10) {
      // Force show when at the very top
      searchSection.classList.remove("hidden");
    } else if (currentScrollY < lastScrollY) {
      // SCROLLING UP: Always reveal
      searchSection.classList.remove("hidden");
    } else if (
      currentScrollY > lastScrollY &&
      currentScrollY > 100
    ) {
      // SCROLLING DOWN: Hide after passing 100px
      searchSection.classList.add("hidden");
    }

    lastScrollY = currentScrollY;

    // 2. Infinite Scroll Trigger
    const resultsContainer =
      document.querySelector(
        ".search-results-container"
      );
    if (
      resultsContainer.style.display ===
        "block" &&
      !isLoading &&
      !noMoreData
    ) {
      if (
        window.innerHeight + currentScrollY >=
        document.body.offsetHeight - 800
      ) {
        loadMoreData();
      }
    }
  },
  { passive: true }
);

function clearSearch() {
  const input = document.getElementById("userInput");
  input.value = "";
  document.getElementById("clearBtn").style.display = "none";
  
  document.querySelector('.trending-section').style.display = 'block';
  document.querySelector('.search-results-container').style.display = 'none';
  document.getElementById('single-result-display').style.display = 'none'; // Hide single result

  document.querySelectorAll(".filter-btn").forEach(b => {
    b.classList.remove("active");
    if(b.dataset.type === 'all') b.classList.add('active');
  });
  currentType = 'all';
  currentView = ''; // Reset view
  input.focus();
  clearSuggestions(); // Clear suggestions when clearing search
}

let debounceTimer;
function debouncedSearch() {
  const query = document.getElementById("userInput").value;
  const clearBtn = document.getElementById("clearBtn");
  clearBtn.style.display = query.length > 0 ? "block" : "none";

  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    if (query.length >= 3) {
      autocomplete(query); // Call autocomplete for suggestions
    } else if (query.length === 0) {
      clearSearch();
    } else {
      clearSuggestions(); // Clear suggestions if query is less than 3 chars
    }
  }, 300); // Shorter debounce for autocomplete responsiveness
}

document
  .getElementById("userInput")
  .addEventListener('input', debouncedSearch); // Use 'input' event for real-time suggestions


document.getElementById("userInput").addEventListener('keydown', (event) => {
  const suggestionsList = document.getElementById('suggestions-list');
  const items = suggestionsList.querySelectorAll('.suggestion-item');
  if (items.length === 0) return;

  if (event.key === 'ArrowDown') {
    event.preventDefault();
    focusedIndex = (focusedIndex + 1) % items.length;
    updateFocusedSuggestion(items);
    items[focusedIndex].scrollIntoView({ block: 'nearest' });
  } else if (event.key === 'ArrowUp') {
    event.preventDefault();
    focusedIndex = (focusedIndex - 1 + items.length) % items.length;
    updateFocusedSuggestion(items);
    items[focusedIndex].scrollIntoView({ block: 'nearest' });
  } else if (event.key === 'Enter') {
    event.preventDefault();
    if (focusedIndex > -1) {
      selectSuggestion(focusedIndex); // Pass index instead of title
    } else {
      runSearch(); // If no suggestion is focused, run normal search
    }
    clearSuggestions();
  } else if (event.key === 'Escape') {
    clearSuggestions();
  }
});

function updateFocusedSuggestion(items) {
  items.forEach((item, idx) => {
    if (idx === focusedIndex) {
      item.classList.add('autocomplete-active');
    } else {
      item.classList.remove('autocomplete-active');
    }
  });
}

// Global click listener to hide suggestions when clicking outside
document.addEventListener('click', (event) => {
  const searchSection = document.querySelector('.search-section'); // Corrected selector
  if (searchSection && !searchSection.contains(event.target)) {
    clearSuggestions();
  }
});