# How to Run Mental Health Companion in VS Code

## Method 1: Using VS Code Debug/Launch (Easiest)

### Step 1: Open the Project
1. Open VS Code
2. File → Open Folder
3. Select: `AI-Powered Personalized Mental Health Companion`

### Step 2: Install Recommended Extensions
VS Code will prompt you to install recommended extensions. Click "Install All" or install:
- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **Black Formatter** (ms-python.black-formatter)

### Step 3: Run the Services

#### Option A: Run API Server
1. Press `F5` or go to **Run and Debug** (Ctrl+Shift+D)
2. Select **"Python: FastAPI"** from the dropdown
3. Click the green play button or press `F5`
4. The API will start on http://localhost:8000

#### Option B: Run Frontend
1. Open a **new terminal** (Terminal → New Terminal or `` Ctrl+` ``)
2. Type: `streamlit run src/frontend/app.py`
3. Press Enter
4. The frontend will start on http://localhost:8501

### Step 4: Run Both Services
You need **two terminals**:
1. **Terminal 1** (API):
   ```bash
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Terminal 2** (Frontend):
   ```bash
   streamlit run src/frontend/app.py --server.port 8501
   ```

---

## Method 2: Using Integrated Terminal (Recommended)

### Step 1: Open Integrated Terminal
- Press `` Ctrl+` `` (backtick) or
- Go to **Terminal → New Terminal**

### Step 2: Start API Server
In the terminal, type:
```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Press Enter. You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
Demo mode activated! Using keyword-based emotion detection.
```

### Step 3: Start Frontend (New Terminal)
1. Click the **+** button next to the terminal tab (or press `` Ctrl+Shift+` ``)
2. In the new terminal, type:
```bash
streamlit run src/frontend/app.py
```
Press Enter. You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### Step 4: Access the Application
- **Frontend**: http://localhost:8501 (opens automatically)
- **API Docs**: http://localhost:8000/docs

---

## Method 3: Using VS Code Tasks

### Step 1: Open Command Palette
- Press `Ctrl+Shift+P`

### Step 2: Run Tasks
1. Type: `Tasks: Run Task`
2. Select:
   - **"Start API Server"** (for API)
   - **"Start Frontend"** (for Frontend)

---

## Quick Start Script (Alternative)

You can also use the batch file from VS Code terminal:

```bash
.\START_PROJECT.bat
```

This will open both services in separate windows.

---

## Debugging in VS Code

### Set Breakpoints
1. Click in the left margin next to line numbers to set breakpoints
2. Press `F5` to start debugging
3. Select **"Python: FastAPI"** configuration
4. Execution will pause at breakpoints

### Debug API Endpoints
1. Set breakpoint in `src/api/main.py` (e.g., in the `predict_emotion` function)
2. Start debugging with `F5`
3. Make a request to the API
4. VS Code will pause at your breakpoint

---

## Troubleshooting

### Port Already in Use
If you see "port already in use":
1. Find the process: `netstat -ano | findstr :8000`
2. Kill it: `taskkill /PID <process_id> /F`
3. Or change the port in launch.json

### Module Not Found
If you see import errors:
1. Open terminal in VS Code
2. Run: `pip install -r requirements.txt`
3. Select the correct Python interpreter:
   - Press `Ctrl+Shift+P`
   - Type: `Python: Select Interpreter`
   - Choose your Python installation

### Terminal Not Working
1. Check Python is in PATH: `python --version`
2. If not, install Python or add to PATH
3. Restart VS Code

---

## VS Code Shortcuts

- `` Ctrl+` `` - Toggle terminal
- `` Ctrl+Shift+` `` - New terminal
- `F5` - Start debugging
- `Ctrl+F5` - Run without debugging
- `Ctrl+Shift+P` - Command palette
- `Ctrl+B` - Toggle sidebar

---

## Recommended VS Code Settings

The project includes `.vscode/settings.json` with:
- Python formatting (Black)
- Linting (Flake8)
- Auto-format on save
- Python path configuration

---

## Running Tests

From VS Code terminal:
```bash
pytest tests/
```

Or use the Test Explorer (install Python Test Explorer extension).

---

## Project Structure in VS Code

```
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

## Tips

1. **Use Split Terminal**: Right-click terminal tab → Split Terminal
2. **Save All**: `Ctrl+K S` to save all files
3. **Format Code**: `Shift+Alt+F` to format current file
4. **Go to Definition**: `F12` on any function/class
5. **Quick Open**: `Ctrl+P` to quickly open files

---

## Next Steps

Once running:
1. Open http://localhost:8501 in your browser
2. Start chatting with the AI companion
3. Check API docs at http://localhost:8000/docs
4. Explore the code in VS Code!














