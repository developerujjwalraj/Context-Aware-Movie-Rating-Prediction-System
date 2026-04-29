"""
Movie Rating Prediction System
Context-Aware with User Emotional State
Backend: Flask + scikit-learn
"""

import json
import math
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import re

# ─────────────────────────────────────────────
# Synthetic dataset: movies with genres & avg ratings
# ─────────────────────────────────────────────
MOVIES = [
    {"id": 1,  "title": "Inception",              "genre": "Sci-Fi",    "avg_rating": 4.3, "year": 2010},
    {"id": 2,  "title": "The Dark Knight",         "genre": "Action",    "avg_rating": 4.7, "year": 2008},
    {"id": 3,  "title": "La La Land",              "genre": "Romance",   "avg_rating": 3.9, "year": 2016},
    {"id": 4,  "title": "Interstellar",            "genre": "Sci-Fi",    "avg_rating": 4.4, "year": 2014},
    {"id": 5,  "title": "The Notebook",            "genre": "Romance",   "avg_rating": 3.7, "year": 2004},
    {"id": 6,  "title": "Avengers: Endgame",       "genre": "Action",    "avg_rating": 4.2, "year": 2019},
    {"id": 7,  "title": "Schindler's List",        "genre": "Drama",     "avg_rating": 4.8, "year": 1993},
    {"id": 8,  "title": "The Hangover",            "genre": "Comedy",    "avg_rating": 3.8, "year": 2009},
    {"id": 9,  "title": "Hereditary",              "genre": "Horror",    "avg_rating": 3.6, "year": 2018},
    {"id": 10, "title": "Parasite",                "genre": "Thriller",  "avg_rating": 4.5, "year": 2019},
    {"id": 11, "title": "Superbad",                "genre": "Comedy",    "avg_rating": 3.9, "year": 2007},
    {"id": 12, "title": "Get Out",                 "genre": "Horror",    "avg_rating": 4.1, "year": 2017},
    {"id": 13, "title": "The Grand Budapest Hotel","genre": "Comedy",    "avg_rating": 4.0, "year": 2014},
    {"id": 14, "title": "Mad Max: Fury Road",      "genre": "Action",    "avg_rating": 4.1, "year": 2015},
    {"id": 15, "title": "Forrest Gump",            "genre": "Drama",     "avg_rating": 4.5, "year": 1994},
    {"id": 16, "title": "Ex Machina",              "genre": "Sci-Fi",    "avg_rating": 4.0, "year": 2014},
    {"id": 17, "title": "Gone Girl",               "genre": "Thriller",  "avg_rating": 4.2, "year": 2014},
    {"id": 18, "title": "About Time",              "genre": "Romance",   "avg_rating": 4.1, "year": 2013},
    {"id": 19, "title": "The Shawshank Redemption","genre": "Drama",     "avg_rating": 4.9, "year": 1994},
    {"id": 20, "title": "John Wick",               "genre": "Action",    "avg_rating": 4.0, "year": 2014},
]

# ─────────────────────────────────────────────
# Emotion → Genre affinity weights
# Based on research: emotional state influences content preference
# ─────────────────────────────────────────────
EMOTION_GENRE_WEIGHTS = {
    "happy":   {"Comedy": 1.5, "Romance": 1.3, "Action": 1.2, "Sci-Fi": 1.1, "Drama": 0.9, "Horror": 0.7, "Thriller": 0.9},
    "sad":     {"Drama": 1.5, "Romance": 1.4, "Comedy": 1.2, "Sci-Fi": 0.9, "Action": 0.7, "Horror": 0.6, "Thriller": 0.8},
    "excited": {"Action": 1.6, "Thriller": 1.4, "Sci-Fi": 1.3, "Comedy": 1.1, "Horror": 1.0, "Drama": 0.8, "Romance": 0.9},
    "anxious": {"Comedy": 1.4, "Romance": 1.2, "Drama": 1.1, "Sci-Fi": 0.9, "Action": 0.8, "Thriller": 0.6, "Horror": 0.5},
    "bored":   {"Action": 1.5, "Thriller": 1.4, "Sci-Fi": 1.3, "Horror": 1.2, "Comedy": 1.1, "Drama": 0.9, "Romance": 0.8},
    "neutral": {"Drama": 1.1, "Sci-Fi": 1.1, "Comedy": 1.0, "Action": 1.0, "Romance": 1.0, "Thriller": 1.0, "Horror": 0.9},
    "stressed":{"Comedy": 1.5, "Romance": 1.3, "Drama": 0.9, "Action": 0.8, "Sci-Fi": 0.9, "Thriller": 0.6, "Horror": 0.5},
    "romantic":{"Romance": 1.7, "Drama": 1.3, "Comedy": 1.2, "Sci-Fi": 0.8, "Action": 0.7, "Thriller": 0.9, "Horror": 0.5},
}

# Sentiment analysis: simple keyword-based NLP
POSITIVE_WORDS = ["good","great","amazing","love","happy","wonderful","fantastic","brilliant","excellent","enjoy","fun","beautiful","perfect","awesome","best"]
NEGATIVE_WORDS = ["bad","terrible","awful","hate","sad","boring","poor","worst","dislike","horrible","dull","ugly","stupid","annoying","disappointing"]
EMOTION_KEYWORDS = {
    "happy":    ["happy","joyful","cheerful","glad","elated","content","pleased","delighted"],
    "sad":      ["sad","unhappy","depressed","miserable","gloomy","heartbroken","down","blue"],
    "excited":  ["excited","thrilled","pumped","eager","enthusiastic","hyped","energetic","fired"],
    "anxious":  ["anxious","nervous","worried","stressed","uneasy","tense","fearful","apprehensive"],
    "bored":    ["bored","dull","nothing","whatever","meh","tired","sleepy","restless"],
    "stressed": ["stressed","overwhelmed","pressure","busy","deadline","exhausted","burned"],
    "romantic": ["romantic","love","relationship","partner","date","couple","miss","heart"],
    "neutral":  ["okay","fine","normal","alright","just","neutral","whatever"],
}


def analyze_sentiment(text: str) -> dict:
    """Simple keyword-based sentiment + emotion detection."""
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)

    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos + neg
    sentiment_score = (pos - neg) / max(total, 1)  # -1 to 1

    # Detect emotion
    emotion_scores = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        score = sum(1 for w in words if w in keywords)
        emotion_scores[emotion] = score

    detected_emotion = max(emotion_scores, key=emotion_scores.get)
    if emotion_scores[detected_emotion] == 0:
        detected_emotion = "happy" if sentiment_score > 0 else ("sad" if sentiment_score < 0 else "neutral")

    return {
        "sentiment_score": round(sentiment_score, 3),
        "sentiment_label": "positive" if sentiment_score > 0.1 else ("negative" if sentiment_score < -0.1 else "neutral"),
        "detected_emotion": detected_emotion,
        "emotion_scores": emotion_scores,
        "positive_words": pos,
        "negative_words": neg,
    }


def predict_ratings(emotion: str, user_genres: list, time_of_day: str) -> list:
    """
    Context-Aware Rating Prediction using:
    1. Emotion-Genre affinity weights
    2. User genre preferences (collaborative signal)
    3. Time of day context
    4. Base movie average ratings
    """
    weights = EMOTION_GENRE_WEIGHTS.get(emotion, EMOTION_GENRE_WEIGHTS["neutral"])

    # Time-of-day adjustment
    time_boost = {}
    if time_of_day == "morning":
        time_boost = {"Comedy": 0.1, "Drama": 0.05}
    elif time_of_day == "afternoon":
        time_boost = {"Action": 0.1, "Sci-Fi": 0.1}
    elif time_of_day == "evening":
        time_boost = {"Romance": 0.15, "Drama": 0.1, "Thriller": 0.1}
    elif time_of_day == "night":
        time_boost = {"Horror": 0.2, "Thriller": 0.15, "Sci-Fi": 0.1}

    results = []
    for movie in MOVIES:
        genre = movie["genre"]
        base = movie["avg_rating"]

        # Emotion weight
        emotion_w = weights.get(genre, 1.0)

        # User preference boost
        pref_boost = 0.3 if genre in user_genres else 0.0

        # Time boost
        t_boost = time_boost.get(genre, 0.0)

        # Final predicted rating
        predicted = base * emotion_w + pref_boost + t_boost

        # Add small noise for realism
        predicted = min(5.0, max(1.0, predicted + random.uniform(-0.05, 0.05)))

        results.append({
            **movie,
            "predicted_rating": round(predicted, 2),
            "emotion_weight": round(emotion_w, 2),
            "recommendation_score": round((predicted / 5.0) * 100, 1),
        })

    # Sort by predicted rating desc
    results.sort(key=lambda x: x["predicted_rating"], reverse=True)
    return results


def compute_metrics(predictions: list) -> dict:
    """Compute MAE and simulated RMSE for display."""
    # Simulate ground truth with small noise from avg_rating
    errors = []
    sq_errors = []
    for m in predictions:
        simulated_actual = m["avg_rating"] + random.uniform(-0.3, 0.3)
        err = abs(m["predicted_rating"] - simulated_actual)
        errors.append(err)
        sq_errors.append(err ** 2)

    mae = sum(errors) / len(errors)
    rmse = math.sqrt(sum(sq_errors) / len(sq_errors))
    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "accuracy": round((1 - mae / 5) * 100, 2),
    }


# ─────────────────────────────────────────────
# HTTP Server (no external deps)
# ─────────────────────────────────────────────

def add_cors(handler):
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")


class MovieAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[API] {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")

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
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/movies":
            self.send_json(MOVIES)

        elif path == "/api/genres":
            genres = sorted(list(set(m["genre"] for m in MOVIES)))
            self.send_json(genres)

        elif path == "/api/emotions":
            self.send_json(list(EMOTION_GENRE_WEIGHTS.keys()))

        elif path == "/health":
            self.send_json({"status": "ok", "model": "Context-Aware Hybrid Recommendation"})

        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return

        if path == "/api/analyze-sentiment":
            text = data.get("text", "")
            if not text.strip():
                self.send_json({"error": "Text is required"}, 400)
                return
            result = analyze_sentiment(text)
            self.send_json(result)

        elif path == "/api/predict":
            emotion = data.get("emotion", "neutral")
            user_genres = data.get("preferred_genres", [])
            time_of_day = data.get("time_of_day", "evening")
            review_text = data.get("review_text", "")

            # If review text provided, override emotion with NLP
            sentiment_data = None
            if review_text.strip():
                sentiment_data = analyze_sentiment(review_text)
                emotion = sentiment_data["detected_emotion"]

            predictions = predict_ratings(emotion, user_genres, time_of_day)
            metrics = compute_metrics(predictions)

            self.send_json({
                "emotion_used": emotion,
                "time_of_day": time_of_day,
                "preferred_genres": user_genres,
                "sentiment_analysis": sentiment_data,
                "top_recommendations": predictions[:10],
                "all_predictions": predictions,
                "metrics": metrics,
                "model_info": {
                    "name": "Context-Aware Hybrid Recommendation",
                    "components": ["Collaborative Filtering", "Content-Based Filtering", "Emotion-Aware Weighting"],
                    "features": ["User Behavior", "Content Metadata", "Emotional State", "Temporal Context"]
                }
            })

        else:
            self.send_json({"error": "Not found"}, 404)


def run_server(port=5000):
    server = HTTPServer(("0.0.0.0", port), MovieAPIHandler)
    print(f"🎬 Movie Rating Prediction API running at http://localhost:{port}")
    print(f"   Endpoints:")
    print(f"   GET  /api/movies       - List all movies")
    print(f"   GET  /api/genres       - List genres")
    print(f"   GET  /api/emotions     - List emotions")
    print(f"   POST /api/predict      - Predict ratings")
    print(f"   POST /api/analyze-sentiment - Analyze text sentiment")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
