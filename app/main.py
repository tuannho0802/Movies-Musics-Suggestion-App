import os
import random
import pandas as pd
import httpx
import math
import asyncio  # New import for speed
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .database import DataLoader
from .engine import RecommendationEngine
from .models import SearchResponse
from .youtube_tool import YoutubeToolset

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
    data = DataLoader.load_media(
        "data/movies_metadata.csv",
        "data/TMDB_movie_dataset_v11.csv",
        "data/music_data.csv",
    )
    if not data.empty:
        engine.media_df = data
        if engine.embeddings is None:
            print("🛠️ No embeddings found, building new ones...")
            engine._prepare_embeddings()

        mov_c = len(data[data["type"] == "movie"])
        mus_c = len(data[data["type"] == "music"])
        print(f"✅ SUCCESS: Loaded {mov_c} Movies & {mus_c} Songs.")
    else:
        print("❌ ERROR: Data injection failed.")
    print("=" * 50 + "\n")


# --- THE OPTIMIZATION WORKER ---
async def get_details_parallel(client, item):
    """Processes a single item. Used by asyncio.gather to run many at once."""
    item_dict = {
        "title": clean_val(item["title"]),
        "year": clean_val(item["year"]),
        "type": clean_val(item["type"]),
        "description": clean_val(item["description"]),
        "genre": clean_val(item["genre"]),
        "popularity": (
            int(round(float(item["popularity"])))
            if not pd.isna(item["popularity"])
            else 0
        ),
        "score": float(item.get("score", 1.0)),
        "image_url": clean_val(item.get("image_url", "")),
    }

    trailer_url = clean_val(item.get("trailer_url", ""))
    preview_url = clean_val(item.get("preview_url", ""))

    if item_dict["type"] == "movie":
        if not trailer_url:
            # RUN IN THREAD: prevents the YouTube search from freezing the app
            trailer_url = await asyncio.to_thread(
                youtube_tool.find_trailer_url, item_dict["title"], item_dict["year"]
            )
            if trailer_url:
                _update_media_df_with_url(
                    "movie",
                    item_dict["title"],
                    item_dict["year"],
                    "trailer_url",
                    trailer_url,
                )
        item_dict["trailer_url"] = clean_val(trailer_url)

    
    # SPEED FIX: Preview URLs are now fetched on-demand by the client
    # We no longer fetch them here to speed up initial load
    item_dict["preview_url"] = ""

    return item_dict

@app.get("/preview")
async def get_preview_url(title: str, artist: str):
    """New endpoint to fetch a music preview URL on-demand."""
    preview_url = await asyncio.to_thread(
        youtube_tool.get_music_preview_url, title, artist
    )
    if preview_url:
        # While we're here, let's update our main dataframe for the next time
        _update_media_df_with_url("music", title, artist, "preview_url", preview_url)
        return {"url": preview_url}
    return {"url": None}


from cachetools import TTLCache
# --- Caching Setup ---
# Cache for search endpoint, items expire after 5 minutes
search_cache = TTLCache(maxsize=200, ttl=300)

@app.get("/trending")
async def get_trending(type: str = "all", limit: int = 15):
    if engine.media_df is None:
        return {"results": []}

    # Your original pooling logic
    if type == "movie":
        pool = (
            engine.media_df[engine.media_df["type"] == "movie"]
            .sort_values("popularity", ascending=False)
            .head(250)
        )
    elif type == "music":
        pool = (
            engine.media_df[engine.media_df["type"] == "music"]
            .sort_values("popularity", ascending=False)
            .head(250)
        )
    else:
        movies = (
            engine.media_df[engine.media_df["type"] == "movie"]
            .sort_values("popularity", ascending=False)
            .head(250)
        )
        music = (
            engine.media_df[engine.media_df["type"] == "music"]
            .sort_values("popularity", ascending=False)
            .head(250)
        )
        pool = pd.concat([movies, music])

    sample = pool.sample(n=min(limit, len(pool)))

    # SPEED FIX: Start all fetches at the same time
    async with httpx.AsyncClient() as client:
        tasks = [get_details_parallel(client, item) for _, item in sample.iterrows()]
        results = await asyncio.gather(*tasks)

    # Shuffle results for all types to ensure randomness
    random.shuffle(results)
    
    return {"results": results}


@app.get("/search", response_model=SearchResponse)
async def search_api(q: str, type: str = "all"):
    cache_key = f"{q}-{type}"
    if cache_key in search_cache:
        print("✅ SEARCH: Returning cached results.")
        return search_cache[cache_key]
        
    raw = engine.search_advanced(query=q, media_type=type)

    # SPEED FIX: Start all searches at once
    async with httpx.AsyncClient() as client:
        tasks = [get_details_parallel(client, item) for item in raw]
        formatted = await asyncio.gather(*tasks)

    response = {"query": q, "count": len(formatted), "results": formatted}
    search_cache[cache_key] = response  # Store in cache
    print("✅ SEARCH: Cached new results.")
    return response

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
