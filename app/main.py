import os
import random
import pandas as pd
import httpx
import math  # Added to check for NaN
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


# HELPER: Ensure values are JSON compliant (No NaNs)
def clean_val(val, default=""):
    if val is None:
        return default
    # Check if it's a float NaN
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


@app.get("/trending")
async def get_trending(type: str = "all", limit: int = 15):
    if engine.media_df is None:
        return {"results": []}

    if type == "movie":
        pool = engine.media_df[engine.media_df["type"] == "movie"].sort_values("popularity", ascending=False).head(250)
    elif type == "music":
        pool = engine.media_df[engine.media_df["type"] == "music"].sort_values("popularity", ascending=False).head(250)
    else:
        movies = engine.media_df[engine.media_df["type"] == "movie"].sort_values("popularity", ascending=False).head(250)
        music = engine.media_df[engine.media_df["type"] == "music"].sort_values("popularity", ascending=False).head(250)
        pool = pd.concat([movies, music])

    sample = pool.sample(n=min(limit, len(pool)))

    results = []
    async with httpx.AsyncClient() as client:
        for _, item in sample.iterrows():
            # Apply clean_val to everything to prevent NaN errors
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
                "score": 1.0,
                "image_url": clean_val(item.get("image_url", "")),
            }

            trailer_url = clean_val(item.get("trailer_url", ""))
            preview_url = clean_val(item.get("preview_url", ""))

            if item_dict["type"] == "movie":
                if not trailer_url:
                    trailer_url = youtube_tool.find_trailer_url(
                        item_dict["title"], item_dict["year"]
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

            elif item_dict["type"] == "music":
                if not preview_url:
                    try:
                        itunes_res = await client.get(
                            f"https://itunes.apple.com/search?term={item_dict['title']}&entity=song&limit=1",
                            timeout=5.0,
                        )
                        if itunes_res.status_code == 200:
                            itunes_data = itunes_res.json()
                            if itunes_data["results"] and itunes_data["results"][0].get(
                                "previewUrl"
                            ):
                                preview_url = itunes_data["results"][0]["previewUrl"]
                                _update_media_df_with_url(
                                    "music",
                                    item_dict["title"],
                                    item_dict["year"],
                                    "preview_url",
                                    preview_url,
                                )
                    except Exception:
                        preview_url = ""
                item_dict["preview_url"] = clean_val(preview_url)

            results.append(item_dict)

    if type == 'all':
        random.shuffle(results)

    return {"results": results}


@app.get("/search", response_model=SearchResponse)
async def search_api(q: str, type: str = "all"):
    raw = engine.search_advanced(query=q, media_type=type)
    formatted = []
    async with httpx.AsyncClient() as client:
        for item in raw:
            item_dict = {
                "title": clean_val(item["title"]),
                "year": clean_val(item.get("year", "")),
                "type": clean_val(item["type"]),
                "description": clean_val(item["description"]),
                "genre": clean_val(item["genre"]),
                "score": float(item["score"]),
                "popularity": int(round(float(item.get("popularity", 0)))),
                "image_url": clean_val(item.get("image_url", "")),
            }

            trailer_url = clean_val(item.get("trailer_url", ""))
            preview_url = clean_val(item.get("preview_url", ""))

            if item_dict["type"] == "movie":
                if not trailer_url:
                    trailer_url = youtube_tool.find_trailer_url(
                        item_dict["title"], item_dict["year"]
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
            elif item_dict["type"] == "music":
                if not preview_url:
                    try:
                        itunes_res = await client.get(
                            f"https://itunes.apple.com/search?term={item_dict['title']}&entity=song&limit=1",
                            timeout=5.0,
                        )
                        if itunes_res.status_code == 200:
                            itunes_data = itunes_res.json()
                            if itunes_data["results"] and itunes_data["results"][0].get(
                                "previewUrl"
                            ):
                                preview_url = itunes_data["results"][0]["previewUrl"]
                                _update_media_df_with_url(
                                    "music",
                                    item_dict["title"],
                                    item_dict["year"],
                                    "preview_url",
                                    preview_url,
                                )
                    except Exception:
                        preview_url = ""
                item_dict["preview_url"] = clean_val(preview_url)
            formatted.append(item_dict)
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
