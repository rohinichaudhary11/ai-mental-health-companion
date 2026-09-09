@echo off
echo Starting AI Mental Health Companion...

call venv\Scripts\activate

start cmd /k python -m uvicorn src.api.main:app --reload
start cmd /k streamlit run src/frontend/app.py

echo Project started!
pause