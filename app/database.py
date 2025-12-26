import pandas as pd
import ast
import re

class DataLoader:
    @staticmethod
    def load_media(movie_path_og, movie_path_new, music_path):

        def normalize(text):
            if not text:
                return ""
            return re.sub(r"[^a-zA-Z0-9]", "", str(text)).lower()

        def extract_genres(genre_str):
            try:
                raw = str(genre_str).strip()
                if not raw or raw == "[]" or raw.lower() == "nan":
                    return "Media"
                if "[" in raw:
                    data = ast.literal_eval(raw)
                    if isinstance(data, list):
                        names = [
                            item.get("name") if isinstance(item, dict) else str(item)
                            for item in data
                        ]
                        return " | ".join(filter(None, names))
                return raw.replace(",", " | ")
            except:
                return "Media"

        def build_subset(path, col_map, type_label):
            try:
                df_raw = pd.read_csv(path, low_memory=False).head(8000)
            except:
                return pd.DataFrame()

            clean = pd.DataFrame()
            # Map columns safely
            for target, source in col_map.items():
                if source in df_raw.columns:
                    clean[target] = df_raw[source]
                else:
                    clean[target] = ""

            # Genre logic
            if "track_genre" in df_raw.columns:
                clean["genre"] = df_raw["track_genre"].apply(extract_genres)
            elif "genres" in df_raw.columns:
                clean["genre"] = df_raw["genres"].apply(extract_genres)
            else:
                clean["genre"] = "Media"

            if type_label == "music":
                artist = (
                    df_raw["artists"].astype(str)
                    if "artists" in df_raw.columns
                    else "Unknown"
                )

                descriptions = []
                for i in range(len(df_raw)):
                    r = df_raw.iloc[i]
                    v = []
                    if r.get("danceability", 0) > 0.6:
                        v.append("danceable")
                    if r.get("energy", 0) > 0.7:
                        v.append("energetic")
                    v_str = " & ".join(v) if v else "unique"
                    descriptions.append(
                        f"A {v_str} {clean.iloc[i]['genre']} track by {artist.iloc[i]}."
                    )

                clean["description"] = descriptions
                clean["year"] = artist
                # Create dedupe key strings
                titles_norm = clean["title"].apply(normalize)
                artists_norm = artist.apply(normalize)
                clean["dedupe_key"] = titles_norm + artists_norm
            else:
                clean["description"] = clean["description"].fillna("A feature film.")
                yr = df_raw["release_date"].astype(str).str.extract(r"(\d{4})")
                yr = yr[0].fillna("2000") if not yr.empty else "2000"
                clean["year"] = yr
                # Create dedupe key strings
                titles_norm = clean["title"].apply(normalize)
                clean["dedupe_key"] = titles_norm + yr.astype(str)

            clean["type"] = type_label
            clean["popularity"] = pd.to_numeric(
                clean["popularity"], errors="coerce"
            ).fillna(0)
            return clean.dropna(subset=["title"])

        m1 = build_subset(
            movie_path_og,
            {"title": "title", "description": "overview", "popularity": "vote_average"},
            "movie",
        )
        m2 = build_subset(
            movie_path_new,
            {"title": "title", "description": "overview", "popularity": "vote_average"},
            "movie",
        )
        s1 = build_subset(
            music_path, {"title": "track_name", "popularity": "popularity"}, "music"
        )

        combined = pd.concat([m1, m2, s1], ignore_index=True).sort_values(
            "popularity", ascending=False
        )
        # Final strict deduplication
        final = combined.drop_duplicates(subset=["dedupe_key"], keep="first").drop(
            columns=["dedupe_key"]
        )

        return final.reset_index(drop=True)
