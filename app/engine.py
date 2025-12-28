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
        if os.path.exists(self.embeddings_path):
            print(f"✅ Pre-loaded embeddings found at: {self.embeddings_path}")
            self.embeddings = torch.load(self.embeddings_path)
        else:
            print(f"❌ No pre-loaded embeddings found at: {self.embeddings_path}")

    def _prepare_embeddings(self):
        if self.media_df is None:
            return
        descriptions = self.media_df["description"].tolist()
        self.embeddings = self.model.encode(descriptions, convert_to_tensor=True, show_progress_bar=True)
        torch.save(self.embeddings, self.embeddings_path)

    def search_advanced(self, query, media_type="all", page=1, page_size=12):
        query_embedding = self.model.encode(query, convert_to_tensor=True)

        if media_type != "all":
            subset_df = self.media_df[self.media_df["type"] == media_type]
            indices = subset_df.index.tolist()
            if not indices:
                return pd.DataFrame()
            subset_embeddings = self.embeddings[indices]
            hits = util.semantic_search(query_embedding, subset_embeddings, top_k=min(100, len(indices)))
            
            # Map hit indices back to original dataframe indices
            original_indices = [indices[hit['corpus_id']] for hit in hits[0]]
            scores = [hit['score'] for hit in hits[0]]
            
            # Create a DataFrame of the results with their scores
            results_df = self.media_df.loc[original_indices].copy()
            results_df["score"] = scores

        else:
            hits = util.semantic_search(query_embedding, self.embeddings, top_k=100)
            indices = [hit['corpus_id'] for hit in hits[0]]
            scores = [hit['score'] for hit in hits[0]]
            results_df = self.media_df.loc[indices].copy()
            results_df["score"] = scores
        
        # Sort by score and then paginate
        sorted_df = results_df.sort_values(by="score", ascending=False)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        return sorted_df.iloc[start_index:end_index]
