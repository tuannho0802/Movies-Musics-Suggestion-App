import os
import pandas as pd
import requests
from huggingface_hub import HfApi, hf_hub_download
from app.engine import RecommendationEngine

# Config Constants
TMDB_KEY = os.getenv("TMDB_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")
REPO_ID = "tuannho080213/media_data"
CACHE_DIR = "data_cache"

# SonarQube Fix: Defined constants for duplicated literals
MUSIC_DATA_FILE = "music_data.csv"
MOVIES_DATA_FILE = "TMDB_movie_dataset_v11.csv"
EMBEDDINGS_FILE = "media_embeddings.pt"

def fetch_trending_movies():
    print("Fetching trending movies from TMDB...")
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_KEY}"
    res = requests.get(url).json()
    new_movies = []
    for m in res.get("results", []):
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
                "poster_path": poster_url,
            }
        )
    return pd.DataFrame(new_movies)


def fetch_new_music():
    print("Fetching 2024-2025 hits from iTunes...")
    tracks = []
    for year in ["2024", "2025", "Billboard", "Indie", "Top100"]:
        url = f"https://itunes.apple.com/search?term={year}&entity=song&limit=50"
        res = requests.get(url).json()
        for t in res.get("results", []):
            tracks.append(
                {
                    "track_name": t.get("trackName"),
                    "artist": t.get("artistName"),  # Matches your CSV column 'artist'
                    "album_cover_url": t.get("artworkUrl100"),
                    "popularity": 90,
                    "track_genre": t.get("primaryGenreName"),
                }
            )
    return pd.DataFrame(tracks)


def sync():
    api = HfApi(token=HF_TOKEN)
    os.makedirs(CACHE_DIR, exist_ok=True)

    # 1. DOWNLOAD CURRENT DATA INTO CACHE
    print("Downloading current files...")
    music_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=MUSIC_DATA_FILE,
        repo_type="dataset",
        local_dir=CACHE_DIR,
    )
    movie_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=MOVIES_DATA_FILE,
        repo_type="dataset",
        local_dir=CACHE_DIR,
    )

    music_df = pd.read_csv(music_path)
    movie_df = pd.read_csv(movie_path)

    # 2. FETCH NEW CONTENT
    new_music = fetch_new_music()
    new_movies = fetch_trending_movies()

    # 3. MERGE & DEDUPLICATE
    updated_music = pd.concat([music_df, new_music]).drop_duplicates(
        subset=["track_name", "artist"], keep="first"
    )
    updated_movies = pd.concat([movie_df, new_movies]).drop_duplicates(
        subset=["title"], keep="first"
    )

    # 4. SAVE TO THE CACHE FOLDER
    music_save_path = os.path.join(CACHE_DIR, MUSIC_DATA_FILE)
    movie_save_path = os.path.join(CACHE_DIR, MOVIES_DATA_FILE)
    updated_music.to_csv(music_save_path, index=False)
    updated_movies.to_csv(movie_save_path, index=False)

    # 5. GENERATE EMBEDDINGS
    print("🔄 Generating fresh search index...")
    engine = RecommendationEngine()
    # Using the constants to build paths
    engine.init_data(movie_save_path, movie_save_path, music_save_path)

    # 6. UPLOAD EVERYTHING
    # Using constants for filenames in repo
    files_to_push = [
        (EMBEDDINGS_FILE, EMBEDDINGS_FILE),
        (music_save_path, MUSIC_DATA_FILE),
        (movie_save_path, MOVIES_DATA_FILE),
    ]

    for local_file, repo_file in files_to_push:
        if os.path.exists(local_file):
            print(f"Uploading {repo_file}...")
            api.upload_file(
                path_or_fileobj=local_file,
                path_in_repo=repo_file,
                repo_id=REPO_ID,
                repo_type="dataset",
            )
        else:
            print(f"⚠️ Warning: {local_file} not found, skipping upload.")

    print("✅ All data and embeddings synced successfully!")

if __name__ == "__main__":
    sync()
