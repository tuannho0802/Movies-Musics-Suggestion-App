import pandas as pd

# Load your updated music file
df = pd.read_csv("data_cache/music_data.csv")
# Search for the song or artist
target_song = "Talking to the Moon"
target_artist = "Bruno Mars"

# Filter the dataframe
match = df[
    (df["track_name"].str.contains(target_song, case=False, na=False))
    | (df["artist_name"].str.contains(target_artist, case=False, na=False))
]

if not match.empty:
    print("✅ FOUND IT!")
    print(match[["track_name", "artist_name", "popularity"]])
else:
    print("❌ NOT FOUND. Check your fetch logic in update_data.py")


# Run this cmd to check data
# python check_data.py
