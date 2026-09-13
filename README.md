# 💚 AI-Powered Mental Health Companion

An intelligent, full-stack application designed to provide emotion-aware conversational support, private journaling, mood tracking, and personalized wellbeing suggestions. Built with **FastAPI**, **Streamlit**, and **MongoDB Atlas**, this application offers a secure and interactive environment for users to reflect on their mental health.

> **⚠️ Disclaimer:** This AI companion provides informational wellbeing support and CBT-inspired coping ideas. It is **not** a replacement for professional medical advice, diagnosis, therapy, or emergency care.

---

## 🌍 Live Application Links

You can test the application live without installing anything locally:

- **Frontend UI (Streamlit):** [https://ai-mental-health-companionn.streamlit.app/](https://ai-mental-health-companionn.streamlit.app/)
- **Backend API (Render):** [https://ai-mental-health-companion-main.onrender.com](https://ai-mental-health-companion-main.onrender.com)
- **API Documentation (Swagger):** [https://ai-mental-health-companion-main.onrender.com/docs](https://ai-mental-health-companion-main.onrender.com/docs)

---

## ✨ Key Features

- **Secure Authentication:** JWT-based email/password signup and login system to keep user data private.
- **Emotion-Aware Chat Therapist:** An AI chat interface that detects user emotions (via a DistilBERT text-classification model fallback to heuristics) and provides empathetic responses, CBT techniques, and confidence scores.
- **Medical Assistance Panel:** Automatically detects high-risk keywords (e.g., anxiety attacks, depression) and provides a dedicated panel with coping mechanisms, nearby support types, and emergency contact numbers.
- **Mood Tracking & Analytics:** Quick mood check-ins (1-5 scale with emojis) and a visual analytics dashboard mapping emotion distribution and timeline.
- **Guided Wellness:** Includes interactive visual breathing exercises (Box Breathing, 4-7-8 Relaxation) to help users manage stress in real-time.
- **Private Journaling:** A safe space to write journal entries, which are analyzed for emotional trends and stored securely in MongoDB.

---

## 🏗️ Architecture & Workflow

The project is structured into a modern, decoupled architecture:

### 1. Frontend (Streamlit UI)
Located in `src/frontend/app.py`. It handles all user interactions, session management, and visual data plotting (using Plotly). It communicates exclusively with the FastAPI backend via RESTful HTTP calls.

### 2. Backend (FastAPI)
A highly modular, router-based API located in `src/api/`. 
- **Routers (`src/api/routers/`):** Separated endpoints for `auth`, `chat`, `journal`, `mood`, `medical`, and `analytics`.
- **Services (`src/api/services/`):** Business logic layer handling NLP classification, crisis detection, and medical knowledge bases.
- **Database (`src/db/mongo.py`):** Motor (async MongoDB driver) handles asynchronous connections to MongoDB Atlas.

### 3. Database (MongoDB Atlas)
Stores document data in 4 main collections within the `mental_health_companion` database:
- `users`: Credentials and profiles.
- `chat_history`: Therapist conversation logs with detected emotions.
- `journal_entries`: User journal texts and analysis.
- `mood_logs`: Daily quick-check-in data.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.11, FastAPI, Uvicorn, Pydantic, Motor (Async MongoDB), Passlib, python-jose (JWT)
- **Frontend:** Streamlit, Requests, Plotly, Pandas
- **Machine Learning / NLP:** HuggingFace Transformers (`transformers`, `torch`), Scikit-learn
- **Infrastructure:** Docker, Render (Backend Hosting), Streamlit Community Cloud (Frontend Hosting)

---

## 🚀 Running Locally

Want to run the project on your own machine? Follow these steps:

### 1. Clone and setup environment
```bash
git clone https://github.com/rohinichaudhary11/ai-mental-health-companion-main.git
cd ai-mental-health-companion-main
python -m venv venv

# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory based on `.env.example`:

```env
# MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/mental_health_companion?retryWrites=true&w=majority&appName=Cluster0
MONGODB_DB_NAME=mental_health_companion

# Authentication
JWT_SECRET_KEY=your-secure-random-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Frontend Configuration
API_URL=http://127.0.0.1:8000
```

### 3. Start the Backend API
Run the FastAPI server:
```bash
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

### 4. Start the Frontend UI
Open a **new terminal window**, activate the virtual environment, and run:
```bash
python -m streamlit run src/frontend/app.py
```
The app will open automatically in your browser at `http://localhost:8501`.

---

## 📁 Repository Structure

```text
├── src/
│   ├── api/
│   │   ├── routers/       # Modular API endpoints (auth, chat, mood, etc.)
│   │   ├── services/      # Business logic (crisis detection, NLP, medical)
│   │   ├── deps.py        # Dependency injection (DB, Auth)
│   │   ├── main.py        # FastAPI application factory and lifespan
│   │   ├── schemas.py     # Pydantic models for request/response validation
│   │   └── state.py       # Global app state management
│   ├── db/
│   │   └── mongo.py       # Async MongoDB connection management
│   ├── frontend/
│   │   └── app.py         # Streamlit User Interface
│   ├── training/          # Model training scripts
│   └── data/              # Data preprocessing scripts
├── tests/                 
│   └── test_api_endpoints.py # Integration test suite for API
├── .env.example           # Environment variables template
├── Dockerfile             # Container definition
├── requirements.txt       # Combined dependencies
├── requirements-api.txt   # Backend specific dependencies
└── requirements-frontend.txt # Frontend specific dependencies
```
