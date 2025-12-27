from youtube_transcript_api import YouTubeTranscriptApi
from youtube_search import YoutubeSearch

class YoutubeToolset:
    def search_youtube(self, query):
        """
        Searches YouTube for videos based on a query.
        Returns a list of dictionaries with video details (id, title, long_desc, channel, duration, views, publish_time, url, image, thumbnails).
        """
        try:
            results = YoutubeSearch(query, max_results=5).to_dict()
            return results
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return []

    def get_video_transcript(self, video_id):
        """
        Retrieves the transcript of a YouTube video.
        Returns a string containing the full transcript.
        """
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = " ".join([item["text"] for item in transcript_list])
            return transcript
        except Exception as e:
            print(f"Error getting transcript for video {video_id}: {e}")
            return None

    def find_trailer_url(self, movie_title, year=None):
        """
        Searches for a movie trailer on YouTube.
        Prioritizes official trailers and includes the year in the search query if provided.
        Returns the URL of the most relevant trailer found, or None if not found.
        """
        search_query = f"{movie_title} official trailer"
        if year:
            search_query += f" {year}"

        results = self.search_youtube(search_query)

        if not results:
            return None

        # Look for the most relevant result
        for result in results:
            if "trailer" in result["title"].lower() and "official" in result["title"].lower():
                return f"https://www.youtube.com/watch?v={result['id']}"
        
        # If no "official trailer" found, return the first one that seems like a trailer
        for result in results:
            if "trailer" in result["title"].lower():
                return f"https://www.youtube.com/watch?v={result['id']}"

        # Otherwise, just return the first video
        if results:
            return f"https://www.youtube.com/watch?v={results[0]['id']}"
            
        return None