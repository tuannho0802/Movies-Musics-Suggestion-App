import os
import requests
from functools import lru_cache
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_search import YoutubeSearch

class YoutubeToolset:
    def search_youtube(self, query):
        """
        Searches YouTube for videos based on a query.
        Returns a list of dictionaries with video details.
        """
        try:
            results = YoutubeSearch(query, max_results=5).to_dict()
            return results
        except Exception as e:
            print(f"Error searching YouTube: {e}")
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
        The lru_cache ensures we don't search the same movie twice in one session.
        """
        # Broaden the search query slightly to get better results
        search_query = f"{movie_title} trailer"
        if year:
            search_query += f" {year}"

        results = self.search_youtube(search_query)

        if not results:
            return None

        # Level 1: Look for "Official" and "Trailer" in the title (Best Match)
        for result in results:
            title_lower = result["title"].lower()
            if "trailer" in title_lower and "official" in title_lower:
                return f"https://www.youtube.com/watch?v={result['id']}"

        # Level 2: Look for just "Trailer"
        for result in results:
            if "trailer" in result["title"].lower():
                return f"https://www.youtube.com/watch?v={result['id']}"

        # Level 3: Fallback - Return the first result found so the button works
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
        search_terms.append(song_title) # Always try with just the song title as a fallback

        for term in search_terms:
            try:
                res = requests.get(
                    f"https://itunes.apple.com/search?term={term}&entity=song&limit=1",
                    timeout=3.0,
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
        """
        Searches TMDB for a movie poster image URL.
        """
        try:
            # Need to get TMDB API key from env
            tmdb_api_key = os.getenv("TMDB_API_KEY")
            if not tmdb_api_key:
                return ""
            res = requests.get(
                f"https://api.themoviedb.org/3/search/movie?api_key={tmdb_api_key}&query={movie_title}",
                timeout=3.0,
            )
            res.raise_for_status()
            data = res.json()
            if data.get("results") and data["results"][0].get("poster_path"):
                return f"https://image.tmdb.org/t/p/w500{data['results'][0]['poster_path']}"
        except Exception as e:
            print(f"Error fetching TMDB movie image: {e}")
            return ""
        return ""

    @lru_cache(maxsize=2048)
    def get_music_image_url(self, song_title, artist_name=""): # Added artist_name parameter
        """
        Searches iTunes for music artwork image URL with fallback queries.
        """
        search_terms = []
        if artist_name:
            search_terms.append(f"{song_title} {artist_name}")
        search_terms.append(song_title) # Always try with just the song title as a fallback

        for term in search_terms:
            try:
                res = requests.get(
                    f"https://itunes.apple.com/search?term={term}&entity=song&limit=1",
                    timeout=3.0,
                )
                res.raise_for_status()
                data = res.json()
                if data.get("results") and data["results"][0].get("artworkUrl100"):
                    # Return a higher resolution image
                    return data["results"][0]["artworkUrl100"].replace("100x100bb", "600x600bb")
            except Exception as e:
                print(f"Error fetching iTunes music image for '{term}': {e}")
        return ""
