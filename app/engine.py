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
        m_df = m_df[['title', 'overview']].rename(columns={'title': 'title', 'overview': 'description'})
        m_df['type'] = 'movie'

        # Load Music
        s_df = pd.read_csv(music_path).head(5000)
        s_df['description'] = "A " + s_df['track_genre'] + " song by " + s_df['artists']
        s_df = s_df[['track_name', 'description']].rename(columns={'track_name': 'title'})
        s_df['type'] = 'music'

        self.media_df = pd.concat([m_df, s_df], ignore_index=True).dropna()
        self._prepare_embeddings()

    def _prepare_embeddings(self):
        if os.path.exists(self.embeddings_path):
            print("Loading saved embeddings...")
            self.embeddings = torch.load(self.embeddings_path)
        else:
            print("Generating new embeddings...")
            descriptions = self.media_df['description'].tolist()
            self.embeddings = self.model.encode(descriptions, convert_to_tensor=True, show_progress_bar=True)
            torch.save(self.embeddings, self.embeddings_path)

    def search(self, query, media_type="all", top_k=10):
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        hits = util.semantic_search(query_embedding, self.embeddings, top_k=top_k)
        
        results = []
        for hit in hits[0]:
            item = self.media_df.iloc[hit['corpus_id']]
            if media_type == "all" or item['type'] == media_type:
                results.append({
                    "title": item['title'],
                    "type": item['type'],
                    "description": item['description'],
                    "score": round(float(hit['score']), 2)
                })
        return results[:5]