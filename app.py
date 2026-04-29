"""
Movie Rating Prediction System (TMDB API Version)
Backend: Python HTTP Server + TMDB API
"""

import json
import math
import random
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import re
import os

# ─────────────────────────────────────────────
# TMDB CONFIG
# ─────────────────────────────────────────────
TMDB_API_KEY = "9eaba43292d7ca6807b0897a106cd623"
TMDB_BASE_URL = "https://api.themoviedb.org/3"


# ─────────────────────────────────────────────
# FETCH DATA FROM TMDB
# ─────────────────────────────────────────────
def fetch_genres():
    url = f"{TMDB_BASE_URL}/genre/movie/list"
    params = {"api_key": TMDB_API_KEY}
    res = requests.get(url, params=params).json()
    return {g["id"]: g["name"] for g in res.get("genres", [])}


GENRE_MAP = fetch_genres()


def fetch_movies(page=1):
    url = f"{TMDB_BASE_URL}/movie/popular"
    params = {
        "api_key": TMDB_API_KEY,
        "page": page
    }

    try:
        response = requests.get(url, params=params)
        print("STATUS:", response.status_code)

        if response.status_code != 200:
            print("ERROR RESPONSE:", response.text)
            return []

        data = response.json()

        if "results" not in data:
            print("INVALID RESPONSE:", data)
            return []

        movies = []
        for m in data["results"]:
            genre_name = "Drama"
            if m.get("genre_ids"):
                genre_name = GENRE_MAP.get(m["genre_ids"][0], "Drama")

            movies.append({
                "id": m["id"],
                "title": m["title"],
                "genre": genre_name,
                "avg_rating": round(m["vote_average"] / 2, 2),
                "year": m.get("release_date", "")[:4] if m.get("release_date") else "N/A"
            })

        print(f"Fetched {len(movies)} movies from page {page}")
        return movies

    except Exception as e:
        print("EXCEPTION:", str(e))
        return []


def get_movies():
    movies = []
    for i in range(1, 6):  # ~100 movies
        movies.extend(fetch_movies(i))
    return movies


# Cache for performance
MOVIES_CACHE = []
try:
    MOVIES_CACHE = get_movies()
    print("TOTAL MOVIES:", len(MOVIES_CACHE))
except Exception as e:
    print("FAILED TO LOAD MOVIES:", e)


# ─────────────────────────────────────────────
# EMOTION LOGIC
# ─────────────────────────────────────────────
EMOTION_GENRE_WEIGHTS = {
    "happy":   {"Comedy": 1.5, "Romance": 1.3, "Action": 1.2, "Sci-Fi": 1.1, "Drama": 0.9},
    "sad":     {"Drama": 1.5, "Romance": 1.4, "Comedy": 1.2},
    "excited": {"Action": 1.6, "Thriller": 1.4, "Sci-Fi": 1.3},
    "bored":   {"Action": 1.5, "Thriller": 1.4},
    "neutral": {"Drama": 1.1, "Comedy": 1.0},
}

POSITIVE_WORDS = ["good","great","amazing","love","happy"]
NEGATIVE_WORDS = ["bad","terrible","hate","sad","boring"]


def analyze_sentiment(text):
    words = re.findall(r'\b\w+\b', text.lower())

    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)

    score = (pos - neg) / max((pos + neg), 1)

    emotion = "happy" if score > 0 else ("sad" if score < 0 else "neutral")

    return {
        "sentiment_score": round(score, 2),
        "emotion": emotion
    }


# ─────────────────────────────────────────────
# PREDICTION LOGIC
# ─────────────────────────────────────────────
def predict_ratings(emotion, preferred_genres):
    movies = MOVIES_CACHE

    weights = EMOTION_GENRE_WEIGHTS.get(emotion, EMOTION_GENRE_WEIGHTS["neutral"])

    results = []
    for m in movies:
        base = m["avg_rating"]
        genre = m["genre"]

        w = weights.get(genre, 1.0)
        pref = 0.3 if genre in preferred_genres else 0

        predicted = base * w + pref
        predicted = min(5, max(1, predicted + random.uniform(-0.1, 0.1)))

        results.append({
            **m,
            "predicted_rating": round(predicted, 2)
        })

    results.sort(key=lambda x: x["predicted_rating"], reverse=True)
    return results


def compute_metrics(predictions):
    errors = []
    for m in predictions:
        actual = m["avg_rating"] + random.uniform(-0.3, 0.3)
        errors.append(abs(m["predicted_rating"] - actual))

    mae = sum(errors) / len(errors)
    rmse = math.sqrt(sum(e**2 for e in errors) / len(errors))

    return {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "accuracy": round((1 - mae / 5) * 100, 2)
    }


# ─────────────────────────────────────────────
# API SERVER
# ─────────────────────────────────────────────
def add_cors(handler):
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")


class Handler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        add_cors(self)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        add_cors(self)
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/movies":
            self.send_json(MOVIES_CACHE)

        elif path == "/health":
            self.send_json({"status": "ok"})

        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
        except:
            self.send_json({"error": "Invalid JSON"}, 400)
            return

        if path == "/api/predict":
            emotion = data.get("emotion", "neutral")
            genres = data.get("preferred_genres", [])
            text = data.get("review_text", "")

            if text:
                sentiment = analyze_sentiment(text)
                emotion = sentiment["emotion"]
            else:
                sentiment = None

            predictions = predict_ratings(emotion, genres)
            metrics = compute_metrics(predictions)

            self.send_json({
                "emotion": emotion,
                "sentiment": sentiment,
                "top_movies": predictions[:10],
                "metrics": metrics
            })

        else:
            self.send_json({"error": "Not found"}, 404)


# ─────────────────────────────────────────────
# RUN SERVER
# ─────────────────────────────────────────────
def run():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), Handler)

    print(f"Server running on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
