# Project Structure

Complete overview of the Mental Health Companion project structure.

```
AI-Powered Personalized Mental Health Companion/
│
├── data/                          # Data directory
│   ├── raw/                      # Raw datasets (CSV files)
│   │   └── .gitkeep
│   └── processed/                # Preprocessed datasets
│       ├── train.csv
│       ├── val.csv
│       ├── test.csv
│       └── metadata.json
│
├── models/                        # Trained model files
│   ├── .gitkeep
│   ├── config.json               # Model configuration
│   ├── pytorch_model.bin         # Model weights
│   ├── tokenizer_config.json     # Tokenizer config
│   ├── vocab.txt                 # Vocabulary
│   └── training_config.json      # Training metadata
│
├── logs/                         # Application logs
│   └── .gitkeep
│
├── src/                          # Source code
│   ├── __init__.py
│   │
│   ├── data/                     # Data processing
│   │   ├── __init__.py
│   │   └── preprocess.py         # Data preprocessing script
│   │
│   ├── training/                 # Model training
│   │   ├── __init__.py
│   │   └── train.py              # Training script
│   │
│   ├── inference/                # Model inference
│   │   ├── __init__.py
│   │   └── model_loader.py       # Model loading and prediction
│   │
│   ├── recommendations/          # Recommendation engine
│   │   ├── __init__.py
│   │   └── engine.py             # CBT-based recommendations
│   │
│   ├── api/                      # FastAPI backend
│   │   ├── __init__.py
│   │   └── main.py               # API endpoints
│   │
│   ├── frontend/                 # Streamlit frontend
│   │   ├── __init__.py
│   │   └── app.py                # Streamlit application
│   │
│   └── utils/                    # Utilities
│       ├── __init__.py
│       └── config_loader.py      # Configuration management
│
├── scripts/                       # Utility scripts
│   ├── download_data.py          # Dataset downloader
│   ├── run_training_pipeline.sh  # Training pipeline (Linux/Mac)
│   └── run_training_pipeline.bat # Training pipeline (Windows)
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── test_api.py               # API tests
│   └── test_recommendations.py   # Recommendation engine tests
│
├── .dockerignore                  # Docker ignore patterns
├── .gitignore                     # Git ignore patterns
├── config.yaml                    # Configuration file
├── Dockerfile                     # Docker image definition
├── docker-compose.yml             # Docker Compose configuration
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
│
├── README.md                      # Main documentation
├── QUICKSTART.md                  # Quick start guide
├── DEPLOYMENT.md                  # Deployment guide
└── PROJECT_STRUCTURE.md           # This file
```

## Component Descriptions

### Data Layer (`src/data/`)

- **preprocess.py**: Handles data cleaning, tokenization, and preparation
  - Text normalization and lemmatization
  - Stratified train/val/test splitting
  - Class balancing with SMOTE

### Training Layer (`src/training/`)

- **train.py**: DistilBERT fine-tuning script
  - Hyperparameter optimization
  - Early stopping
  - Model evaluation and metrics
  - Saves best model based on validation F1

### Inference Layer (`src/inference/`)

- **model_loader.py**: Model loading and prediction
  - Loads trained DistilBERT model
  - Handles tokenization
  - Returns emotion probabilities

### Recommendation Layer (`src/recommendations/`)

- **engine.py**: CBT-based recommendation system
  - Maps emotions to evidence-based strategies
  - Provides personalized suggestions
  - Generates explanations

### API Layer (`src/api/`)

- **main.py**: FastAPI REST API
  - `/predict`: Emotion classification endpoint
  - `/healthcheck`: Health monitoring
  - `/predict/batch`: Batch processing
  - CORS enabled for frontend integration

### Frontend Layer (`src/frontend/`)

- **app.py**: Streamlit web interface
  - Interactive chat interface
  - Real-time emotion visualization
  - Emotion trend analytics
  - Session management

## Data Flow

```
User Input (Text)
    ↓
Streamlit Frontend
    ↓
FastAPI Backend (/predict)
    ↓
Emotion Classifier (DistilBERT)
    ↓
Recommendation Engine
    ↓
Response (Emotion + Recommendation)
    ↓
Frontend Display + Visualization
```

## Key Files

### Configuration Files

- **config.yaml**: Centralized configuration
- **requirements.txt**: Python dependencies
- **.env**: Environment variables (create as needed)

### Docker Files

- **Dockerfile**: Single-stage container definition
- **docker-compose.yml**: Multi-service orchestration
- **.dockerignore**: Exclude files from Docker build

### Documentation

- **README.md**: Main project documentation
- **QUICKSTART.md**: Quick setup guide
- **DEPLOYMENT.md**: Production deployment guide

## Directory Conventions

- **data/**: All datasets (raw and processed)
- **models/**: Trained model artifacts
- **logs/**: Application logs
- **src/**: Source code (organized by functionality)
- **scripts/**: Utility and automation scripts
- **tests/**: Unit and integration tests

## Adding New Features

1. **New Emotion**: Update `src/recommendations/engine.py` and retrain model
2. **New Endpoint**: Add to `src/api/main.py`
3. **New Visualization**: Extend `src/frontend/app.py`
4. **New Preprocessing**: Modify `src/data/preprocess.py`

## File Naming Conventions

- Python files: `snake_case.py`
- Directories: `lowercase/`
- Configuration: `kebab-case.yaml` or `UPPERCASE.env`
- Model files: Follow HuggingFace conventions

