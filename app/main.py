import os
import random
import pandas as pd
import httpx
import math
import asyncio
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .database import DataLoader
from .engine import RecommendationEngine
from .models import SearchResponse
from .youtube_tool import YoutubeToolset
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv  # Import load_dotenv

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
engine = RecommendationEngine()
youtube_tool = YoutubeToolset()

def clean_val(val, default=""):
    if val is None:
        return default
    if isinstance(val, float) and math.isnan(val):
        return default
    return str(val)


def _update_media_df_with_url(media_type, title, year, url_type, url):
    if engine.media_df is not None:
        url = clean_val(url)
        idx = engine.media_df[
            (engine.media_df["title"] == title) & (engine.media_df["year"] == year)
        ].index
        if not idx.empty:
            engine.media_df.loc[idx, url_type] = url


@app.on_event("startup")
async def startup_event():
    print("\n" + "=" * 50 + "\n🚀 INITIALIZING ENGINE\n" + "=" * 50)

    # Load environment variables from .env file
    load_dotenv()
    # print(f"DEBUG: TMDB_API_KEY from environment: {os.getenv('TMDB_API_KEY')}")

    DATASET_REPO = "tuannho080213/media_data"
    DATA_CACHE_DIR = "data_cache" 

    os.makedirs(DATA_CACHE_DIR, exist_ok=True)

    local_path1 = os.path.join(DATA_CACHE_DIR, "movies_metadata.csv")
    local_path2 = os.path.join(DATA_CACHE_DIR, "TMDB_movie_dataset_v11.csv")
    local_path3 = os.path.join(DATA_CACHE_DIR, "music_data.csv")

    try:
        # Download files using local_dir
        hf_hub_download(
            repo_id=DATASET_REPO,
            filename="movies_metadata.csv",
            repo_type="dataset",
            local_dir=DATA_CACHE_DIR,
        )
        hf_hub_download(
            repo_id=DATASET_REPO,
            filename="TMDB_movie_dataset_v11.csv",
            repo_type="dataset",
            local_dir=DATA_CACHE_DIR,
        )
        hf_hub_download(
            repo_id=DATASET_REPO,
            filename="music_data.csv",
            repo_type="dataset",
            local_dir=DATA_CACHE_DIR,
        )

        # Initialize engine data
        engine.init_data(local_path1, local_path2, local_path3)

        if engine.media_df is not None:
            print(f"✅ SUCCESS: Loaded {len(engine.media_df)} items.")
        else:
            print("❌ ERROR: engine.media_df is None after init_data.")

    except Exception as e:
        print(f"❌ ERROR: Failed to fetch or load data: {e}")

    print("=" * 50 + "\n")

# --- THE OPTIMIZATION WORKER (remains unchanged) ---
async def get_details_parallel(client, item):
    """Processes a single item (pd.Series) and ensures all URLs are present."""

    item_dict = {
        "title": clean_val(item.get("title")),
        "year": clean_val(item.get("year")),
        "type": clean_val(item.get("type")),
        "description": clean_val(item.get("description")),
        "genre": clean_val(item.get("genre")),
        "popularity": int(round(float(item.get("popularity", 0)))),
        "score": float(item.get("score", 1.0)),
        "image_url": clean_val(item.get("image_url", "")),
    }

    if not item_dict["image_url"]:
        if item_dict["type"] == "movie":
            item_dict["image_url"] = await asyncio.to_thread(
                youtube_tool.get_movie_image_url, item_dict["title"]
            )
        elif item_dict["type"] == "music":
            item_dict["image_url"] = await asyncio.to_thread(
                youtube_tool.get_music_image_url, item_dict["title"], item_dict["year"]
            )

    if item_dict["type"] == "movie":
        trailer_url = clean_val(item.get("trailer_url", ""))
        if not trailer_url:
            trailer_url = await asyncio.to_thread(
                youtube_tool.find_trailer_url, item_dict["title"], item_dict["year"]
            )
        item_dict["trailer_url"] = clean_val(trailer_url)

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
@app.get("/autocomplete")
async def autocomplete(q: str = Query(..., min_length=1)):
    if not q:
        return {"movies": [], "music": []}

    suggestions_raw = engine.autocomplete_search(
        q, limit=20
    )  # Get enough to pick top 3 of each

    # Prepare tasks for fetching image URLs concurrently for ALL raw suggestions
    image_fetch_tasks = []
    for item in suggestions_raw:
        if item["type"] == "movie":
            image_fetch_tasks.append(
                asyncio.to_thread(youtube_tool.get_movie_image_url, item["title"])
            )
        elif item["type"] == "music":
            # 'year' column in media_df for music stores artist name
            image_fetch_tasks.append(
                asyncio.to_thread(
                    youtube_tool.get_music_image_url, item["title"], item["year"]
                )
            )
        else:
            image_fetch_tasks.append(
                asyncio.to_thread(lambda: None)
            )  # Placeholder for unknown types

    fetched_image_urls = await asyncio.gather(*image_fetch_tasks)

    # Assign fetched image URLs back to the suggestions_raw
    for i, item in enumerate(suggestions_raw):
        item["image_url"] = fetched_image_urls[i]

    final_movie_suggestions = []
    final_music_suggestions = []

    for item in suggestions_raw:
        if item["type"] == "movie" and len(final_movie_suggestions) < 3:
            final_movie_suggestions.append(item)
        elif item["type"] == "music" and len(final_music_suggestions) < 3:
            final_music_suggestions.append(item)

    return {"movies": final_movie_suggestions, "music": final_music_suggestions}


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
