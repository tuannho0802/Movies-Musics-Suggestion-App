import pandas as pd
import torch
import os
from sentence_transformers import SentenceTransformer, util

class RecommendationEngine:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.media_df = None
        self.embeddings = None
        self.embeddings_path = "media_embeddings.pt"

    def _prepare_embeddings(self):
        if self.media_df is None:
            return
        descriptions = self.media_df["description"].tolist()
        self.embeddings = self.model.encode(descriptions, convert_to_tensor=True, show_progress_bar=True)
        torch.save(self.embeddings, self.embeddings_path)

    def search_advanced(self, query, media_type="all"):
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        hits = util.semantic_search(query_embedding, self.embeddings, top_k=40)

        results = []
        for hit in hits[0]:
            item = self.media_df.iloc[hit["corpus_id"]]
            if media_type != "all" and item["type"] != media_type:
                continue

            results.append(
                {
                    "title": item["title"],
                    "type": item["type"],
                    "description": item["description"],
                    "genre": item["genre"],
                    "year": str(
                        item.get("year", "")
                    ),  # Contains Year for movies, Artist for music
                    "popularity": float(item["popularity"]),
                    "score": round(float(hit["score"]), 2),
                }
            )

        return sorted(results, key=lambda x: x["score"], reverse=True)[:12]
