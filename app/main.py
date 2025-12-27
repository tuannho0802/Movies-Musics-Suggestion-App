import os
import random
import pandas as pd
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .database import DataLoader
from .engine import RecommendationEngine
from .models import SearchResponse

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
engine = RecommendationEngine()


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
def get_trending(type: str = "all", limit: int = 15):
    if engine.media_df is None:
        return {"results": []}

    # Define the pool of items to sample from based on the 'type' parameter
    if type == "movie":
        pool = engine.media_df[engine.media_df["type"] == "movie"].sort_values("popularity", ascending=False).head(250)
    elif type == "music":
        pool = engine.media_df[engine.media_df["type"] == "music"].sort_values("popularity", ascending=False).head(250)
    else: # type == 'all'
        movies = engine.media_df[engine.media_df["type"] == "movie"].sort_values("popularity", ascending=False).head(250)
        music = engine.media_df[engine.media_df["type"] == "music"].sort_values("popularity", ascending=False).head(250)
        pool = pd.concat([movies, music])

    # Randomly pick 'limit' different items from the pool
    sample = pool.sample(n=min(limit, len(pool)))

    results = []
    for _, item in sample.iterrows():
        results.append(
            {
                "title": str(item["title"]),
                "year": str(item["year"]),
                "type": str(item["type"]),
                "description": str(item["description"]),
                "genre": str(item["genre"]),
                "popularity": int(round(float(item["popularity"]))),
                "score": 1.0,
                "image_url": str(item.get("image_url", "")),
            }
        )
    
    # Shuffle only if we are getting all types
    if type == 'all':
        random.shuffle(results)

    return {"results": results}


@app.get("/search", response_model=SearchResponse)
def search_api(q: str, type: str = "all"):
    raw = engine.search_advanced(query=q, media_type=type)
    formatted = []
    for item in raw:
        formatted.append(
            {
                "title": str(item["title"]),
                "year": str(item.get("year", "")),
                "type": str(item["type"]),
                "description": str(item["description"]),
                "genre": str(item["genre"]),
                "score": float(item["score"]),
                "popularity": int(round(float(item.get("popularity", 0)))),
                "image_url": str(item.get("image_url", "")),
            }
        )
    return {"query": q, "count": len(formatted), "results": formatted}


@app.get("/config")
def get_config():
    return {"TMDB_API_KEY": os.getenv("TMDB_API_KEY", "")}


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")
