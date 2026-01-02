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
        if self.media_df is None or self.embeddings is None:
            return pd.DataFrame()

        # --- 1. Fix the Indexing Bug ---
        # We reset the index to ensure row numbers match the embeddings tensor exactly
        df_to_search = self.media_df.reset_index(drop=True)

        # --- 2. Specific Search Logic (Direct Match) ---
        # Normalize for a fair comparison
        clean_query = query.strip().lower()

        # Check for an exact title match (Case-insensitive)
        exact_match = df_to_search[df_to_search["title"].str.lower() == clean_query]

        if media_type != "all":
            exact_match = exact_match[exact_match["type"] == media_type]

        # If a perfect match is found on the first page, return it with a 1.0 score
        if not exact_match.empty and page == 1:
            results_df = exact_match.copy()
            results_df["score"] = 1.0
            return results_df.sort_values(by="popularity", ascending=False).head(1)

        # --- 3. Normal Semantic Search (Old Functionality) ---
        query_embedding = self.model.encode(query, convert_to_tensor=True)

        if media_type != "all":
            mask = df_to_search["type"] == media_type
            indices = df_to_search.index[mask].tolist()
            if not indices:
                return pd.DataFrame()

            subset_embeddings = self.embeddings[indices]
            hits = util.semantic_search(query_embedding, subset_embeddings, top_k=min(100, len(indices)))

            # Map hit indices back to the continuous range of df_to_search
            final_indices = [indices[hit["corpus_id"]] for hit in hits[0]]
            scores = [hit['score'] for hit in hits[0]]

            results_df = df_to_search.iloc[final_indices].copy()
            results_df["score"] = scores
        else:
            hits = util.semantic_search(query_embedding, self.embeddings, top_k=100)
            final_indices = [hit["corpus_id"] for hit in hits[0]]
            scores = [hit['score'] for hit in hits[0]]

            results_df = df_to_search.iloc[final_indices].copy()
            results_df["score"] = scores

        # Sort and paginate as before
        sorted_df = results_df.sort_values(by="score", ascending=False)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size

        return sorted_df.iloc[start_index:end_index]
