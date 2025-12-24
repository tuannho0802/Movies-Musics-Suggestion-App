# 🔍 Media Discovery Engine

A creative "Semantic Search" application that allows users to find movies and music based on **concepts, moods, and vibes** rather than just keywords. Built with Python, FastAPI, and Sentence-Transformers.

## 🚀 How it Works

Unlike traditional search engines that look for exact word matches, this app uses **Natural Language Processing (NLP)**. It converts text descriptions into high-dimensional vectors (embeddings) and calculates the mathematical similarity between your query and the media library.

> **Example:** Searching for "Space adventure" will find _Interstellar_ even if the word "adventure" isn't in the description.

## 🛠️ Tech Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **AI Model:** `all-MiniLM-L6-v2` (via Sentence-Transformers)
- **Data Handling:** Pandas & PyTorch
- **Frontend:** Vanilla HTML5 / JavaScript (Fetch API)

## 📦 Installation & Setup

### 1. Clone the repository

```bash
  git clone https://github.com/tuannho0802/Movies-Musics-Suggestion-App.git
```

Go to the project directory

```bash
  cd Movies-Musics-Suggestion-App
```

### 2. Set up Virtual Environment

```bash
python -m venv venv
```

Windows:

```
.\venv\Scripts\activate
```

Mac/Linux:

```
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install fastapi uvicorn sentence-transformers pandas torch
```

### 4. Prepare Data _(You can search these on Kaggle)_

Ensure you have the following files in the **root directory**:

- _movies_metadata.csv_ (From TMDB/Kaggle)

- _music_data.csv_ (Spotify Tracks Dataset)

## 🖥️ Usage

### 1. Start the API server:

```bash
uvicorn main:app --reload
```

### 2. Open the App: Simply open index.html in your preferred web browser.

### 3. API Documentation: Once the server is running, visit *http://127.0.0.1:8000/docs* to test the API endpoints interactively.

### 🌟 Future Improvements

[ ] **Vector Database:** Integrate ChromaDB for faster searching of millions of rows.

[ ] **Visuals:** Fetch real movie posters and album art via external APIs.

[ ] **Hybrid Search:** Combine semantic search with metadata filters (Year, Genre, Artist).

[ ] **Deployment:** Host the API on Render/Heroku and the frontend on GitHub Pages.
