# Render Deployment

This project is deployed as two Python web services in the same Render project.

| Service | Purpose | Build command | Start command |
| --- | --- | --- | --- |
| FastAPI backend | API, authentication, MongoDB access | `pip install -r requirements.txt` | `python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT` |
| Streamlit frontend | User interface | `pip install -r requirements.txt` | `streamlit run src/frontend/app.py --server.address 0.0.0.0 --server.port $PORT` |

## Backend variables

Configure these in the FastAPI service's **Environment** page:

```text
MONGODB_URI=<your MongoDB Atlas URI>
MONGODB_DB_NAME=mental_health_companion
JWT_SECRET_KEY=<generated secret>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
PYTHON_VERSION=3.11.11
```

## Frontend variables

Configure this in the Streamlit service's **Environment** page:

```text
API_URL=https://<your-backend-service>.onrender.com
PYTHON_VERSION=3.11.11
```

## Verification

1. Open `https://<your-backend-service>.onrender.com/healthcheck`.
2. Open `https://<your-backend-service>.onrender.com/docs`.
3. Open the Streamlit service URL and check that its sidebar says **API Connected**.
4. Create a test account, then test login, chat, mood logging, and journal saving.

## Security checklist

- Do not commit `.env`, MongoDB URIs, JWT secrets, or passwords.
- Use distinct MongoDB users and databases for development and production.
- Restrict MongoDB network access and rotate credentials if a secret is exposed.
- Before public release, restrict API CORS to the frontend's production URL.
