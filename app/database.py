import pandas as pd

class DataLoader:
    @staticmethod
    def load_media(movie_path, music_path):
        # 1. Load Movies with Metadata
        m_df = pd.read_csv(movie_path, low_memory=False).head(5000)
        m_df = m_df[['title', 'overview', 'vote_average']].rename(
            columns={'overview': 'description', 'vote_average': 'popularity'}
        )
        m_df['type'] = 'movie'
        m_df['genre'] = 'Film' # You can extract real genres here later

        # 2. Load Music with actual CSV columns
        s_df = pd.read_csv(music_path).head(5000)
        s_df = s_df.drop_duplicates(subset=['track_name', 'artists'])
        s_df['description'] = "A " + s_df['track_genre'] + " song by " + s_df['artists']
        s_df = s_df[['track_name', 'description', 'track_genre', 'popularity']].rename(
            columns={'track_name': 'title', 'track_genre': 'genre'}
        )
        s_df['type'] = 'music'

        return pd.concat([m_df, s_df], ignore_index=True).dropna(subset=['description'])