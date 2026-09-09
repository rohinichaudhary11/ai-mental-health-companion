# Quick Start Guide

Get the Mental Health Companion up and running in minutes!

## Prerequisites

- Python 3.10 or higher
- pip package manager
- (Optional) CUDA-capable GPU for faster training

## Step 1: Setup Environment

```bash
# Clone or navigate to project directory
cd "AI-Powered Personalized Mental Health Companion"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

## Step 2: Prepare Data

You have two options:

### Option A: Use Sample Data (Quick Testing)

```bash
python scripts/download_data.py --output data/raw/emotion_dataset.csv --create-sample
```

### Option B: Download Full Dataset

1. Download the DAIR-AI Emotion Dataset from: https://github.com/dair-ai/emotion_dataset
2. Place it in `data/raw/emotion_dataset.csv`

## Step 3: Preprocess Data

```bash
python src/data/preprocess.py --input data/raw/emotion_dataset.csv --output data/processed/
```

## Step 4: Train Model

```bash
python src/training/train.py --data_dir data/processed/ --output_dir models/ --epochs 5 --batch_size 32 --learning_rate 2e-5
```

**Note:** Training may take 1-2 hours depending on your hardware. For quick testing, you can reduce epochs to 2-3.

## Step 5: Start the API

Open a terminal and run:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Model loaded successfully!
```

## Step 6: Start the Frontend

Open a **new terminal** (keep API running) and run:

```bash
streamlit run src/frontend/app.py
```

The frontend will open automatically in your browser at `http://localhost:8501`

## Step 7: Test the System

1. In the Streamlit interface, type a message like: "I feel really anxious about tomorrow's exam"
2. The system will:
   - Detect the emotion (likely "fear")
   - Show confidence score
   - Provide a personalized recommendation
   - Display emotion probabilities

## Using the API Directly

You can also test the API directly:

```bash
# Health check
curl http://localhost:8000/healthcheck

# Predict emotion
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"text": "I am feeling great today!"}'
```

## Troubleshooting

### Model Not Found Error

If you see "Model not loaded" error:
- Ensure you've completed Step 4 (training)
- Check that `models/` directory contains model files
- Verify the model path in the API code

### Import Errors

If you encounter import errors:
- Ensure virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.10+)

### Port Already in Use

If port 8000 or 8501 is already in use:
- Change port in API: `uvicorn src.api.main:app --port 8001`
- Update frontend API URL in sidebar to match

### GPU Not Detected

If training is slow:
- Check CUDA installation: `python -c "import torch; print(torch.cuda.is_available())"`
- Install CUDA-enabled PyTorch if needed
- Training will work on CPU, just slower

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Explore the code structure in `src/` directory
- Customize recommendations in `src/recommendations/engine.py`

## Quick Commands Reference

```bash
# Preprocess data
python src/data/preprocess.py --input data/raw/emotion_dataset.csv --output data/processed/

# Train model
python src/training/train.py --data_dir data/processed/ --output_dir models/

# Run API
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Run Frontend
streamlit run src/frontend/app.py

# Run tests
pytest tests/
```

## Using Docker (Alternative)

If you prefer Docker:

```bash
# Build image
docker build -t mental-health-companion .

# Run with docker-compose
docker-compose up
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for more Docker options.

---

**Need Help?** Check the main [README.md](README.md) or open an issue on the repository.

