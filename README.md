# 🎬🎵 Media Discovery Engine 🎵🎬

A unique application that allows users to find movies and music based on **concepts, moods, and vibes**, moving beyond traditional keyword searching. Powered by Python, FastAPI, and advanced NLP techniques.

## ✨ Features

*   **Semantic Search:** Find media using natural language queries based on meaning, not just exact keywords.
*   **Movie & Music Discovery:** Search for both movies and music within a unified interface.
*   **Trending Views:** Explore curated lists of trending movies and music.
*   **"See More" Functionality:** Load more content with a click in trending views.
*   **Infinite Scroll & Lazy Loading:** Seamlessly load more content as you scroll, ensuring a smooth user experience.
*   **Hide/Show Search on Scroll:** The search bar and filters intelligently hide on scroll down and reappear on scroll up.
*   **UI Enhancements:** Optimized description lengths, right-aligned "See More" buttons with emojis, and consistent grid layouts for both movie and music lists.

## 🚀 Technologies Used

*   **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
*   **AI/NLP:** Sentence-Transformers (`all-MiniLM-L6-v2` model) for semantic embeddings.
*   **Data Handling:** Pandas & PyTorch
*   **Frontend:** Vanilla HTML5, CSS, and JavaScript (using Fetch API)
*   **APIs:** TMDB API (for movie posters and metadata), iTunes API (for music artwork)

## 📚 Datasets

This application utilizes the following datasets:
*   **Spotify Tracks Dataset:** [Kaggle Link](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)
*   **IMDb & TMDB Movie Metadata:** [Kaggle Link](https://www.kaggle.com/datasets/shubhamchandra235/imdb-and-tmdb-movie-metadata-big-dataset-1m?resource=download)
*   **TMDB Movies Dataset (2023):** [Kaggle Link](https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies)

## 🛠️ Installation & Setup

### 1. Clone the repository

```bash
  git clone https://github.com/tuannho0802/Movies-Musics-Suggestion-App.git
  cd Movies-Musics-Suggestion-App
```

### 2. Set up Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
.\venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install fastapi uvicorn sentence-transformers pandas torch python-dotenv
```

### 5. Environment Variables

Create a `.env` file in the root directory based on `.env.example` and add your **TMDB API Key**:

```
TMDB_API_KEY=YOUR_TMDB_API_KEY_HERE
```
*(Replace `YOUR_TMDB_API_KEY_HERE` with your actual key obtained from [The Movie Database API](https://www.themoviedb.org/documentation/api/key))*

## 🚀 Running the Application

### 1. Start the Backend API Server:

```bash
uvicorn app.main:app --reload
```
*(This assumes your FastAPI app instance is named `app` in `app/main.py`)*

### 2. Open the App:

Run the server using `uvicorn app.main:app --reload`, then access the application in your browser at:
`http://127.0.0.1:8000/`

### 3. API Documentation:

Once the server is running, you can access the interactive API documentation at:
`http://127.0.0.1:8000/docs`

## 🤔 How it Works

This application leverages Natural Language Processing (NLP) to go beyond simple keyword matching. It converts text descriptions into vector embeddings and calculates similarity scores between your query and the media library. This allows for more intuitive searching based on concepts, moods, and vibes.

## 🌟 Future Improvements

*   **Vector Database:** Integrate ChromaDB for faster searching with large datasets.
*   **Hybrid Search:** Combine semantic search with metadata filters (Year, Genre, Artist).
*   **Deployment:** Host the API on platforms like Render/Heroku and the frontend on GitHub Pages.

## 🐞 Bug Report / Feedback

If you encounter any issues or have suggestions, please use the `/bug` command or report them.