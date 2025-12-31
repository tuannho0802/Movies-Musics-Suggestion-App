import os
import requests
from functools import lru_cache
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_search import YoutubeSearch
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class YoutubeToolset:

    def __init__(self):
        # Setup a robust session to handle cloud network glitches
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        # Add a real browser header to avoid being blocked by YouTube
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def search_youtube(self, query):
        """
        Searches YouTube for videos based on a query.
        Returns a list of dictionaries with video details.
        """
        try:
            # We use the library but wrap it in a retry-aware environment
            results = YoutubeSearch(query, max_results=5).to_dict()
            return results
        except Exception as e:
            print(f"Error searching YouTube for '{query}': {e}")
            return []

    def get_video_transcript(self, video_id):
        """Retrieves the transcript of a YouTube video."""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = " ".join([item["text"] for item in transcript_list])
            return transcript
        except Exception as e:
            print(f"Error getting transcript for video {video_id}: {e}")
            return None

    @lru_cache(maxsize=1024)
    def find_trailer_url(self, movie_title, year=None):
        """
        Searches for a movie trailer on YouTube with multiple fallback levels.
        """
        search_query = f"{movie_title} trailer"
        if year:
            search_query += f" {year}"

        results = self.search_youtube(search_query)

        # NEW: If scraping fails, provide a direct search link as a last resort
        if not results:
            safe_query = search_query.replace(" ", "+")
            return f"https://www.youtube.com/results?search_query={safe_query}"

        # Level 1: Look for "Official" and "Trailer" in the title (Best Match)
        for result in results:
            title_lower = result.get("title", "").lower()
            if "trailer" in title_lower and "official" in title_lower:
                return f"https://www.youtube.com/watch?v={result['id']}"

        # Level 2: Look for just "Trailer"
        for result in results:
            if "trailer" in result.get("title", "").lower():
                return f"https://www.youtube.com/watch?v={result['id']}"

        # Level 3: Fallback - Return the first result found
        if results:
            return f"https://www.youtube.com/watch?v={results[0]['id']}"

        return None

    @lru_cache(maxsize=2048)
    def get_music_preview_url(self, song_title, artist_name=""):
        """
        Searches for a music preview URL on iTunes API with fallback queries.
        """
        search_terms = []
        if artist_name:
            search_terms.append(f"{song_title} {artist_name}")
        search_terms.append(song_title)

        for term in search_terms:
            try:
                # Use the robust session instead of bare requests.get
                res = self.session.get(
                    f"https://itunes.apple.com/search?term={term}&entity=song&limit=1",
                    timeout=5.0,
                )
                res.raise_for_status()
                data = res.json()
                if data.get("results"):
                    preview_url = data["results"][0].get("previewUrl")
                    if preview_url:
                        return preview_url
            except Exception as e:
                print(f"Error fetching iTunes preview for '{term}': {e}")
        return ""

    @lru_cache(maxsize=2048)
    def get_movie_image_url(self, movie_title):
        """Searches TMDB for a movie poster image URL."""
        try:
            tmdb_api_key = os.getenv("TMDB_API_KEY")
            if not tmdb_api_key:
                return ""
            res = self.session.get(
                f"https://api.themoviedb.org/3/search/movie?api_key={tmdb_api_key}&query={movie_title}",
                timeout=5.0,
            )
            res.raise_for_status()
            data = res.json()
            if data.get("results") and data["results"][0].get("poster_path"):
                return f"https://image.tmdb.org/t/p/w500{data['results'][0]['poster_path']}"
        except Exception as e:
            print(f"Error fetching TMDB movie image: {e}")
        return ""

    @lru_cache(maxsize=2048)
    def get_music_image_url(self, song_title, artist_name=""):
        """Searches iTunes for music artwork image URL."""
        search_terms = []
        if artist_name:
            search_terms.append(f"{song_title} {artist_name}")
        search_terms.append(song_title)

        for term in search_terms:
            try:
                res = self.session.get(
                    f"https://itunes.apple.com/search?term={term}&entity=song&limit=1",
                    timeout=5.0,
                )
                res.raise_for_status()
                data = res.json()
                if data.get("results") and data["results"][0].get("artworkUrl100"):
                    return data["results"][0]["artworkUrl100"].replace("100x100bb", "600x600bb")
            except Exception as e:
                print(f"Error fetching iTunes music image for '{term}': {e}")
        return ""