import os
import torch
import numpy as np

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer, util

app = FastAPI()

# ---CORS BLOCK ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (fine for personal projects)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
# --------------------------------
model = SentenceTransformer('all-MiniLM-L6-v2')

EMBEDDINGS_FILE = "media_embeddings.pt" # We will save them here

# --- DATA LOADING & PREPARATION ---

# Load Movies (Safety check for column names)
movies_df = pd.read_csv("movies_metadata.csv", low_memory=False).head(5000)
# Note: Use 'title' or 'original_title' depending on your specific CSV
movies_df = movies_df[['title', 'overview']].rename(
    columns={'title': 'title', 'overview': 'description'}
)
movies_df['type'] = 'movie'

# Load Music (Matching your specific music_data.csv)
music_df = pd.read_csv("music_data.csv").head(5000)

# We create a 'description' by combining Genre, Artist, and Album 
# This gives the AI more context than just a song title!
# Better music description
music_df['description'] = (
    "A " + music_df['track_genre'] + 
    " song titled " + music_df['track_name'] + 
    " by " + music_df['artists']
)

music_df = music_df[['track_name', 'description']].rename(
    columns={'track_name': 'title'}
)
music_df['type'] = 'music'

# Combine
media_df = pd.concat([movies_df, music_df], ignore_index=True).dropna()

# Check if we already have saved embeddings
if os.path.exists(EMBEDDINGS_FILE):
    print("Loading saved embeddings from disk... (Instant)")
    media_embeddings = torch.load(EMBEDDINGS_FILE)
else:
    print("No saved embeddings found. Generating now...")
    media_embeddings = model.encode(
        media_df['description'].tolist(), 
        convert_to_tensor=True, 
        show_progress_bar=True
    )
    # Save them so we never have to do this again!
    torch.save(media_embeddings, EMBEDDINGS_FILE)
    print(f"Saved embeddings to {EMBEDDINGS_FILE}")

print(f"Generating embeddings for {len(media_df)} items...")
media_embeddings = model.encode(media_df['description'].tolist(), convert_to_tensor=True, show_progress_bar=True)

@app.get("/search")
def search(q: str, media_type: str = "all"):
    query_embedding = model.encode(q, convert_to_tensor=True)
    
    # We ask for more hits (top_k=20) because if the user filters for 'music', 
    # we want to make sure we found enough music in the top results.
    hits = util.semantic_search(query_embedding, media_embeddings, top_k=20)
    
    results = []
    for hit in hits[0]:
        idx = hit['corpus_id']
        item = media_df.iloc[idx]
        
        if media_type == "all" or item['type'] == media_type:
            results.append({
                "title": item['title'],
                "type": item['type'],
                "description": item['description'][:100] + "...",
                "score": round(float(hit['score']), 2)
            })
    
    return {"results": results[:5]}