"""
Movie Rating Prediction System (TMDB API Version)
Backend: Python HTTP Server + TMDB API

Run:  python movie_rating_predictor.py
API Endpoints:
  GET  /health
  GET  /api/movies
  POST /api/predict   { "emotion": "happy", "preferred_genres": ["Action"], "review_text": "" }
"""

import json
import math
import random
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import re
import os


# TMDB CONFIG

TMDB_API_KEY = "9eaba43292d7ca6807b0897a106cd623"
TMDB_BASE_URL = "https://api.themoviedb.org/3"



# FETCH GENRE MAP FROM TMDB

def fetch_genres():
    url = f"{TMDB_BASE_URL}/genre/movie/list"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    try:
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return {g["id"]: g["name"] for g in res.json().get("genres", [])}
    except Exception as e:
        print(f"[WARN] Could not fetch genres: {e}")
        return {}


GENRE_MAP = fetch_genres()
print(f"[INFO] Loaded {len(GENRE_MAP)} genres from TMDB")



# FETCH POPULAR MOVIES FROM TMDB

def fetch_movies(page=1):
    url = f"{TMDB_BASE_URL}/movie/popular"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "page": page
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"[TMDB] Page {page} — Status: {response.status_code}")

        if response.status_code != 200:
            print(f"[ERROR] TMDB response: {response.text}")
            return []

        data = response.json()

        if "results" not in data:
            print(f"[ERROR] Unexpected TMDB response: {data}")
            return []

        movies = []
        for m in data["results"]:
            genre_ids = m.get("genre_ids", [])
            genre_name = GENRE_MAP.get(genre_ids[0], "Drama") if genre_ids else "Drama"

            movies.append({
                "id": m["id"],
                "title": m["title"],
                "genre": genre_name,
                "all_genres": [GENRE_MAP.get(gid, "Unknown") for gid in genre_ids],
                "avg_rating": round(m.get("vote_average", 5.0) / 2, 2),   # TMDB is /10, convert to /5
                "vote_count": m.get("vote_count", 0),
                "popularity": round(m.get("popularity", 0), 2),
                "overview": m.get("overview", ""),
                "year": m.get("release_date", "")[:4] if m.get("release_date") else "N/A",
                "poster": f"https://image.tmdb.org/t/p/w185{m['poster_path']}" if m.get("poster_path") else None
            })

        return movies

    except Exception as e:
        print(f"[EXCEPTION] fetch_movies page={page}: {e}")
        return []


def get_all_movies(pages=5):
    """Fetch movies across multiple pages (~20 results/page)."""
    movies = []
    for i in range(1, pages + 1):
        batch = fetch_movies(i)
        movies.extend(batch)
        print(f"[INFO] Fetched {len(batch)} movies from page {i}. Total so far: {len(movies)}")
    return movies



# STARTUP: CACHE MOVIES

MOVIES_CACHE = []
try:
    MOVIES_CACHE = get_all_movies(pages=5)
    print(f"[INFO] Total movies cached: {len(MOVIES_CACHE)}")
except Exception as e:
    print(f"[CRITICAL] Failed to load movies from TMDB: {e}")



# EMOTION → GENRE WEIGHT MAPPING

EMOTION_GENRE_WEIGHTS = {
    "happy":   {"Comedy": 1.5, "Romance": 1.3, "Animation": 1.3, "Action": 1.2, "Sci-Fi": 1.1, "Drama": 0.9},
    "sad":     {"Drama": 1.5, "Romance": 1.4, "Music": 1.3, "Comedy": 1.2, "Animation": 1.1},
    "excited": {"Action": 1.6, "Thriller": 1.5, "Science Fiction": 1.4, "Adventure": 1.3, "Crime": 1.2},
    "bored":   {"Action": 1.5, "Thriller": 1.4, "Mystery": 1.3, "Science Fiction": 1.2, "Horror": 1.1},
    "anxious": {"Comedy": 1.4, "Animation": 1.3, "Family": 1.3, "Romance": 1.2, "Fantasy": 1.1},
    "romantic":{"Romance": 1.6, "Drama": 1.4, "Comedy": 1.3, "Music": 1.2},
    "neutral": {"Drama": 1.1, "Comedy": 1.0, "Action": 1.0, "Documentary": 1.0},
}

POSITIVE_WORDS = {
    "good", "great", "amazing", "love", "happy", "excellent", "fantastic",
    "wonderful", "brilliant", "superb", "awesome", "best", "enjoyed", "fun",
    "exciting", "thrilling", "beautiful", "perfect", "outstanding"
}
NEGATIVE_WORDS = {
    "bad", "terrible", "hate", "sad", "boring", "awful", "horrible", "worst",
    "disappointing", "dull", "mediocre", "poor", "waste", "slow", "painful", "annoying"
}



# SENTIMENT ANALYSIS

def analyze_sentiment(text: str) -> dict:
    words = re.findall(r'\b\w+\b', text.lower())

    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos + neg

    score = round((pos - neg) / max(total, 1), 2)

    if score > 0.3:
        emotion = "happy"
    elif score > 0:
        emotion = "excited"
    elif score < -0.3:
        emotion = "sad"
    elif score < 0:
        emotion = "bored"
    else:
        emotion = "neutral"

    return {
        "sentiment_score": score,
        "emotion": emotion,
        "positive_words_found": pos,
        "negative_words_found": neg
    }


# ─────────────────────────────────────────────
# RATING PREDICTION
# ─────────────────────────────────────────────
def predict_ratings(emotion: str, preferred_genres: list) -> list:
    if not MOVIES_CACHE:
        return []

    weights = EMOTION_GENRE_WEIGHTS.get(emotion, EMOTION_GENRE_WEIGHTS["neutral"])
    results = []

    for m in MOVIES_CACHE:
        base = m["avg_rating"]
        genre = m["genre"]

        # Emotion-based genre weight
        emotion_weight = weights.get(genre, 1.0)

        # User preference boost
        pref_boost = 0.3 if genre in preferred_genres else 0.0

        # Popularity signal (minor boost for widely-seen films)
        pop_boost = min(0.1, m["popularity"] / 5000)

        # Small random noise to simulate per-user variation
        noise = random.uniform(-0.1, 0.1)

        predicted = base * emotion_weight + pref_boost + pop_boost + noise
        predicted = round(min(5.0, max(1.0, predicted)), 2)

        results.append({
            **m,
            "predicted_rating": predicted
        })

    results.sort(key=lambda x: x["predicted_rating"], reverse=True)
    return results



# EVALUATION METRICS

def compute_metrics(predictions: list) -> dict:
    if not predictions:
        return {"mae": 0, "rmse": 0, "accuracy": 0}

    errors = []
    for m in predictions:
        # Simulate actual rating with small variance around TMDB avg
        actual = m["avg_rating"] + random.uniform(-0.3, 0.3)
        actual = min(5.0, max(1.0, actual))
        errors.append(abs(m["predicted_rating"] - actual))

    mae = sum(errors) / len(errors)
    rmse = math.sqrt(sum(e ** 2 for e in errors) / len(errors))
    accuracy = (1 - mae / 5) * 100

    return {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "accuracy": round(accuracy, 2)
    }



# HTTP SERVER

def add_cors_headers(handler):
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")


class MovieHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Override to add cleaner logging
        print(f"[{self.command}] {self.path} — {args[1]}")

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        add_cors_headers(self)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        add_cors_headers(self)
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            self.send_json({
                "status": "ok",
                "movies_loaded": len(MOVIES_CACHE),
                "genres_loaded": len(GENRE_MAP)
            })

        elif path == "/api/movies":
            self.send_json(MOVIES_CACHE)

        elif path == "/api/genres":
            self.send_json(list(GENRE_MAP.values()))

        else:
            self.send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON body"}, 400)
            return

        if path == "/api/predict":
            emotion = data.get("emotion", "neutral").lower()
            preferred_genres = data.get("preferred_genres", [])
            review_text = data.get("review_text", "").strip()
            top_n = int(data.get("top_n", 40))

            # Override emotion via sentiment if review text provided
            sentiment_result = None
            if review_text:
                sentiment_result = analyze_sentiment(review_text)
                emotion = sentiment_result["emotion"]
                print(f"[INFO] Sentiment detected: {emotion} (score={sentiment_result['sentiment_score']})")

            if emotion not in EMOTION_GENRE_WEIGHTS:
                emotion = "neutral"

            predictions = predict_ratings(emotion, preferred_genres)
            metrics = compute_metrics(predictions)

            self.send_json({
                "emotion_used": emotion,
                "sentiment": sentiment_result,
                "preferred_genres": preferred_genres,
                "top_movies": predictions[:top_n],
                "total_movies_evaluated": len(predictions),
                "metrics": metrics
            })

        else:
            self.send_json({"error": "Endpoint not found"}, 404)



# ENTRY POINT

def run():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), MovieHandler)
    print(f"\n{'='*50}")
    print(f"  Movie Rating Predictor — TMDB Edition")
    print(f"  Server: http://localhost:{port}")
    print(f"  Movies: {len(MOVIES_CACHE)} loaded")
    print(f"{'='*50}\n")
    print("Endpoints:")
    print(f"  GET  http://localhost:{port}/health")
    print(f"  GET  http://localhost:{port}/api/movies")
    print(f"  GET  http://localhost:{port}/api/genres")
    print(f"  POST http://localhost:{port}/api/predict")
    print("\nExample POST body:")
    print('  {"emotion": "excited", "preferred_genres": ["Action", "Thriller"], "review_text": ""}')
    print("\nPress Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped.")
        server.server_close()


if __name__ == "__main__":
    run()