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
        Searches for a music preview URL on iTunes API.
        """
        search_term = f"{song_title} {artist_name}"
        try:
            res = requests.get(
                f"https://itunes.apple.com/search?term={search_term}&entity=song&limit=1",
                timeout=3.0,
            )
            res.raise_for_status()
            data = res.json()
            if data.get("results"):
                return data["results"][0].get("previewUrl", "")
        except Exception as e:
            print(f"Error fetching iTunes preview: {e}")
            return ""
