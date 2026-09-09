@echo off
REM Complete training pipeline script for Windows

echo === Mental Health Companion Training Pipeline ===

REM Step 1: Download data (if needed)
echo Step 1: Checking dataset...
if not exist "data\raw\emotion_dataset.csv" (
    echo Dataset not found. Downloading...
    python scripts\download_data.py --output data\raw\emotion_dataset.csv --create-sample
) else (
    echo Dataset found.
)

REM Step 2: Preprocess data
echo Step 2: Preprocessing data...
python src\data\preprocess.py --input data\raw\emotion_dataset.csv --output data\processed\

REM Step 3: Train model
echo Step 3: Training model...
python src\training\train.py --data_dir data\processed\ --output_dir models\ --epochs 5 --batch_size 32 --learning_rate 2e-5 --dropout 0.1 --weight_decay 0.01

echo === Training Pipeline Complete ===
echo Model saved to: models\

pause

