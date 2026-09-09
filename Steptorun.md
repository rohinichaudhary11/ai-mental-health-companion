For Backend
cd "C:\Users\atuln\Desktop\AI-Powered Personalized Mental Health Companion"
.\venv\Scripts\Activate.ps1
uvicorn src.api.main:app --host 0.0.0.0 --port 8000



Crt + SHIFT + 5 


For Frontend
cd "C:\Users\atuln\Desktop\AI-Powered Personalized Mental Health Companion"
 .\venv\Scripts\Activate.ps1
 streamlit run src/frontend/app.py



 📁 AI-Powered Personalized Mental Health Companion
├── 📁 src/
│   ├── 📁 api/          → FastAPI backend
│   ├── 📁 frontend/     → Streamlit frontend
│   ├── 📁 training/     → Model training
│   ├── 📁 inference/    → Model inference
│   └── 📁 recommendations/ → Recommendation engine
├── 📁 data/             → Data files
├── 📁 models/           → Trained models
├── 📁 tests/            → Test files
├── 📄 README.md         → Main documentation
└── 📄 START_PROJECT.bat → Quick start script
```

---
