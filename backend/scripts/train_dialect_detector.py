#!/usr/bin/env python3
"""
Train Machine Learning Model for Egyptian Dialect Detection

This script trains a classifier to detect Egyptian Arabic dialects
using labeled training data for improved transcription routing.
"""

import os
import json
import argparse
from pathlib import Path
import logging
from typing import List, Tuple, Dict

from app.services.dialect_detection_service import EgyptianDialectDetector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_training_data(data_path: str) -> List[Tuple[str, str]]:
    """Load training data from various formats."""
    training_data = []

    data_path = Path(data_path)

    if data_path.is_file():
        if data_path.suffix == '.json':
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                # List of (text, dialect) pairs
                training_data = [(item['text'], item['dialect']) for item in data]
            elif isinstance(data, dict):
                # Dictionary with dialect keys
                for dialect, texts in data.items():
                    for text in texts:
                        training_data.append((text, dialect))

        elif data_path.suffix == '.csv':
            import pandas as pd
            df = pd.read_csv(data_path)
            training_data = list(zip(df['text'], df['dialect']))

    elif data_path.is_dir():
        # Directory with dialect subdirectories
        for dialect_dir in data_path.iterdir():
            if dialect_dir.is_dir():
                dialect = dialect_dir.name
                for text_file in dialect_dir.glob('*.txt'):
                    with open(text_file, 'r', encoding='utf-8') as f:
                        text = f.read().strip()
                        if text:
                            training_data.append((text, dialect))

    logger.info(f"Loaded {len(training_data)} training samples from {data_path}")
    return training_data

def create_sample_training_data() -> List[Tuple[str, str]]:
    """Create sample training data for demonstration."""
    return [
        # Cairo dialect samples
        ("أهلا يا جماعة إحنا هنتكلم عن المشروع ده", "cairo"),
        ("شوية فلوس ونقدر نعمل حاجة كويس", "cairo"),
        ("ده اللي احنا عايزينه بالظبط", "cairo"),
        ("تمام كده خلاص هنشوفكوا", "cairo"),

        # Alexandria dialect samples
        ("قوي أوي ده اللي احنا محتاجينه", "alexandria"),
        ("كده برضه كويس أما", "alexandria"),
        ("أنا مش فاهم إيه اللي بيحصل", "alexandria"),
        ("تمام يا جماعة خلاص", "alexandria"),

        # Upper Egypt dialect samples
        ("أهو ده اللي إحنا عايزينه", "upper_egypt"),
        ("كده كده تمام يا جماعة", "upper_egypt"),
        ("مش كده يا إحنا هنقولك", "upper_egypt"),
        ("يلا يا خلاص هنروح", "upper_egypt"),

        # Delta dialect samples
        ("أه يا ده اللي احنا محتاجينه", "delta"),
        ("كده يا تمام والحمد لله", "delta"),
        ("مش يا إحنا هنشوف", "delta"),
        ("يلا يا خلاص", "delta"),

        # Mixed Egyptian samples
        ("إحنا عايزين نتكلم عن الموضوع ده", "mixed_egyptian"),
        ("تمام خلاص هنعمل كده", "mixed_egyptian"),
        ("ده مش كويس أوي", "mixed_egyptian"),

        # Standard Arabic samples (for contrast)
        ("أنا أريد أن أتحدث عن هذا الموضوع", "standard_arabic"),
        ("هل يمكنني الحصول على معلومات إضافية", "standard_arabic"),
        ("أعتقد أن هذا سيكون مفيداً", "standard_arabic"),
        ("ما رأيك في هذا الاقتراح", "standard_arabic"),
    ]

def validate_training_data(training_data: List[Tuple[str, str]]) -> Dict[str, int]:
    """Validate and analyze training data distribution."""
    dialect_counts = {}
    total_samples = len(training_data)

    for text, dialect in training_data:
        dialect_counts[dialect] = dialect_counts.get(dialect, 0) + 1

        # Basic validation
        if not text or not isinstance(text, str):
            raise ValueError(f"Invalid text sample: {text}")
        if not dialect or not isinstance(dialect, str):
            raise ValueError(f"Invalid dialect label: {dialect}")

    logger.info("Training data validation passed")
    logger.info(f"Dialect distribution: {dialect_counts}")

    return dialect_counts

def main():
    parser = argparse.ArgumentParser(description="Train Egyptian dialect detection model")
    parser.add_argument('--training-data', help='Path to training data file/directory')
    parser.add_argument('--output-dir', required=True, help='Output directory for trained model')
    parser.add_argument('--use-sample-data', action='store_true',
                       help='Use built-in sample training data')
    parser.add_argument('--test-split', type=float, default=0.2,
                       help='Fraction of data to use for testing')

    args = parser.parse_args()

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load training data
    if args.use_sample_data:
        logger.info("Using sample training data")
        training_data = create_sample_training_data()
    elif args.training_data:
        training_data = load_training_data(args.training_data)
    else:
        raise ValueError("Must provide --training-data or use --use-sample-data")

    # Validate training data
    dialect_distribution = validate_training_data(training_data)

    # Initialize dialect detector
    detector = EgyptianDialectDetector()

    # Train the model
    logger.info("Starting model training...")
    training_results = detector.train_ml_model(
        training_data=training_data,
        save_path=str(output_path)
    )

    # Log results
    logger.info("Training completed successfully!")
    logger.info(f"Training accuracy: {training_results['train_accuracy']:.3f}")
    logger.info(f"Test accuracy: {training_results['test_accuracy']:.3f}")
    logger.info("Detailed classification report:")
    logger.info(training_results['classification_report'])

    # Test the trained model
    logger.info("Testing trained model...")
    test_texts = [
        "أهلا يا جماعة إحنا عايزين نتكلم",
        "أنا أريد أن أتحدث عن هذا الموضوع",
        "قوي أوي ده اللي احنا محتاجينه",
        "أهو ده اللي إحنا عايزينه",
    ]

    for text in test_texts:
        result = detector.detect_dialect(text, use_ml_model=True)
        logger.info(f"Text: '{text[:50]}...' -> Dialect: {result.primary_dialect} "
                   f"(confidence: {result.confidence_score:.3f})")

    # Save training metadata
    metadata = {
        'training_config': {
            'data_source': 'sample_data' if args.use_sample_data else args.training_data,
            'total_samples': len(training_data),
            'dialect_distribution': dialect_distribution,
            'test_split': args.test_split
        },
        'training_results': training_results,
        'model_path': str(output_path)
    }

    with open(output_path / 'training_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(f"Training complete! Model saved to {output_path}")
    logger.info(f"Metadata saved to {output_path / 'training_metadata.json'}")

if __name__ == '__main__':
    main()