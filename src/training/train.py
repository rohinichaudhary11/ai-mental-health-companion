"""
Training script for fine-tuning DistilBERT on emotion classification task.
Implements hyperparameter optimization, early stopping, and model evaluation.
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    DistilBertConfig,
    get_linear_schedule_with_warmup
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
import pandas as pd
import numpy as np
import json
import argparse
from pathlib import Path
from tqdm import tqdm
import os
from datetime import datetime

# Set random seeds for reproducibility
torch.manual_seed(42)
np.random.seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(42)


class EmotionDataset(Dataset):
    """Dataset class for emotion classification."""
    
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        # Map emotions to indices
        self.emotion_to_idx = {
            'joy': 0, 'sadness': 1, 'anger': 2,
            'fear': 3, 'disgust': 4, 'surprise': 5
        }
        self.idx_to_emotion = {v: k for k, v in self.emotion_to_idx.items()}
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(self.emotion_to_idx[label], dtype=torch.long)
        }


def load_data(data_dir):
    """Load train, validation, and test datasets."""
    data_dir = Path(data_dir)
    
    train_df = pd.read_csv(data_dir / 'train.csv')
    val_df = pd.read_csv(data_dir / 'val.csv')
    test_df = pd.read_csv(data_dir / 'test.csv')
    
    return train_df, val_df, test_df


def evaluate_model(model, dataloader, device, idx_to_emotion):
    """Evaluate model on a dataset."""
    model.eval()
    predictions = []
    true_labels = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            
            preds = torch.argmax(logits, dim=1)
            predictions.extend(preds.cpu().numpy())
            true_labels.extend(labels.cpu().numpy())
    
    # Calculate metrics
    accuracy = accuracy_score(true_labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_labels, predictions, average='macro', zero_division=0
    )
    
    # Per-class metrics
    precision_per_class, recall_per_class, f1_per_class, _ = precision_recall_fscore_support(
        true_labels, predictions, average=None, zero_division=0
    )
    
    results = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'per_class': {
            emotion: {
                'precision': float(precision_per_class[i]),
                'recall': float(recall_per_class[i]),
                'f1': float(f1_per_class[i])
            }
            for i, emotion in idx_to_emotion.items()
        }
    }
    
    return results, predictions, true_labels


def train_model(
    train_df,
    val_df,
    model_name='distilbert-base-uncased',
    output_dir='models',
    epochs=5,
    batch_size=32,
    learning_rate=2e-5,
    dropout=0.1,
    weight_decay=0.01,
    max_length=128,
    device=None
):
    """Train DistilBERT model for emotion classification."""
    
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    print(f"Using device: {device}")
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize tokenizer and model
    print("Loading tokenizer and model...")
    tokenizer = DistilBertTokenizer.from_pretrained(model_name)
    
    config = DistilBertConfig.from_pretrained(model_name)
    config.num_labels = 6
    config.dropout = dropout
    model = DistilBertForSequenceClassification.from_pretrained(model_name, config=config)
    model.to(device)
    
    # Create datasets
    print("Creating datasets...")
    train_dataset = EmotionDataset(
        train_df['processed_text'].tolist(),
        train_df['emotion'].tolist(),
        tokenizer,
        max_length=max_length
    )
    val_dataset = EmotionDataset(
        val_df['processed_text'].tolist(),
        val_df['emotion'].tolist(),
        tokenizer,
        max_length=max_length
    )
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Setup optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=0,
        num_training_steps=total_steps
    )
    
    # Training loop
    best_f1 = 0.0
    patience = 3
    patience_counter = 0
    training_history = []
    
    idx_to_emotion = train_dataset.idx_to_emotion
    
    print(f"\nStarting training for {epochs} epochs...")
    print(f"Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")
    
    for epoch in range(epochs):
        print(f"\nEpoch {epoch + 1}/{epochs}")
        model.train()
        total_loss = 0
        
        progress_bar = tqdm(train_loader, desc=f"Training Epoch {epoch + 1}")
        for batch in progress_bar:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            optimizer.zero_grad()
            
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            
            total_loss += loss.item()
            progress_bar.set_postfix({'loss': loss.item()})
        
        avg_loss = total_loss / len(train_loader)
        
        # Evaluate on validation set
        print("Evaluating on validation set...")
        val_results, _, _ = evaluate_model(model, val_loader, device, idx_to_emotion)
        
        print(f"Validation - Accuracy: {val_results['accuracy']:.4f}, "
              f"F1: {val_results['f1']:.4f}, Loss: {avg_loss:.4f}")
        
        training_history.append({
            'epoch': epoch + 1,
            'train_loss': avg_loss,
            'val_accuracy': val_results['accuracy'],
            'val_f1': val_results['f1']
        })
        
        # Early stopping
        if val_results['f1'] > best_f1:
            best_f1 = val_results['f1']
            patience_counter = 0
            
            # Save best model
            print(f"New best F1: {best_f1:.4f}. Saving model...")
            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)
            
            # Save training config
            config_dict = {
                'model_name': model_name,
                'epochs': epoch + 1,
                'batch_size': batch_size,
                'learning_rate': learning_rate,
                'dropout': dropout,
                'weight_decay': weight_decay,
                'max_length': max_length,
                'best_f1': best_f1,
                'training_history': training_history
            }
            
            with open(output_dir / 'training_config.json', 'w') as f:
                json.dump(config_dict, f, indent=2)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping triggered after {epoch + 1} epochs")
                break
    
    print(f"\nTraining completed. Best F1: {best_f1:.4f}")
    return model, tokenizer, training_history


def main():
    parser = argparse.ArgumentParser(description="Train DistilBERT for emotion classification")
    parser.add_argument("--data_dir", type=str, required=True, help="Directory with processed data")
    parser.add_argument("--output_dir", type=str, default="models", help="Output directory for model")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout rate")
    parser.add_argument("--weight_decay", type=float, default=0.01, help="Weight decay")
    parser.add_argument("--max_length", type=int, default=128, help="Max sequence length")
    parser.add_argument("--model_name", type=str, default="distilbert-base-uncased", help="Base model name")
    
    args = parser.parse_args()
    
    # Load data
    train_df, val_df, test_df = load_data(args.data_dir)
    
    # Train model
    model, tokenizer, history = train_model(
        train_df,
        val_df,
        model_name=args.model_name,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        dropout=args.dropout,
        weight_decay=args.weight_decay,
        max_length=args.max_length
    )
    
    # Evaluate on test set
    print("\nEvaluating on test set...")
    test_dataset = EmotionDataset(
        test_df['processed_text'].tolist(),
        test_df['emotion'].tolist(),
        tokenizer,
        max_length=args.max_length
    )
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    test_results, predictions, true_labels = evaluate_model(
        model, test_loader, device, test_dataset.idx_to_emotion
    )
    
    print(f"\nTest Results:")
    print(f"Accuracy: {test_results['accuracy']:.4f}")
    print(f"Precision: {test_results['precision']:.4f}")
    print(f"Recall: {test_results['recall']:.4f}")
    print(f"F1-Score: {test_results['f1']:.4f}")
    
    # Save test results
    with open(Path(args.output_dir) / 'test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)


if __name__ == "__main__":
    main()


