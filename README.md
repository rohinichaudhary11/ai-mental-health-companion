# AI-Powered Mental Health Companion

> Live demo: [Mental Health Companion](https://mental-health-frontend-hoec.onrender.com)

An interactive full-stack application that offers emotion-aware conversational support, mood tracking, private journaling, and personalized wellbeing suggestions. It uses FastAPI for the API, Streamlit for the interface, and MongoDB for persisted user data.

## Features

- Email/password authentication using JWTs
- Emotion-aware chat support and CBT-inspired coping suggestions
- Mood tracking and dashboard analytics
- Private journal analysis and saved user history
- MongoDB-backed user, mood, journal, and chat data
- Streamlit frontend and FastAPI backend deployed independently

## Live application

Open the deployed frontend: [mental-health-frontend-hoec.onrender.com](https://mental-health-frontend-hoec.onrender.com)

## Quick start

```bash
pip install -r requirements.txt
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

In a second terminal:

```bash
streamlit run src/frontend/app.py
```

The API runs at `http://localhost:8000` and the UI runs at `http://localhost:8501`.

## Configuration

Copy `.env.example` to `.env` and replace the placeholder values. Never commit `.env` or deployment secrets.

| Variable | Purpose |
| --- | --- |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | Database name |
| `JWT_SECRET_KEY` | JWT signing secret |
| `API_URL` | Backend URL used by the Streamlit app |

## Documentation

- [Render deployment guide](RENDER_DEPLOYMENT.md)
- [MongoDB schema reference](docs_mongodb_schema.md)
- [How to run locally](HOW_TO_RUN.md)

## Important note

This project provides informational wellbeing support and is not a replacement for professional mental-health or emergency care.
