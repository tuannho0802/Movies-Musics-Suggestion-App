import pandas as pd
import torch
import os
from sentence_transformers import SentenceTransformer, util

class RecommendationEngine:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.media_df = None
        self.embeddings = None
        self.embeddings_path = "media_embeddings.pt"

    def load_data(self, movie_path, music_path):
        # Load Movies
        m_df = pd.read_csv(movie_path, low_memory=False).head(5000)
        m_df = m_df[['title', 'overview', 'vote_average']].rename(
            columns={'overview': 'description', 'vote_average': 'popularity'}
        )
        m_df['type'] = 'movie'
        m_df['genre'] = 'Movie'

        # Load Music
        s_df = pd.read_csv(music_path).head(5000)
        
     
        # 1. Sort by popularity so we keep the "best" version
        s_df = s_df.sort_values('popularity', ascending=False)
        # 2. Remove duplicates based on song name AND artist
        s_df = s_df.drop_duplicates(subset=['track_name', 'artists'])
      

        s_df['description'] = "A " + s_df['track_genre'] + " song by " + s_df['artists']
        s_df = s_df[['track_name', 'description', 'popularity', 'track_genre']].rename(
            columns={'track_name': 'title', 'track_genre': 'genre'}
        )
        s_df['type'] = 'music'

        self.media_df = pd.concat([m_df, s_df], ignore_index=True).dropna()
        self._prepare_embeddings()

    def _prepare_embeddings(self):
        # Everything here MUST be indented 8 spaces (2 tabs)
        if self.media_df is None:
            return

        expected_count = len(self.media_df)

        if os.path.exists(self.embeddings_path):
            print("Loading saved embeddings...")
            saved_embeddings = torch.load(self.embeddings_path)
            
            if saved_embeddings.shape[0] == expected_count:
                self.embeddings = saved_embeddings
                print("Embeddings loaded successfully.")
                return
            else:
                print(f"Size mismatch! Data has {expected_count} rows. Re-generating...")

        descriptions = self.media_df['description'].tolist()
        self.embeddings = self.model.encode(descriptions, convert_to_tensor=True, show_progress_bar=True)
        torch.save(self.embeddings, self.embeddings_path)
        print("New embeddings saved.")

    def search_advanced(self, query, media_type="all", min_popularity=0):
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        hits = util.semantic_search(query_embedding, self.embeddings, top_k=50)
        
        results = []
        for hit in hits[0]:
            item = self.media_df.iloc[hit['corpus_id']]
            
            if media_type != "all" and item['type'] != media_type:
                continue
            
            # Ensure popularity is treated as a number
            pop = float(item['popularity']) if not pd.isna(item['popularity']) else 0
            if pop < min_popularity:
                continue

            results.append({
                "title": item['title'],
                "type": item['type'],
                "description": item['description'],
                "genre": item['genre'],
                "popularity": int(pop) if not pd.isna(pop) else 0,
                "score": round(float(hit['score']), 2)
            })
            
        results = sorted(results, key=lambda x: (x['score'] * 0.7) + (x['popularity'] / 100 * 0.3), reverse=True)
        return results[:10]