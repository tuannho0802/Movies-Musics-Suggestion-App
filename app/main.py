from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles  
from fastapi.responses import FileResponse 
from fastapi.middleware.cors import CORSMiddleware
from .engine import RecommendationEngine

app = FastAPI()

# 1. Standard CORS and Engine setup
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
engine = RecommendationEngine()
engine.load_data("data/movies_metadata.csv", "data/music_data.csv")

# 2. Mount the static folder so images/css/js are accessible
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3. Serve the index.html at the main URL
@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.get("/search")
def search_api(q: str, media_type: str = "all"):
    results = engine.search(q, media_type=media_type)
    return {"results": results}