# Gemini Project Summary

## Project Overview

This project is a media discovery engine that allows users to find movies and music based on a query. It provides a web interface where users can see trending media, search for media, and play trailers and previews.

## Technologies Used

-   **Backend:** FastAPI, Python
-   **Frontend:** HTML, CSS, JavaScript
-   **Machine Learning:** SentenceTransformers for semantic search
-   **Data:** Pandas for data manipulation
-   **APIs:** YouTube API for trailers, iTunes API for music previews, TMDB API for movie posters

## date progress 12/28/2025 progress

### Initial Performance Optimization & Bug Fixes

-   **Frontend Audio Playback Fix (`static/script.js`):**
    -   Resolved a bug where music previews were not playing correctly due to a duplicated and less robust `attachAudioPlayerListeners` function. The more robust version, handling `play()` promises and loading states, was retained.
-   **Backend Caching for YouTube Trailers (`app/youtube_tool.py`):**
    -   Implemented `functools.lru_cache` on the `find_trailer_url` function to cache YouTube search results, reducing redundant external API calls.
-   **Backend Caching for API Endpoints (`app/main.py`):
    -   Introduced `cachetools.TTLCache` for `/trending` and `/search` API endpoints to improve response times. Trending cache had a 1-hour TTL, and search cache had a 5-minute TTL. (Note: Caching for `/trending` was later removed based on user feedback for fresh results).
-   **Dependency Management:**
    -   Created `requirements.txt` to explicitly list project dependencies (`fastapi`, `pandas`, `torch`, `sentence-transformers`, `youtube-transcript-api`, `youtube-search`, `httpx`, `uvicorn`, `python-dotenv`, `cachetools`, `requests`).
-   **Code Quality & Typo Fixes:**
    -   Corrected a typo in `app/youtube_tool.py` (`functfunctools` to `functools`).
    -   Ensured `requests` library was properly integrated and installed.

### Addressing Startup Errors & Music Preview Performance

-   **Fixed Backend Indentation Error (`app/main.py`):**
    -   Resolved an `IndentationError` on line 91 of `app/main.py`, which was preventing the application from starting. This was caused by incorrect indentation within an `elif` block.
-   **Optimized Music Preview Loading (Lazy Loading):**
    -   **Backend (`app/main.py`):**
        -   Created a new `/preview` API endpoint to fetch music preview URLs *on demand*. This endpoint utilizes the cached `get_music_preview_url` from `youtube_tool.py`.
        -   Removed the "eager" fetching of `preview_url` from the `get_details_parallel` function to prevent initial slowdowns and excessive network requests.
    -   **Frontend (`static/script.js`):**
        -   Modified the `renderCards` function to no longer embed `preview_url` directly. Instead, "Play Preview" buttons now carry `data-title` and `data-artist` attributes.
        -   Rewrote `attachAudioPlayerListeners` to:
            -   Fetch the preview URL from the new `/preview` endpoint only when the "Play Preview" button is clicked.
            -   Display a "⌛ Loading..." state during the fetch.
            -   Dynamically create and append the `<audio>` element with the fetched URL.

### Final Refinements Based on User Feedback

-   **Trending Results Shuffling (`app/main.py`):**
    -   Removed caching from the `/trending` endpoint to ensure trending results are truly randomized on each load, as per user request for dynamic content.
    -   Applied `random.shuffle(results)` to all trending types for consistent shuffling.
-   **Improved "Play Preview" Robustness (`static/script.js`):**
    -   Added a "loading" guard to the `attachAudioPlayerListeners` function to prevent race conditions and unintended behavior when the "Play Preview" button is clicked multiple times rapidly during loading.
    -   Removed a redundant `originalLoadMoreData` declaration.
-   **Fixed UI Rendering Issue (`static/script.js`):**
    -   Corrected a critical bug in the `renderCards` function by restoring the `container.innerHTML += ...` line, which was accidentally removed. This ensures that generated media cards are correctly appended to the DOM and displayed in the UI.

### date progress 12/28/2025 progress - Continued

### Addressing Infinite Scroll Duplication and Missing Movie Details

-   **Backend Pagination for Search Results (`app/engine.py`, `app/main.py`):**
    -   Implemented pagination logic in `engine.search_advanced` by adding `page` and `page_size` parameters.
    -   Modified `search_api` in `app/main.py` to accept and pass these pagination parameters, and to remove the `/search` endpoint's caching.
-   **Enhanced Genre Tag Loading (`app/database.py`):**
    -   Updated the `build_subset` function in `app/database.py` to correctly extract genre information by checking for the `genres_list` column in movie datasets, resolving the "Media" tag issue.
-   **Consistent "Play Trailer" Button Display (`static/script.js`):**
    -   Modified `renderCards` to always display the "Play Trailer" button for movies. If a `trailer_url` is unavailable, the button appears in a disabled state as "🚫 Trailer N/A".
-   **Robust Data Handling for Movie Details (`app/main.py`, `app/engine.py`):**
    -   Refactored `engine.search_advanced` to return a pandas DataFrame instead of a list of dictionaries, unifying the data structure for both trending and search results.
    -   Simplified `get_details_parallel` in `app/main.py` to consistently process pandas Series objects, eliminating data type inconsistencies that led to missing genres and trailer URLs.
    -   Removed side-effect (`_update_media_df_with_url`) from `get_details_parallel` to prevent potential race conditions and ensure pure function execution in a concurrent environment.

### Final Fix for Missing Trailer URLs & Debug Cleanup

-   **Corrected `MediaResult` Model (`app/models.py`):**
    -   Added the `trailer_url: Optional[str] = None` field to the `MediaResult` Pydantic model. This crucial fix ensures that the `trailer_url` is no longer stripped out by FastAPI's response validation, allowing the backend's successfully fetched trailer URLs to reach the frontend.
-   **Removed Debug Logs (`app/main.py`, `static/script.js`):**
    -   Removed all temporary `print` statements from `app/main.py` and `console.log` statements from `static/script.js` that were added for debugging purposes. This restores the code to its clean, production-ready state.

### Image Loading Optimization

-   **Backend Image URL Pre-fetching (`app/youtube_tool.py`, `app/main.py`):**
    -   Introduced cached helper functions (`get_movie_image_url`, `get_music_image_url`) in `app/youtube_tool.py` for efficient, centralized retrieval and caching of image URLs from external APIs (TMDB, iTunes).
    -   Modified `get_details_parallel` in `app/main.py` to proactively call these new backend functions, ensuring `item.image_url` is populated in the API response.
-   **Frontend Image Handling Simplification (`static/script.js`):**
    -   Streamlined `fetchImage` to directly utilize the `item.image_url` already provided by the backend response, eliminating redundant frontend API calls.
    -   Updated `renderCards` to correctly pass the pre-fetched `item.image_url` to the simplified `fetchImage` function.
-   **Music Preview & Image Fetching Robustness:**
    -   Refined iTunes Search Queries (`app/youtube_tool.py`): Modified `get_music_preview_url` and `get_music_image_url` to implement a fallback mechanism, trying both `song_title` with `artist_name`, then just `song_title` if the first attempt fails. This improves the success rate of finding preview URLs and images.
    -   Enhanced `get_music_image_url` (`app/youtube_tool.py`, `app/main.py`): Updated `get_music_image_url` to accept `artist_name` as a parameter for more precise image searches, and modified the call to `get_music_image_url` in `get_details_parallel` to correctly pass the `artist_name` (from `item_dict["year"]`).

These continuous refinements ensure a more robust, efficient, and user-friendly media discovery application.

## date progress 12/30/2025 progress

### UI/UX Overhaul

- **Responsive Design:** Implemented a fully responsive design that adapts the layout for desktop, tablet, and mobile devices.
    - The grid of movie/music cards now adjusts automatically to the screen size, showing 4+ columns on desktop, 3-4 on tablets, and a clean 2-column layout on mobile.
- **Dynamic "Facebook-Style" Search Bar:**
    - The main search bar is now dynamic on all devices. It smoothly hides when scrolling down to maximize content visibility and reappears instantly when scrolling up.
- **Mobile Scrolling Fix:** Resolved a critical bug that was preventing smooth scrolling on mobile devices.
- **Improved Mobile Search:** The search input and button now stack vertically on mobile screens for a more user-friendly and tappable interface.

## date progress 12/31/2025 progress

### Advanced Autocomplete Feature Implementation

-   **Backend (`app/engine.py`):**
    -   Added `init_data` method to `RecommendationEngine` to load media data using `DataLoader` and prepare embeddings.
    -   Implemented `autocomplete_search` method for fuzzy title-based suggestions, returning rich metadata (ID, title, type, year/artist, initial image_url).
-   **Backend (`app/main.py`):**
    -   Modified `startup_event` to correctly use `engine.init_data` for data loading.
    -   Removed `local_dir_use_symlinks=False` from `hf_hub_download` calls to eliminate UserWarnings.
    -   Implemented the `/autocomplete` endpoint:
        -   Calls `engine.autocomplete_search` to get raw suggestions.
        -   Asynchronously fetches `image_url` for movie and music items using `youtube_tool.get_movie_image_url` and `youtube_tool.get_music_image_url`.
        -   Groups and limits results to top 3 movies and top 3 music items.
        -   Returns a structured JSON response with rich metadata.
-   **Backend (`app/youtube_tool.py`):**
    -   Reverted temporary debugging `print` statements in `get_movie_image_url`.
    -   Confirmed correct integration and reliance on `TMDB_API_KEY` (user-provided in `.env`).
-   **Frontend (`static/index.html`):**
    -   Ensured the presence of `<div id="suggestions-list"></div>` for autocomplete suggestions.
    -   Added `<div id="single-result-display"></div>` for prominently displaying a single selected media card.
-   **Frontend (`static/script.js`):**
    -   Initialized autocomplete state variables (`autocompleteCache`, `focusedIndex`, `autocompleteSuggestions`).
    -   Implemented `highlightMatch` function for keyword highlighting.
    -   Implemented `renderSuggestions`: Processes grouped data, displays category headers, icons, and thumbnails, uses `highlightMatch`, and stores full item objects.
    -   Implemented `autocomplete(query)`: Includes client-side caching, min search length (3 chars), and skeleton loaders.
    -   Implemented `selectSuggestion(index)`: Gets full item, updates `userInput`, clears suggestions, and calls `displaySingleMediaCard(item)`.
    -   Implemented `clearSuggestions()`.
    -   Implemented `displaySingleMediaCard(item)`: Hides other sections, shows "Hey, this is what you're looking for!" message, fetches full details via `/search`, renders a single card, and includes a "Back to Search Results" button.
    -   Implemented `clearSingleResultAndRunSearch()`: Clears single result display and triggers `runSearch()`.
    -   Updated event listeners: `debouncedSearch` calls `autocomplete`, `userInput` `keydown` handles arrow navigation and `Enter` selection (passing `index`), global `click` listener clears suggestions.
    -   Updated `clearSearch`, `loadAllTrending`, `runSearch` to correctly hide/show `single-result-display`.
-   **Frontend (`static/style.css`):**
    -   Added comprehensive styles for autocomplete suggestions (`#suggestions-list`, `.suggestion-group-header`, `.suggestion-item`, `.suggestion-thumbnail`, `.highlight-match`, `.autocomplete-active`).
    -   Added styles for skeleton loaders (`.skeleton-loader`).
    -   Added styles for the single media card display (`#single-result-display`, `.single-card-view`, `.you-looking-for-message`, `.back-to-search-btn`).
    -   Ensured mobile responsiveness for all new UI elements.
-   **Dependencies (`requirements.txt`):**
    -   Added `Pillow` to `requirements.txt` as an indirect dependency for robustness.

These updates significantly enhance the user experience by providing a rich, interactive, and performant autocomplete search feature, addressing previous image loading issues, and cleaning up server warnings.

## date progress 01/02/2026 progress

### Music Search Accuracy Improvement

-   **Backend (`app/engine.py`):**
    -   Modified the `search_advanced` function to prioritize exact matches for music.
    -   Implemented a strict exact match for `title` and `artist` when `media_type` is "music", ensuring the correct song is returned.
    -   Added a `normalize` function within the `RecommendationEngine` class and applied it to the search query's `title` and `artist` for consistent matching.
-   **Backend (`app/database.py`):**
    -   Modified the `build_subset` function to create and use `normalized_title` and `normalized_year` columns for music data, ensuring that the `media_df` stores original human-readable titles while using normalized values for internal matching.
    -   Added the `id` column to the `music_df` DataFrame in the `build_subset` function to ensure that the function works correctly.
-   **Frontend (`static/script.js`):**
    -   Modified the `displaySingleMediaCard` function to only show the "Hey, this is what you're looking for!" message for movies, improving user experience for music results.
