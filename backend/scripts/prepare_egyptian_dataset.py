#!/usr/bin/env python3
"""
Egyptian Arabic Dataset Preparation Script

This script prepares high-quality Egyptian Arabic datasets for fine-tuning Whisper models.
It includes data collection, preprocessing, validation, and formatting for Whisper fine-tuning.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import logging
from typing import List, Dict, Optional
import re
from datasets import Dataset, DatasetDict
import soundfile as sf
from pydub import AudioSegment
import librosa
import torch
from transformers import WhisperProcessor, WhisperTokenizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EgyptianDatasetPreparer:
    """Handles preparation of Egyptian Arabic datasets for Whisper fine-tuning."""

    def __init__(self, base_path: str = "data/egyptian_arabic"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Initialize Whisper processor and tokenizer
        self.processor = WhisperProcessor.from_pretrained("openai/whisper-large-v3")
        self.tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-large-v3")

        # Egyptian Arabic specific patterns
        self.egyptian_patterns = {
            'colloquial_phrases': [
                'أهلاً', 'إيه اللي', 'عايز', 'عامل إيه', 'تمام', 'كويس', 'أوي', 'بقى',
                'مش هقولك', 'يلا', 'خلاص', 'كده', 'ده', 'دي', 'إحنا', 'إنتوا',
                'أنا عايز', 'مش عارف', 'هقولك إيه', 'طب إحنا'
            ],
            'regional_variants': {
                'cairo': ['شوية', 'كتير', 'زي', 'أه'],
                'alexandria': ['قوي', 'كده برضه', 'أصل'],
                'upper_egypt': ['أهو', 'كده كده', 'تمام كده']
            }
        }

    def validate_audio_file(self, audio_path: str) -> Dict[str, any]:
        """Validate audio file quality and extract metadata."""
        try:
            # Load audio with librosa
            audio, sr = librosa.load(audio_path, sr=None)

            # Basic quality checks
            duration = len(audio) / sr
            rms = np.sqrt(np.mean(audio**2))
            peak = np.max(np.abs(audio))

            # Check for silence (more than 50% silence is suspicious)
            silence_threshold = 0.01
            silence_ratio = np.mean(np.abs(audio) < silence_threshold)

            quality_score = 1.0
            issues = []

            if duration < 1.0:
                quality_score *= 0.5
                issues.append("Too short")
            elif duration > 300:  # 5 minutes
                quality_score *= 0.8
                issues.append("Very long")

            if rms < 0.01:
                quality_score *= 0.3
                issues.append("Too quiet")
            elif rms > 0.8:
                quality_score *= 0.9
                issues.append("Too loud")

            if peak > 0.95:
                quality_score *= 0.8
                issues.append("Clipped")

            if silence_ratio > 0.5:
                quality_score *= 0.4
                issues.append("Mostly silent")

            return {
                'valid': quality_score > 0.6,
                'duration': duration,
                'sample_rate': sr,
                'rms': rms,
                'peak': peak,
                'silence_ratio': silence_ratio,
                'quality_score': quality_score,
                'issues': issues
            }

        except Exception as e:
            logger.error(f"Error validating audio {audio_path}: {e}")
            return {'valid': False, 'error': str(e)}

    def preprocess_transcript(self, text: str) -> str:
        """Clean and normalize Egyptian Arabic transcripts."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Normalize Arabic characters
        text = self._normalize_arabic(text)

        # Remove non-Arabic punctuation that might interfere
        text = re.sub(r'[^\u0600-\u06FF\s\.,!؟،؛]', '', text)

        # Fix common OCR/transcription errors in Egyptian Arabic
        text = self._fix_common_errors(text)

        return text.strip()

    def _normalize_arabic(self, text: str) -> str:
        """Normalize Arabic characters and remove diacritics."""
        # Remove diacritics (Tashkeel)
        text = re.sub(r'[\u064B-\u065F]', '', text)

        # Normalize different forms of characters
        normalizations = {
            'أ': 'ا', 'إ': 'ا', 'آ': 'ا',  # Different forms of Alif
            'ة': 'ه',  # Teh Marbuta
            'ى': 'ي',  # Alif Maqsura
        }

        for old, new in normalizations.items():
            text = text.replace(old, new)

        return text

    def _fix_common_errors(self, text: str) -> str:
        """Fix common transcription errors in Egyptian Arabic."""
        fixes = {
            'ايه': 'إيه',
            'اهلا': 'أهلاً',
            'عايز': 'عايز',
            'كده': 'كده',
            'كويس': 'كويس',
            'اوي': 'أوي',
            'بقي': 'بقى',
            'خلص': 'خلاص',
            'مش هقولك': 'مش هقولك',
        }

        for old, new in fixes.items():
            text = re.sub(r'\b' + re.escape(old) + r'\b', new, text)

        return text

    def detect_dialect_features(self, text: str) -> Dict[str, any]:
        """Detect Egyptian dialect-specific features in text."""
        features = {
            'has_egyptian_colloquial': False,
            'regional_markers': [],
            'confidence_score': 0.0
        }

        colloquial_count = 0
        total_words = len(text.split())

        # Check for colloquial phrases
        for phrase in self.egyptian_patterns['colloquial_phrases']:
            if phrase in text:
                colloquial_count += 1
                features['has_egyptian_colloquial'] = True

        # Check regional variants
        for region, markers in self.egyptian_patterns['regional_variants'].items():
            region_count = sum(1 for marker in markers if marker in text)
            if region_count > 0:
                features['regional_markers'].append({
                    'region': region,
                    'count': region_count
                })

        # Calculate confidence score
        if total_words > 0:
            colloquial_ratio = colloquial_count / total_words
            features['confidence_score'] = min(1.0, colloquial_ratio * 10)  # Scale up for visibility

        return features

    def create_dataset_from_files(self, audio_dir: str, transcript_file: str,
                                output_path: str) -> Dataset:
        """Create a HuggingFace dataset from audio files and transcripts."""
        audio_files = []
        transcripts = []

        # Load transcript data
        if transcript_file.endswith('.json'):
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
        elif transcript_file.endswith('.csv'):
            df = pd.read_csv(transcript_file)
            transcript_data = dict(zip(df['audio_file'], df['transcript']))
        else:
            raise ValueError("Unsupported transcript file format")

        valid_samples = []

        for audio_file, transcript in transcript_data.items():
            audio_path = Path(audio_dir) / audio_file

            if not audio_path.exists():
                logger.warning(f"Audio file not found: {audio_path}")
                continue

            # Validate audio
            audio_info = self.validate_audio_file(str(audio_path))
            if not audio_info['valid']:
                logger.warning(f"Invalid audio {audio_file}: {audio_info.get('issues', [])}")
                continue

            # Preprocess transcript
            clean_transcript = self.preprocess_transcript(transcript)

            # Detect dialect features
            dialect_info = self.detect_dialect_features(clean_transcript)

            sample = {
                'audio': str(audio_path),
                'transcript': clean_transcript,
                'duration': audio_info['duration'],
                'quality_score': audio_info['quality_score'],
                'dialect_features': dialect_info,
                'language': 'ar',
                'dialect': 'egyptian_arabic'
            }

            valid_samples.append(sample)

        # Create HuggingFace dataset
        dataset = Dataset.from_list(valid_samples)

        # Save dataset
        dataset.save_to_disk(output_path)

        logger.info(f"Created dataset with {len(valid_samples)} samples")
        return dataset

    def split_dataset(self, dataset: Dataset, train_ratio: float = 0.8,
                     val_ratio: float = 0.1) -> DatasetDict:
        """Split dataset into train/validation/test sets."""
        # Shuffle dataset
        dataset = dataset.shuffle(seed=42)

        # Calculate split sizes
        total_size = len(dataset)
        train_size = int(total_size * train_ratio)
        val_size = int(total_size * val_ratio)
        test_size = total_size - train_size - val_size

        # Split dataset
        train_dataset = dataset.select(range(train_size))
        val_dataset = dataset.select(range(train_size, train_size + val_size))
        test_dataset = dataset.select(range(train_size + val_size, total_size))

        return DatasetDict({
            'train': train_dataset,
            'validation': val_dataset,
            'test': test_dataset
        })

    def prepare_whisper_format(self, dataset: Dataset) -> Dataset:
        """Convert dataset to Whisper fine-tuning format."""
        def process_sample(sample):
            # Load and process audio
            audio_array, sr = librosa.load(sample['audio'], sr=16000)

            # Process with Whisper processor
            inputs = self.processor(
                audio_array,
                sampling_rate=sr,
                return_tensors="pt",
                padding=True
            )

            # Tokenize transcript
            labels = self.tokenizer(
                sample['transcript'],
                return_tensors="pt",
                padding=True
            )

            return {
                'input_features': inputs['input_features'].squeeze(),
                'labels': labels['input_ids'].squeeze(),
                'transcript': sample['transcript'],
                'duration': sample['duration'],
                'quality_score': sample['quality_score'],
                'dialect_features': sample['dialect_features']
            }

        # Process all samples
        processed_dataset = dataset.map(
            process_sample,
            remove_columns=dataset.column_names,
            num_proc=4  # Parallel processing
        )

        return processed_dataset

def main():
    parser = argparse.ArgumentParser(description="Prepare Egyptian Arabic dataset for Whisper fine-tuning")
    parser.add_argument('--audio-dir', required=True, help='Directory containing audio files')
    parser.add_argument('--transcript-file', required=True, help='Transcript file (JSON or CSV)')
    parser.add_argument('--output-dir', default='data/processed', help='Output directory')
    parser.add_argument('--train-ratio', type=float, default=0.8, help='Training data ratio')
    parser.add_argument('--val-ratio', type=float, default=0.1, help='Validation data ratio')

    args = parser.parse_args()

    # Initialize preparer
    preparer = EgyptianDatasetPreparer()

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Starting dataset preparation...")

    # Create raw dataset
    raw_dataset = preparer.create_dataset_from_files(
        args.audio_dir,
        args.transcript_file,
        str(output_path / 'raw_dataset')
    )

    # Split dataset
    split_datasets = preparer.split_dataset(raw_dataset, args.train_ratio, args.val_ratio)

    # Prepare for Whisper fine-tuning
    logger.info("Converting to Whisper format...")
    whisper_datasets = DatasetDict()

    for split_name, dataset in split_datasets.items():
        logger.info(f"Processing {split_name} split...")
        whisper_datasets[split_name] = preparer.prepare_whisper_format(dataset)

    # Save processed datasets
    final_output_path = output_path / 'whisper_finetune_dataset'
    whisper_datasets.save_to_disk(str(final_output_path))

    # Generate dataset statistics
    stats = {
        'total_samples': len(raw_dataset),
        'train_samples': len(split_datasets['train']),
        'val_samples': len(split_datasets['validation']),
        'test_samples': len(split_datasets['test']),
        'avg_duration': np.mean([s['duration'] for s in raw_dataset]),
        'avg_quality_score': np.mean([s['quality_score'] for s in raw_dataset]),
        'dialect_coverage': sum(1 for s in raw_dataset if s['dialect_features']['has_egyptian_colloquial'])
    }

    with open(output_path / 'dataset_stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    logger.info(f"Dataset preparation complete! Stats: {stats}")
    logger.info(f"Datasets saved to: {final_output_path}")

if __name__ == '__main__':
    main()