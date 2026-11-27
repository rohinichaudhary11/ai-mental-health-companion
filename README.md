<div align="center">

# 💚 AI-Powered Mental Health Companion
### Emotion-aware support, private reflection, and personalized wellbeing guidance.

[![Python 3.11](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/) [![MongoDB Atlas](https://img.shields.io/badge/MongoDB_Atlas-47A248?style=flat-square&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/) [![Transformers](https://img.shields.io/badge/Transformers-FFD21E?style=flat-square&logo=huggingface&logoColor=111111)](https://huggingface.co/docs/transformers/index) [![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

An intelligent full-stack application for emotion-aware conversational support, private journaling, mood tracking, and personalized wellbeing suggestions.

🌐 **Live application:** [Frontend UI](https://ai-mental-health-companionn.streamlit.app/) · [Backend API](https://ai-mental-health-companion-main.onrender.com) · [Swagger docs](https://ai-mental-health-companion-main.onrender.com/docs)

**[Key Features](#-key-features) · [Architecture](#️-architecture--workflow) · [Tech Stack](#️-tech-stack) · [Running Locally](#-running-locally) · [Repository Structure](#-repository-structure)**

> **⚠️ Disclaimer:** This AI companion provides informational wellbeing support and CBT-inspired coping ideas. It is **not** a replacement for professional medical advice, diagnosis, therapy, or emergency care.

* * *

</div>

## 📌 Overview

This project combines a Streamlit frontend, a FastAPI backend, MongoDB Atlas storage, and machine-learning services to create a secure space for reflection and wellbeing support. It is designed to complement professional care, never replace it.

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

| Domain | Technologies Used |
| --- | --- |
| Backend API | Python 3.11, FastAPI, Uvicorn, Pydantic, Motor, Passlib, python-jose |
| Frontend UI | Streamlit, Requests, Plotly, Pandas |
| Machine learning and NLP | HuggingFace Transformers, PyTorch, scikit-learn |
| Database | MongoDB Atlas, PyMongo, Motor |
| Infrastructure | Docker, Render, Streamlit Community Cloud |

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

---

## 📚 Documentation

- [Deployment guide](DEPLOYMENT.md)
- [How to run the project](HOW_TO_RUN.md)
- [Quick start guide](QUICKSTART.md)
- [Project structure](PROJECT_STRUCTURE.md)
- [MongoDB schema](docs_mongodb_schema.md)
- [Render deployment](RENDER_DEPLOYMENT.md)

---

## 🤝 Contributing

Contributions and suggestions are welcome. Fork the repository, create a feature branch, make your changes, and open a pull request with a clear description of what was improved. Please avoid committing secrets, database credentials, or private user data.

Before submitting a change, run the relevant API tests and verify that the application still respects the mental-health disclaimer and privacy expectations.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
