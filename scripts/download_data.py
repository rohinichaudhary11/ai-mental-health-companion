"""
Script to download the DAIR-AI Emotion Dataset.
This is a helper script to acquire the training data.
"""

import requests
import pandas as pd
from pathlib import Path
import json
import argparse

# DAIR-AI Emotion Dataset URL (example - adjust based on actual source)
# Note: This is a placeholder. You'll need to update with the actual dataset URL
DATASET_URL = "https://github.com/dair-ai/emotion_dataset/raw/main/emotion.csv"


def download_dataset(output_path: str):
    """
    Download emotion dataset.
    
    Args:
        output_path: Path to save the dataset
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading dataset from {DATASET_URL}...")
    
    try:
        response = requests.get(DATASET_URL, stream=True)
        response.raise_for_status()
        
        # Save to file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Dataset downloaded to {output_path}")
        
        # Verify dataset
        df = pd.read_csv(output_path)
        print(f"Dataset shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        if 'emotion' in df.columns:
            print(f"\nEmotion distribution:")
            print(df['emotion'].value_counts())
        
        return True
    
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        print("\nAlternative: You can manually download the dataset from:")
        print("https://github.com/dair-ai/emotion_dataset")
        print(f"And place it at: {output_path}")
        return False


def create_sample_data(output_path: str):
    """
    Create a sample dataset for testing if download fails.
    
    Args:
        output_path: Path to save sample data
    """
    sample_data = {
        'text': [
            "I am feeling so happy today!",
            "This makes me really sad.",
            "I'm so angry about this situation.",
            "I feel anxious and scared.",
            "That's disgusting!",
            "Wow, I'm really surprised!",
            "I love spending time with my friends.",
            "I feel lonely and depressed.",
            "This is frustrating and annoying.",
            "I'm worried about the future."
        ],
        'emotion': [
            'joy', 'sadness', 'anger', 'fear', 'disgust',
            'surprise', 'joy', 'sadness', 'anger', 'fear'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Sample data created at {output_path}")
    print("Note: This is a small sample. For training, use the full DAIR-AI dataset.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download emotion dataset")
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/emotion_dataset.csv",
        help="Output path for dataset"
    )
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="Create sample data if download fails"
    )
    
    args = parser.parse_args()
    
    success = download_dataset(args.output)
    
    if not success and args.create_sample:
        print("\nCreating sample data...")
        create_sample_data(args.output)

