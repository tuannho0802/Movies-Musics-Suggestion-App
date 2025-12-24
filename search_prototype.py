import pandas as pd
from sentence_transformers import SentenceTransformer, util

# 1. Load the data
df = pd.read_csv("media_data.csv")

# 2. Load a pre-trained "Model" (Think of this as the AI's brain)
# 'all-MiniLM-L6-v2' is small, fast, and perfect for beginners.
model = SentenceTransformer('all-MiniLM-L6-v2')

# 3. Create "Embeddings" for all your media descriptions
# This turns your text descriptions into lists of numbers (vectors).
print("Generating embeddings... please wait.")
media_embeddings = model.encode(df['description'].tolist(), convert_to_tensor=True)

def search_media(query, top_k=2):
    # Turn the user's question into numbers too
    query_embedding = model.encode(query, convert_to_tensor=True)
    
    # Calculate "Cosine Similarity" (How close the numbers are)
    hits = util.semantic_search(query_embedding, media_embeddings, top_k=top_k)
    
    print(f"\nResults for: '{query}'")
    for hit in hits[0]:
        idx = hit['corpus_id']
        score = hit['score']
        print(f"- {df.iloc[idx]['title']} ({df.iloc[idx]['type']}) | Match Score: {score:.2f}")

# --- Test it out! ---
search_media("I want something exciting with superheroes")
search_media("Something relaxing to listen to")