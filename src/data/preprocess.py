"""
Data preprocessing script for emotion classification dataset.
Handles cleaning, tokenization, and preparation for DistilBERT training.
"""

import pandas as pd
import numpy as np
import re
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import argparse
import os
import json
from pathlib import Path

# Initialize spaCy
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Please install spaCy English model: python -m spacy download en_core_web_sm")
    nlp = None

# Download NLTK data if needed
try:
    stop_words = set(stopwords.words('english'))
except LookupError:
    import nltk
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))


def clean_text(text):
    """Clean and normalize text."""
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def lemmatize_text(text, nlp_model):
    """Lemmatize text using spaCy."""
    if nlp_model is None:
        return text
    
    doc = nlp_model(text)
    lemmatized = [token.lemma_ for token in doc if not token.is_punct]
    return ' '.join(lemmatized)


def preprocess_dataset(input_path, output_dir, use_lemmatization=True, remove_stopwords=False):
    """
    Preprocess emotion dataset for training.
    
    Args:
        input_path: Path to input CSV file
        output_dir: Directory to save processed data
        use_lemmatization: Whether to lemmatize text
        remove_stopwords: Whether to remove stopwords
    """
    print(f"Loading dataset from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Expected columns: 'text' and 'emotion' or similar
    # Adjust based on actual dataset structure
    if 'text' not in df.columns:
        # Try common alternatives
        text_col = [col for col in df.columns if 'text' in col.lower() or 'sentence' in col.lower()][0]
        df.rename(columns={text_col: 'text'}, inplace=True)
    
    if 'emotion' not in df.columns:
        emotion_col = [col for col in df.columns if 'emotion' in col.lower() or 'label' in col.lower()][0]
        df.rename(columns={emotion_col: 'emotion'}, inplace=True)
    
    print(f"Original dataset size: {len(df)}")
    
    # Clean text
    print("Cleaning text...")
    df['cleaned_text'] = df['text'].apply(clean_text)
    
    # Remove empty texts
    df = df[df['cleaned_text'].str.len() > 0]
    
    # Lemmatization
    if use_lemmatization and nlp is not None:
        print("Lemmatizing text...")
        df['processed_text'] = df['cleaned_text'].apply(lambda x: lemmatize_text(x, nlp))
    else:
        df['processed_text'] = df['cleaned_text']
    
    # Remove stopwords if requested
    if remove_stopwords:
        print("Removing stopwords...")
        df['processed_text'] = df['processed_text'].apply(
            lambda x: ' '.join([word for word in word_tokenize(x) if word not in stop_words])
        )
    
    # Map emotions to standard labels
    emotion_mapping = {
        'joy': 'joy', 'happy': 'joy', 'happiness': 'joy',
        'sadness': 'sadness', 'sad': 'sadness',
        'anger': 'anger', 'angry': 'anger',
        'fear': 'fear', 'afraid': 'fear', 'anxious': 'fear',
        'disgust': 'disgust', 'disgusted': 'disgust',
        'surprise': 'surprise', 'surprised': 'surprise'
    }
    
    df['emotion'] = df['emotion'].str.lower().map(emotion_mapping).fillna(df['emotion'].str.lower())
    
    # Filter to only valid emotions
    valid_emotions = ['joy', 'sadness', 'anger', 'fear', 'disgust', 'surprise']
    df = df[df['emotion'].isin(valid_emotions)]
    
    print(f"Processed dataset size: {len(df)}")
    print(f"Emotion distribution:\n{df['emotion'].value_counts()}")
    
    # Split data
    print("Splitting data...")
    train_df, temp_df = train_test_split(df, test_size=0.2, stratify=df['emotion'], random_state=42)
    val_df, test_df = train_test_split(temp_df, test_size=0.5, stratify=temp_df['emotion'], random_state=42)
    
    # Save processed data
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    train_df.to_csv(output_dir / 'train.csv', index=False)
    val_df.to_csv(output_dir / 'val.csv', index=False)
    test_df.to_csv(output_dir / 'test.csv', index=False)
    
    # Save metadata
    metadata = {
        'total_samples': len(df),
        'train_samples': len(train_df),
        'val_samples': len(val_df),
        'test_samples': len(test_df),
        'emotions': valid_emotions,
        'emotion_counts': df['emotion'].value_counts().to_dict()
    }
    
    with open(output_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Processed data saved to {output_dir}")
    print(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    
    return train_df, val_df, test_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess emotion dataset")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file path")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--no-lemmatization", action="store_true", help="Skip lemmatization")
    parser.add_argument("--remove-stopwords", action="store_true", help="Remove stopwords")
    
    args = parser.parse_args()
    
    preprocess_dataset(
        args.input,
        args.output,
        use_lemmatization=not args.no_lemmatization,
        remove_stopwords=args.remove_stopwords
    )

