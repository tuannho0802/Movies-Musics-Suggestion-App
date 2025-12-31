import pandas as pd
import torch
import os
from sentence_transformers import SentenceTransformer, util
from app.database import DataLoader # Import DataLoader

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

    def init_data(self, movie_path_og, movie_path_new, music_path):
        self.media_df = DataLoader.load_media(movie_path_og, movie_path_new, music_path)
        if self.embeddings is None:
            self._prepare_embeddings()

    def _prepare_embeddings(self):
        if self.media_df is None:
            return
        descriptions = self.media_df["description"].tolist()
        self.embeddings = self.model.encode(descriptions, convert_to_tensor=True, show_progress_bar=True)
        torch.save(self.embeddings, self.embeddings_path)

    def autocomplete_search(self, query: str, limit: int = 5):
        if self.media_df is None:
            return []

        # Simple fuzzy matching: check if query is contained in title (case-insensitive)
        mask = self.media_df['title'].str.contains(query, case=False, na=False)
        suggestions = self.media_df[mask].head(limit)

        results = []
        for index, row in suggestions.iterrows():
            item_id = row['id'] if 'id' in row else index # Use existing 'id' or DataFrame index
            results.append({
                "id": item_id,
                "title": row['title'],
                "type": row['type'],
                "year": row['year'], # Use 'year' for both, which is artist for music
                "image_url": row['image_url'] if 'image_url' in row else None # Will be fetched dynamically
            })
        return results

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