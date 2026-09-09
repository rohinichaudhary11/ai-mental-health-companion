# How to Run the Mental Health Companion

## Quick Start (Easiest Method)

### Option 1: Use the Batch Files

1. **Double-click `start_all.bat`** - This will start both API and Frontend in separate windows
2. Wait for both services to start (about 10-15 seconds)
3. Your browser should open automatically to http://localhost:8501
4. If not, manually open: http://localhost:8501

### Option 2: Manual Start (Step by Step)

#### Step 1: Start the API Server

Open a terminal/command prompt and run:
```bash
cd "c:\Users\atuln\Desktop\AI-Powered Personalized Mental Health Companion"
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
Demo mode activated! Using keyword-based emotion detection.
```

**Keep this window open!**

#### Step 2: Start the Frontend

Open a **NEW** terminal/command prompt and run:
```bash
cd "c:\Users\atuln\Desktop\AI-Powered Personalized Mental Health Companion"
streamlit run src/frontend/app.py
```

You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

#### Step 3: Access the Application

1. The Streamlit app should open automatically in your browser
2. If not, manually navigate to: **http://localhost:8501**
3. Start chatting with the AI companion!

## Verify Services Are Running

### Check API
Open in browser: http://localhost:8000
- Should show: `{"message":"Mental Health Companion API",...}`

Or check health: http://localhost:8000/healthcheck
- Should show: `{"status":"healthy","model_loaded":true,...}`

### Check Frontend
Open in browser: http://localhost:8501
- Should show the chat interface

## Using the Application

1. **Type a message** in the chat box, for example:
   - "I feel really anxious about tomorrow's exam"
   - "I'm so happy today!"
   - "This situation makes me angry"

2. **The system will:**
   - Detect your emotion
   - Show confidence scores
   - Provide personalized recommendations
   - Display emotion analytics

## Troubleshooting

### Port Already in Use

If you get "port already in use" error:

**For API (port 8000):**
```bash
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Or use a different port
python -m uvicorn src.api.main:app --port 8001
# Then update frontend API URL in sidebar
```

**For Frontend (port 8501):**
```bash
# Find and kill the process
netstat -ano | findstr :8501
taskkill /PID <process_id> /F

# Or use a different port
streamlit run src/frontend/app.py --server.port 8502
```

### API Not Responding

1. Check if API is running: http://localhost:8000/healthcheck
2. Check the API terminal window for errors
3. Make sure port 8000 is not blocked by firewall

### Frontend Can't Connect to API

1. Check API is running on port 8000
2. In the frontend sidebar, verify API URL is: `http://localhost:8000`
3. If API is on different port, update the API URL in sidebar

### Import Errors

If you see import errors:
```bash
# Reinstall dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Stopping the Services

1. Go to the terminal windows where services are running
2. Press `Ctrl+C` in each window
3. Or simply close the terminal windows

## Testing the API Directly

You can test the API without the frontend:

### Using PowerShell:
```powershell
# Health check
Invoke-WebRequest http://localhost:8000/healthcheck

# Predict emotion
$body = @{text="I feel great today!"} | ConvertTo-Json
Invoke-WebRequest -Method POST -Uri http://localhost:8000/predict -ContentType "application/json" -Body $body
```

### Using Browser:
- API Docs: http://localhost:8000/docs
- Click "Try it out" on the `/predict` endpoint
- Enter text and execute

### Using curl (if available):
```bash
curl http://localhost:8000/healthcheck
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"text\":\"I feel happy\"}"
```

## Next Steps

Once running, you can:
- ✅ Chat with the AI companion
- ✅ View emotion analytics
- ✅ Test different emotions
- ✅ Train a full model for better accuracy (see README.md)

## Need Help?

- Check the main README.md for detailed documentation
- See QUICKSTART.md for setup instructions
- Review DEPLOYMENT.md for production deployment







