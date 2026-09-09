"""
Model loading and inference utilities for emotion classification.
Handles model loading, text preprocessing, and prediction.
"""

import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from pathlib import Path
import json
from typing import Dict, List, Optional
import numpy as np


class EmotionClassifier:
    """Emotion classification model wrapper."""
    
    def __init__(self, model_path: str, device: Optional[str] = None):
        """
        Initialize emotion classifier.
        
        Args:
            model_path: Path to trained model directory
            device: Device to run inference on ('cuda' or 'cpu')
        """
        self.model_path = Path(model_path)
        
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        # Load tokenizer and model
        print(f"Loading model from {model_path}...")
        self.tokenizer = DistilBertTokenizer.from_pretrained(str(self.model_path))
        self.model = DistilBertForSequenceClassification.from_pretrained(str(self.model_path))
        self.model.to(self.device)
        self.model.eval()
        
        # Load emotion mapping
        self.idx_to_emotion = {
            0: 'joy',
            1: 'sadness',
            2: 'anger',
            3: 'fear',
            4: 'disgust',
            5: 'surprise'
        }
        self.emotion_to_idx = {v: k for k, v in self.idx_to_emotion.items()}
        
        # Load config if available
        config_path = self.model_path / 'training_config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}
        
        print(f"Model loaded successfully on {self.device}")
    
    def predict(self, text: str, return_probs: bool = True, max_length: int = 128) -> Dict:
        """
        Predict emotion from text.
        
        Args:
            text: Input text string
            return_probs: Whether to return probability distribution
            max_length: Maximum sequence length
        
        Returns:
            Dictionary with prediction results
        """
        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=max_length,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)
        
        # Get predicted class
        pred_idx = torch.argmax(probs, dim=1).item()
        predicted_emotion = self.idx_to_emotion[pred_idx]
        confidence = probs[0][pred_idx].item()
        
        result = {
            'emotion': predicted_emotion,
            'confidence': confidence
        }
        
        if return_probs:
            probabilities = {
                self.idx_to_emotion[i]: float(probs[0][i].item())
                for i in range(len(self.idx_to_emotion))
            }
            result['probabilities'] = probabilities
        
        return result
    
    def predict_batch(self, texts: List[str], max_length: int = 128) -> List[Dict]:
        """
        Predict emotions for multiple texts.
        
        Args:
            texts: List of input text strings
            max_length: Maximum sequence length
        
        Returns:
            List of prediction dictionaries
        """
        # Tokenize batch
        encodings = self.tokenizer(
            texts,
            truncation=True,
            padding='max_length',
            max_length=max_length,
            return_tensors='pt'
        )
        
        input_ids = encodings['input_ids'].to(self.device)
        attention_mask = encodings['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)
        
        # Process results
        results = []
        for i in range(len(texts)):
            pred_idx = torch.argmax(probs[i]).item()
            predicted_emotion = self.idx_to_emotion[pred_idx]
            confidence = probs[i][pred_idx].item()
            
            probabilities = {
                self.idx_to_emotion[j]: float(probs[i][j].item())
                for j in range(len(self.idx_to_emotion))
            }
            
            results.append({
                'emotion': predicted_emotion,
                'confidence': confidence,
                'probabilities': probabilities
            })
        
        return results
    
    def get_attention_weights(self, text: str, max_length: int = 128) -> Optional[np.ndarray]:
        """
        Get attention weights for interpretability (if model supports it).
        
        Args:
            text: Input text
            max_length: Maximum sequence length
        
        Returns:
            Attention weights array (if available)
        """
        # Note: DistilBERT doesn't easily expose attention weights
        # This is a placeholder for future implementation with explainability tools
        return None


def load_classifier(model_path: str = "models", device: Optional[str] = None) -> EmotionClassifier:
    """
    Convenience function to load emotion classifier.
    
    Args:
        model_path: Path to model directory
        device: Device to use
    
    Returns:
        EmotionClassifier instance
    """
    return EmotionClassifier(model_path, device)

