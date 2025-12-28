import os
import random
import pandas as pd
import httpx
import math
import asyncio
import shutil # Import shutil
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .database import DataLoader
from .engine import RecommendationEngine
from .models import SearchResponse
from .youtube_tool import YoutubeToolset
from huggingface_hub import hf_hub_download

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
engine = RecommendationEngine()
youtube_tool = YoutubeToolset()

# HELPER: Remains exactly as your original
def clean_val(val, default=""):
    if val is None:
        return default
    if isinstance(val, float) and math.isnan(val):
        return default
    return str(val)



@app.on_event("startup")
async def startup_event():
    print("\n" + "=" * 50 + "\n🚀 INITIALIZING ENGINE\n" + "=" * 50)
    
    # Define the repository where your data is stored
    DATASET_REPO = "tuannho080213/media_data"
    DATA_CACHE_DIR = "data_cache" # Define a local cache directory

    # Ensure the cache directory exists
    os.makedirs(DATA_CACHE_DIR, exist_ok=True)
    
    # Define local paths for the datasets
    local_path1 = os.path.join(DATA_CACHE_DIR, "movies_metadata.csv")
    local_path2 = os.path.join(DATA_CACHE_DIR, "TMDB_movie_dataset_v11.csv")
    local_path3 = os.path.join(DATA_CACHE_DIR, "music_data.csv")

    try:
        # Check if files already exist locally, otherwise download
        if not os.path.exists(local_path1):
            print(f"Downloading movies_metadata.csv to {local_path1}")
            path1_temp = hf_hub_download(repo_id=DATASET_REPO, filename="movies_metadata.csv", repo_type="dataset")
            shutil.copyfile(path1_temp, local_path1) # Copy the downloaded file
            os.remove(path1_temp) # Remove the temporary file
            path1 = local_path1
        else:
            print(f"Using cached movies_metadata.csv from {local_path1}")
            path1 = local_path1

        if not os.path.exists(local_path2):
            print(f"Downloading TMDB_movie_dataset_v11.csv to {local_path2}")
            path2_temp = hf_hub_download(repo_id=DATASET_REPO, filename="TMDB_movie_dataset_v11.csv", repo_type="dataset")
            shutil.copyfile(path2_temp, local_path2)
            os.remove(path2_temp)
            path2 = local_path2
        else:
            print(f"Using cached TMDB_movie_dataset_v11.csv from {local_path2}")
            path2 = local_path2

        if not os.path.exists(local_path3):
            print(f"Downloading music_data.csv to {local_path3}")
            path3_temp = hf_hub_download(repo_id=DATASET_REPO, filename="music_data.csv", repo_type="dataset")
            shutil.copyfile(path3_temp, local_path3)
            os.remove(path3_temp)
            path3 = local_path3
        else:
            print(f"Using cached music_data.csv from {local_path3}")
            path3 = local_path3

        # Pass these (potentially cached) paths to your DataLoader
        data = DataLoader.load_media(path1, path2, path3)
        
        if not data.empty:
            engine.media_df = data
            if engine.embeddings is None:
                print("🛠️ No embeddings found, building new ones...")
                engine._prepare_embeddings()
            print(f"✅ SUCCESS: Loaded {len(data)} items.")
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch data from Hub: {e}")
    
    print("=" * 50 + "\n")

# --- THE OPTIMIZATION WORKER ---
async def get_details_parallel(client, item):
    """Processes a single item (pd.Series) and ensures all URLs are present."""

    # 1. Start with the base data
    item_dict = {
        "title": clean_val(item.get("title")),
        "year": clean_val(item.get("year")),
        "type": clean_val(item.get("type")),
        "description": clean_val(item.get("description")),
        "genre": clean_val(item.get("genre")),
        "popularity": int(round(float(item.get("popularity", 0)))),
        "score": float(item.get("score", 1.0)),
        # Initial image_url from the dataframe/dict
        "image_url": clean_val(item.get("image_url", "")),
    }

    # If image_url is still empty, try to fetch it from external sources
    if not item_dict["image_url"]:
        if item_dict["type"] == "movie":
            item_dict["image_url"] = await asyncio.to_thread(
                youtube_tool.get_movie_image_url, item_dict["title"]
            )
        elif item_dict["type"] == "music":
            item_dict["image_url"] = await asyncio.to_thread(
                youtube_tool.get_music_image_url, item_dict["title"], item_dict["year"]
            )

    # 2. Fix Movie Trailers
    if item_dict["type"] == "movie":
        # Check if URL already exists in the item
        trailer_url = clean_val(item.get("trailer_url", ""))

        if not trailer_url:
            # Search YouTube if missing (this function is cached)
            trailer_url = await asyncio.to_thread(
                youtube_tool.find_trailer_url, item_dict["title"], item_dict["year"]
            )
        
        # This is the final URL for the response
        item_dict["trailer_url"] = clean_val(trailer_url)

    # 3. Handle Music Previews (On-demand via /preview endpoint)
    if item_dict["type"] == "music":
        item_dict["preview_url"] = ""

    return item_dict

@app.get("/preview")
async def get_preview_url(title: str, artist: str):
    """New endpoint to fetch a music preview URL on-demand."""
    preview_url = await asyncio.to_thread(
        youtube_tool.get_music_preview_url, title, artist
    )
    if preview_url:
        _update_media_df_with_url("music", title, artist, "preview_url", preview_url)
        return {"url": preview_url}
    return {"url": None}


# --- API Endpoints ---


@app.get("/trending")
async def get_trending(type: str = "all", limit: int = 15, page: int = 1):
    if engine.media_df is None:
        return {"results": []}

    if type == "movie":
        pool = engine.media_df[engine.media_df["type"] == "movie"]
    elif type == "music":
        pool = engine.media_df[engine.media_df["type"] == "music"]
    else:
        pool = engine.media_df

    sample = pool.nlargest(250, "popularity").sample(n=min(limit, len(pool)))

    async with httpx.AsyncClient() as client:
        tasks = [get_details_parallel(client, item) for _, item in sample.iterrows()]
        results = await asyncio.gather(*tasks)

    random.shuffle(results)
    return {"results": results}


@app.get("/search", response_model=SearchResponse)
async def search_api(q: str, type: str = "all", page: int = 1):
    results_df = engine.search_advanced(query=q, media_type=type, page=page)

    if results_df.empty:
        return {"query": q, "count": 0, "results": []}

    async with httpx.AsyncClient() as client:
        tasks = [
            get_details_parallel(client, item) for _, item in results_df.iterrows()
        ]
        formatted = await asyncio.gather(*tasks)

    return {"query": q, "count": len(formatted), "results": formatted}


@app.get("/config")
def get_config():
    return {"TMDB_API_KEY": os.getenv("TMDB_API_KEY", "")}

# Your original update logic
def _update_media_df_with_url(media_type, title, year, url_type, url):
    if engine.media_df is not None:
        url = clean_val(url)
        idx = engine.media_df[
            (engine.media_df["title"] == title) & (engine.media_df["year"] == year)
        ].index
        if not idx.empty:
            engine.media_df.loc[idx, url_type] = url

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")
