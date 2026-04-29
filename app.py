import json
import math
import random
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import re
import os

# ================= API KEY =================
API_KEY = "9eaba43292d7ca6807b0897a106cd623"   # 👈 PUT YOUR OMDb API KEY

# ================= FETCH MOVIE FROM API =================
def fetch_movie(movie_name):
    url = f"https://www.omdbapi.com/?t={movie_name}&apikey={API_KEY}"
    res = requests.get(url)
    data = res.json()

    if data.get("Response") == "False":
        return None

    return {
        "title": data["Title"],
        "genre": data["Genre"].split(",")[0],
        "avg_rating": float(data["imdbRating"]) / 2 if data["imdbRating"] != "N/A" else 3.5,
        "year": int(data["Year"][:4])
    }

# ================= EMOTION WEIGHTS =================
EMOTION_GENRE_WEIGHTS = {
    "happy":   {"Comedy": 1.5, "Romance": 1.3, "Action": 1.2, "Sci-Fi": 1.1, "Drama": 0.9, "Horror": 0.7, "Thriller": 0.9},
    "sad":     {"Drama": 1.5, "Romance": 1.4, "Comedy": 1.2, "Sci-Fi": 0.9, "Action": 0.7, "Horror": 0.6, "Thriller": 0.8},
    "excited": {"Action": 1.6, "Thriller": 1.4, "Sci-Fi": 1.3, "Comedy": 1.1, "Horror": 1.0, "Drama": 0.8, "Romance": 0.9},
    "neutral": {"Drama": 1.1, "Sci-Fi": 1.1, "Comedy": 1.0, "Action": 1.0, "Romance": 1.0, "Thriller": 1.0, "Horror": 0.9},
    "stressed":{"Comedy": 1.5, "Romance": 1.3, "Drama": 0.9, "Action": 0.8, "Sci-Fi": 0.9, "Thriller": 0.6, "Horror": 0.5},
    "romantic":{"Romance": 1.7, "Drama": 1.3, "Comedy": 1.2, "Sci-Fi": 0.8, "Action": 0.7, "Thriller": 0.9, "Horror": 0.5}
}

# ================= SENTIMENT =================
POSITIVE_WORDS = ["good","great","amazing","love","happy","awesome"]
NEGATIVE_WORDS = ["bad","terrible","awful","hate","sad","boring"]

def analyze_sentiment(text):
    words = re.findall(r'\b\w+\b', text.lower())
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)

    if pos > neg:
        return "happy"
    elif neg > pos:
        return "sad"
    return "neutral"

# ================= PREDICT =================
def predict_rating(movie, emotion, user_genres):
    weights = EMOTION_GENRE_WEIGHTS.get(emotion, EMOTION_GENRE_WEIGHTS["neutral"])

    base = movie["avg_rating"]
    genre = movie["genre"]

    emotion_w = weights.get(genre, 1.0)
    pref_boost = 0.3 if genre in user_genres else 0.0

    predicted = base * emotion_w + pref_boost
    predicted = min(5.0, max(1.0, predicted + random.uniform(-0.05, 0.05)))

    return round(predicted, 2)

# ================= SERVER =================
class Handler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        data = json.loads(body)

        if self.path == "/api/predict":

            movie_name = data.get("movie")
            emotion = data.get("emotion", "neutral")
            user_genres = data.get("preferred_genres", [])
            review_text = data.get("review_text", "")

            # NLP override
            if review_text.strip():
                emotion = analyze_sentiment(review_text)

            # 🔥 Fetch movie from API
            movie = fetch_movie(movie_name)

            if not movie:
                self.send_json({"error": "Movie not found"})
                return

            rating = predict_rating(movie, emotion, user_genres)

            self.send_json({
                "title": movie["title"],
                "genre": movie["genre"],
                "year": movie["year"],
                "predicted_rating": rating,
                "emotion_used": emotion
            })

# ================= RUN =================
def run():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Server running at http://localhost:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run()
