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
    print("\n" + "=" * 50 + "\n🚀 INITIALIZING CLEAN ENGINE\n" + "=" * 50)
    data = DataLoader.load_media(
        "data/movies_metadata.csv",
        "data/TMDB_movie_dataset_v11.csv",
        "data/music_data.csv",
    )
    if not data.empty:
        engine.media_df = data
        engine._prepare_embeddings()

        mov_c = len(data[data["type"] == "movie"])
        mus_c = len(data[data["type"] == "music"])
        print(f"✅ SUCCESS: Loaded {mov_c} Movies & {mus_c} Songs.")
    else:
        print("❌ ERROR: Data injection failed.")
    print("=" * 50 + "\n")


@app.get("/trending")
def get_trending():
    if engine.media_df is None:
        return {"results": []}

    # Pool top 500 items
    pool = engine.media_df.sort_values("popularity", ascending=False).head(500)

    # Randomly pick 15 different items from the pool
    sample = pool.sample(n=min(15, len(pool)))

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
            }
        )

    # Shuffle the list so movies and music are mixed up
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
