# Deployment Guide

This guide covers deployment options for the Mental Health Companion system.

## Local Development

### Prerequisites
- Python 3.10+
- Virtual environment
- CUDA-capable GPU (optional, for training)

### Setup

1. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

2. **Train the model** (if not already done)
```bash
# Windows
scripts\run_training_pipeline.bat

# Linux/Mac
bash scripts/run_training_pipeline.sh
```

3. **Start the API**
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

4. **Start the frontend** (in a new terminal)
```bash
streamlit run src/frontend/app.py
```

## Docker Deployment

### Build and Run

1. **Build Docker image**
```bash
docker build -t mental-health-companion .
```

2. **Run with Docker Compose**
```bash
docker-compose up -d
```

This will start both API (port 8000) and frontend (port 8501).

3. **Check logs**
```bash
docker-compose logs -f
```

4. **Stop services**
```bash
docker-compose down
```

### Manual Docker Run

```bash
# API only
docker run -p 8000:8000 -v $(pwd)/models:/app/models mental-health-companion

# Frontend only
docker run -p 8501:8501 -e API_URL=http://host.docker.internal:8000 mental-health-companion streamlit run src/frontend/app.py --server.port 8501
```

## Cloud Deployment

### Google Cloud Run

1. **Build and push to Container Registry**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/mental-health-companion
```

2. **Deploy to Cloud Run**
```bash
gcloud run deploy mental-health-companion \
  --image gcr.io/PROJECT_ID/mental-health-companion \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

### AWS Elastic Beanstalk

1. **Create application**
```bash
eb init -p docker mental-health-companion
```

2. **Create environment**
```bash
eb create mental-health-companion-env
```

3. **Deploy**
```bash
eb deploy
```

### Azure Container Instances

1. **Create resource group**
```bash
az group create --name mental-health-rg --location eastus
```

2. **Deploy container**
```bash
az container create \
  --resource-group mental-health-rg \
  --name mental-health-companion \
  --image mental-health-companion:latest \
  --dns-name-label mental-health-companion \
  --ports 8000 8501
```

## Production Considerations

### Environment Variables

Create a `
` file:
```env
API_URL=http://localhost:8000
MODEL_PATH=models
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://yourdomain.com
```

### Security

1. **HTTPS**: Use reverse proxy (nginx) with SSL certificates
2. **Authentication**: Add API keys or OAuth for production
3. **Rate Limiting**: Implement rate limiting on API endpoints
4. **CORS**: Restrict CORS origins to your domain

### Scaling

1. **Horizontal Scaling**: Use Kubernetes or load balancer
2. **Caching**: Implement Redis for frequently accessed predictions
3. **Database**: Add database for session persistence (optional)
4. **Monitoring**: Set up logging and monitoring (e.g., Prometheus, Grafana)

### Performance Optimization

1. **Model Optimization**: Use ONNX or TensorRT for faster inference
2. **Batch Processing**: Process multiple requests in batches
3. **GPU Acceleration**: Deploy on GPU instances for faster inference
4. **CDN**: Use CDN for static frontend assets

## Health Checks

The API includes a health check endpoint:
```bash
curl http://localhost:8000/healthcheck
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2025-01-XX..."
}
```

## Troubleshooting

### Model Not Loading

- Ensure model files exist in `models/` directory
- Check model path in API configuration
- Verify model files are not corrupted

### API Connection Issues

- Check if API is running on correct port
- Verify firewall settings
- Check CORS configuration

### High Latency

- Use GPU for inference
- Reduce batch size
- Optimize model (quantization, pruning)
- Use model caching

## Monitoring

### Logs

Logs are written to `logs/` directory. Monitor for:
- API errors
- High latency warnings
- Model loading issues

### Metrics to Monitor

- Request latency (target: <200ms)
- Error rate (target: <1%)
- Model confidence scores
- API uptime
- Resource usage (CPU, memory, GPU)

