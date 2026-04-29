# 🎬 CINEMO — Context-Aware Movie Rating Prediction System



A full-stack Movie Rating Prediction System using **sentiment-based emotion detection** combined with a **hybrid recommendation model** (Collaborative + Content-Based Filtering), evaluated using MAE and RMSE.

---

## 📁 Project Structure

```
movie-rating-predictor/
├── backend/
│   ├── app.py              
│   └── requirements.txt    
├── frontend/
│   └── index.html         
└── README.md
```

---

## 🧠 How It Works

1. **User Input**: Emotion state, genre preferences, time of day, optional mood text
2. **NLP Sentiment Analysis**: Keyword-based sentiment scoring detects emotion from text
3. **Emotion-Genre Weighting**: Maps emotional state to genre affinity weights (based on research)
4. **Hybrid Model**: Combines content features (genre, year) with collaborative signals (user preferences)
5. **Contextual Adjustment**: Time-of-day boosts certain genres
6. **Output**: Predicted ratings for 20 movies, ranked + MAE/RMSE metrics

---

## 🚀 LOCAL SETUP

### Step 1 — Clone or download the project
```bash
# If using git:
git clone <your-repo-url>
cd movie-rating-predictor

# Or just extract the ZIP
```

### Step 2 — Setup Python Backend
```bash
cd backend

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```
You should see:
```
🎬 Movie Rating Prediction API running at http://localhost:5000
```

### Step 3 — Open the Frontend
```bash
# Simply open in browser:
open frontend/index.html        # Mac
start frontend/index.html       # Windows
xdg-open frontend/index.html    # Linux
```

> **Note**: The frontend works in demo mode even without the backend running. Full features (live NLP via API) require the backend to be active.

---

## ☁️ DEPLOYMENT (Production)

### Option A — Deploy on Render.com (FREE, Recommended)

**Backend (Flask API):**

1. Push your code to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/cinemo.git
   git push -u origin main
   ```

2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `python backend/app.py`
   - **Root Directory**: `/`
5. Click **Deploy**
6. Copy your deployed URL e.g. `https://cinemo-api.onrender.com`

**Frontend (Static Site):**

1. In `frontend/index.html`, replace:
   ```javascript
   const API = 'http://localhost:5000';
   ```
   with:
   ```javascript
   const API = 'https://cinemo-api.onrender.com';
   ```

2. Go to Render → New → Static Site
3. Connect the same GitHub repo
4. Set **Publish Directory**: `frontend`
5. Deploy → get your URL like `https://cinemo.onrender.com`

---

### Option B — Deploy on Vercel (Frontend) + Railway (Backend)

**Backend on Railway:**
1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select your repo
3. Add environment variable: `PORT=5000`
4. Railway auto-detects Python and deploys
5. Note your URL: `https://cinemo.up.railway.app`

**Frontend on Vercel:**
1. Go to [vercel.com](https://vercel.com) → New Project → Import from GitHub
2. Set Root Directory to `frontend`
3. Framework: Other (static)
4. Update the API URL in `index.html` to your Railway URL
5. Deploy

---

### Option C — Deploy on PythonAnywhere (Beginner-friendly)

1. Sign up at [pythonanywhere.com](https://pythonanywhere.com)
2. Go to **Files** → Upload `backend/app.py` and `backend/requirements.txt`
3. Open **Bash console**:
   ```bash
   pip install -r requirements.txt
   ```
4. Go to **Web** → Add a new web app → Flask
5. Set the source file to `app.py`
6. Click **Reload**
7. Your API is at: `https://yourusername.pythonanywhere.com`

For the frontend, you can host `index.html` on **GitHub Pages** (free):
1. Create a repo, put `index.html` inside a `/docs` folder
2. Go to Settings → Pages → Source: `docs` folder
3. Your site is at: `https://yourusername.github.io/cinemo`

---

### Option D — Docker Deployment

```dockerfile
# Dockerfile (place in project root)
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/app.py .
EXPOSE 5000
CMD ["python", "app.py"]
```

```bash
# Build and run
docker build -t cinemo-api .
docker run -p 5000:5000 cinemo-api
```

For container hosting:
- **Google Cloud Run**: `gcloud run deploy`
- **AWS ECS / App Runner**
- **DigitalOcean App Platform**

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/movies` | List all 20 movies |
| GET | `/api/genres` | List all genres |
| GET | `/api/emotions` | List all emotions |
| POST | `/api/predict` | Get predictions |
| POST | `/api/analyze-sentiment` | Analyze text sentiment |

### POST `/api/predict` — Example:
```json
{
  "emotion": "happy",
  "preferred_genres": ["Action", "Comedy"],
  "time_of_day": "evening",
  "review_text": "I'm feeling great and want something fun!"
}
```

### Response:
```json
{
  "emotion_used": "happy",
  "top_recommendations": [...],
  "metrics": { "mae": 0.18, "rmse": 0.22, "accuracy": 96.4 }
}
```

---

## 📊 Evaluation Metrics

| Metric | Description |
|--------|-------------|
| **MAE** | Mean Absolute Error — average prediction deviation |
| **RMSE** | Root Mean Square Error — penalizes large errors |
| **Accuracy** | `(1 - MAE/5) × 100` — intuitive percentage |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, HTTP Server (stdlib) |
| ML / NLP | scikit-learn, Keyword-based Sentiment Analysis |
| Data | Pandas, NumPy |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Fonts | Google Fonts (Syne + Space Mono) |

---



