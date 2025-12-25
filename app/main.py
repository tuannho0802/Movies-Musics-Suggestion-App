import os
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from .database import DataLoader
from .engine import RecommendationEngine
from .models import SearchResponse

from dotenv import load_dotenv
load_dotenv() # Load the .env file

app = FastAPI(title="Advanced Media Discovery API")

# 1. Security & Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Initialize Engine & Load Data
# This happens once when the server starts
engine = RecommendationEngine()
media_data = DataLoader.load_media("data/movies_metadata.csv", "data/music_data.csv")
engine.media_df = media_data
engine._prepare_embeddings() # Ensure embeddings are ready

# Config Env
@app.get("/config")
def get_config():
    return {
       "TMDB_API_KEY": os.getenv("TMDB_API_KEY")
    }


# 3. Static Files (UI)
app.mount("/static", StaticFiles(directory="static"), name="static")



@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

# 4. Advanced Search Endpoint
@app.get("/search", response_model=SearchResponse)
def search_api(
    q: str, 
    media_type: str = "all", 
    min_popularity: int = Query(0, ge=0, le=100)
):
    """
    Advanced Search: Combines Semantic Vibe with Popularity filters.
    """
    results = engine.search_advanced(q, media_type=media_type, min_popularity=min_popularity)
    
    return {
        "query": q,
        "count": len(results),
        "results": results
    }