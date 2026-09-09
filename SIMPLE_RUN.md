# Simple Guide: Run in VS Code

## 🚀 Quick Start (3 Steps)

### Step 1: Open Terminal
Press `` Ctrl+` `` (backtick key, above Tab)

### Step 2: Start API Server
Type this and press Enter:
```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Step 3: Start Frontend (New Terminal)
1. Click the **+** button next to terminal tab (or press `` Ctrl+Shift+` ``)
2. Type this and press Enter:
```bash
streamlit run src/frontend/app.py
```

**Done!** Open http://localhost:8501 in your browser.

---

## 📝 Visual Guide

```
VS Code Window
├── [Terminal 1] ← Run API here
│   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
│
└── [Terminal 2] ← Run Frontend here
    streamlit run src/frontend/app.py
```

---

## 🎯 That's It!

- **Frontend**: http://localhost:8501
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## ⚠️ If Something Goes Wrong

**Port already in use?**
- Close the terminal and try again
- Or change port: `--port 8001`

**Module not found?**
- Run: `pip install -r requirements.txt`

**Python not found?**
- Install Python from python.org
- Or select Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"







