import os
import pandas as pd
import requests
from huggingface_hub import HfApi, hf_hub_download
from app.engine import RecommendationEngine

# Config
TMDB_KEY = os.getenv("TMDB_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
REPO_ID = "tuannho080213/media_data"

# 1. Trigger the encoding locally on the GitHub Action runner
engine = RecommendationEngine()
engine.init_data("movies.csv", "new_movies.csv", "music.csv")

# 2. Upload the new .pt file back to the dataset
from huggingface_hub import HfApi

api = HfApi()
api.upload_file(
    path_or_fileobj="media_embeddings.pt",
    path_in_repo="media_embeddings.pt",
    repo_id="tuannho080213/media_data",
    repo_type="dataset",
    token=os.getenv("HF_TOKEN"),
)


def fetch_trending_movies():
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_KEY}"
    res = requests.get(url).json()
    new_movies = []
    for m in res.get("results", []):
        # Build the full poster URL so your app can actually show the image
        poster_url = (
            f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}"
            if m.get("poster_path")
            else ""
        )

        new_movies.append(
            {
                "title": m.get("title"),
                "overview": m.get("overview"),
                "vote_average": m.get("vote_average"),
                "release_date": m.get("release_date"),
                "poster_path": poster_url,  # Full URL
            }
        )
    return pd.DataFrame(new_movies)


def fetch_new_music():
    # iTunes search for 2024/2025 hits
    url = "https://itunes.apple.com/search?term=2025&entity=song&limit=30"
    res = requests.get(url).json()
    new_tracks = []
    for t in res.get("results", []):
        new_tracks.append(
            {
                "track_name": t.get("trackName"),
                "artist_name": t.get("artistName"),
                "album_cover_url": t.get("artworkUrl100"),
                "popularity": 80,
                "track_genre": t.get("primaryGenreName"),
            }
        )
    return pd.DataFrame(new_tracks)


def sync():
    api = HfApi(token=HF_TOKEN)

    # --- UPDATE MUSIC ---
    print("Syncing Music...")
    music_path = hf_hub_download(
        repo_id=REPO_ID, filename="music_data.csv", repo_type="dataset"
    )
    music_df = pd.read_csv(music_path)
    new_music = fetch_new_music()
    # Merge and drop duplicates based on track and artist
    updated_music = pd.concat([music_df, new_music]).drop_duplicates(
        subset=["track_name", "artist_name"], keep="first"
    )
    updated_music.to_csv("music_data_updated.csv", index=False)

    api.upload_file(
        path_or_fileobj="music_data_updated.csv",
        path_in_repo="music_data.csv",
        repo_id=REPO_ID,
        repo_type="dataset",
    )

    # --- UPDATE MOVIES ---
    print("Syncing Movies...")
    # Note: Using your TMDB_movie_dataset_v11.csv as the base
    movie_path = hf_hub_download(
        repo_id=REPO_ID, filename="TMDB_movie_dataset_v11.csv", repo_type="dataset"
    )
    movie_df = pd.read_csv(movie_path)
    new_movies = fetch_trending_movies()
    # Merge and drop duplicates
    updated_movies = pd.concat([movie_df, new_movies]).drop_duplicates(
        subset=["title"], keep="first"
    )
    updated_movies.to_csv("movie_data_updated.csv", index=False)

    api.upload_file(
        path_or_fileobj="movie_data_updated.csv",
        path_in_repo="TMDB_movie_dataset_v11.csv",
        repo_id=REPO_ID,
        repo_type="dataset",
    )
    print("Done!")


if __name__ == "__main__":
    sync()
