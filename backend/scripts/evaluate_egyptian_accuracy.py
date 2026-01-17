#!/usr/bin/env python3
"""
Egyptian Arabic Transcription Accuracy Evaluation

This script evaluates the accuracy improvements achieved by fine-tuning
Whisper models on Egyptian Arabic dialects compared to base models.
"""

import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import asyncio
import time

import torch
import librosa
import evaluate
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from faster_whisper import WhisperModel

from app.services.transcription_service import transcription_service
from app.services.dialect_detection_service import EgyptianDialectDetector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EgyptianAccuracyEvaluator:
    """Evaluates transcription accuracy for Egyptian Arabic content."""

    def __init__(self, base_model_size: str = "large-v3"):
        self.base_model_size = base_model_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Initialize metrics
        self.wer_metric = evaluate.load("wer")
        self.cer_metric = evaluate.load("cer")

        # Initialize dialect detector
        self.dialect_detector = EgyptianDialectDetector()

    async def load_models(self):
        """Load base and fine-tuned models for comparison."""
        logger.info("Loading models for evaluation...")

        # Load base Faster-Whisper model
        self.base_model = WhisperModel(
            self.base_model_size,
            device=self.device,
            compute_type="float16" if self.device == "cuda" else "int8"
        )

        # Load fine-tuned models
        self.finetuned_models = {}
        model_configs = {
            'cairo': 'models/egyptian/cairo/final_model',
            'alexandria': 'models/egyptian/alexandria/final_model',
            'upper_egypt': 'models/egyptian/upper_egypt/final_model',
            'mixed': 'models/egyptian/mixed/final_model'
        }

        for dialect, path in model_configs.items():
            if os.path.exists(path):
                try:
                    processor = WhisperProcessor.from_pretrained(path)
                    model = WhisperForConditionalGeneration.from_pretrained(path)
                    model = model.to(self.device)
                    self.finetuned_models[dialect] = {
                        'processor': processor,
                        'model': model
                    }
                    logger.info(f"Loaded fine-tuned model for {dialect}")
                except Exception as e:
                    logger.warning(f"Failed to load {dialect} model: {e}")
            else:
                logger.warning(f"Fine-tuned model not found: {path}")

    def load_evaluation_dataset(self, dataset_path: str) -> List[Dict]:
        """Load evaluation dataset with audio and reference transcripts."""
        dataset = []

        if os.path.isfile(dataset_path):
            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for item in data:
                audio_path = item.get('audio_path') or item.get('audio')
                if audio_path and os.path.exists(audio_path):
                    dataset.append({
                        'audio_path': audio_path,
                        'reference_text': item['transcript'],
                        'dialect': item.get('dialect', 'mixed_egyptian'),
                        'speaker_info': item.get('speaker_info', {})
                    })

        elif os.path.isdir(dataset_path):
            # Assume directory structure: dialect/audio_files.json
            for dialect_dir in Path(dataset_path).iterdir():
                if dialect_dir.is_dir():
                    dialect = dialect_dir.name
                    json_file = dialect_dir / 'evaluation_data.json'
                    if json_file.exists():
                        with open(json_file, 'r', encoding='utf-8') as f:
                            dialect_data = json.load(f)
                            for item in dialect_data:
                                item['dialect'] = dialect
                                dataset.append(item)

        logger.info(f"Loaded {len(dataset)} evaluation samples")
        return dataset

    async def transcribe_with_base_model(self, audio_path: str) -> str:
        """Transcribe using base Faster-Whisper model."""
        segments, _ = self.base_model.transcribe(
            audio_path,
            language="ar",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        transcript = " ".join(segment.text.strip() for segment in segments)
        return transcript

    async def transcribe_with_finetuned_model(self, audio_path: str, dialect: str) -> Optional[str]:
        """Transcribe using fine-tuned model for specific dialect."""
        if dialect not in self.finetuned_models:
            return None

        model_info = self.finetuned_models[dialect]
        processor = model_info['processor']
        model = model_info['model']

        try:
            # Load and process audio
            audio_input, _ = librosa.load(audio_path, sr=16000)

            inputs = processor(
                audio_input,
                sampling_rate=16000,
                return_tensors="pt",
                return_attention_mask=True
            ).to(self.device)

            # Generate transcription
            with torch.no_grad():
                generated_ids = model.generate(
                    inputs.input_features,
                    attention_mask=inputs.attention_mask,
                    forced_decoder_ids=processor.get_decoder_prompt_ids(language="ar", task="transcribe"),
                    max_length=448,
                    num_beams=5,
                    early_stopping=True,
                )

            transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return transcription

        except Exception as e:
            logger.error(f"Fine-tuned transcription failed for {dialect}: {e}")
            return None

    def calculate_metrics(self, hypothesis: str, reference: str) -> Dict[str, float]:
        """Calculate WER and CER metrics."""
        try:
            wer = self.wer_metric.compute(predictions=[hypothesis], references=[reference])
            cer = self.cer_metric.compute(predictions=[hypothesis], references=[reference])

            return {
                'wer': wer,
                'cer': cer,
                'reference_length': len(reference.split()),
                'hypothesis_length': len(hypothesis.split())
            }
        except Exception as e:
            logger.error(f"Metrics calculation failed: {e}")
            return {'wer': 1.0, 'cer': 1.0, 'error': str(e)}

    async def evaluate_sample(self, sample: Dict) -> Dict:
        """Evaluate a single sample across all models."""
        audio_path = sample['audio_path']
        reference_text = sample['reference_text']
        dialect = sample['dialect']

        results = {
            'sample_info': {
                'audio_path': audio_path,
                'reference_text': reference_text,
                'dialect': dialect
            },
            'models': {}
        }

        # Transcribe with base model
        logger.info(f"Evaluating base model on {os.path.basename(audio_path)}")
        start_time = time.time()
        base_transcript = await self.transcribe_with_base_model(audio_path)
        base_time = time.time() - start_time

        base_metrics = self.calculate_metrics(base_transcript, reference_text)
        results['models']['base_whisper'] = {
            'transcript': base_transcript,
            'metrics': base_metrics,
            'processing_time': base_time
        }

        # Transcribe with fine-tuned model for this dialect
        finetuned_transcript = await self.transcribe_with_finetuned_model(audio_path, dialect)
        if finetuned_transcript:
            logger.info(f"Evaluating fine-tuned model for {dialect}")
            start_time = time.time()
            # Time is already measured in transcribe_with_finetuned_model
            finetuned_time = time.time() - start_time

            finetuned_metrics = self.calculate_metrics(finetuned_transcript, reference_text)
            results['models'][f'finetuned_{dialect}'] = {
                'transcript': finetuned_transcript,
                'metrics': finetuned_metrics,
                'processing_time': finetuned_time
            }

            # Calculate improvements
            wer_improvement = base_metrics['wer'] - finetuned_metrics['wer']
            cer_improvement = base_metrics['cer'] - finetuned_metrics['cer']

            results['improvements'] = {
                'wer_improvement': wer_improvement,
                'cer_improvement': cer_improvement,
                'relative_wer_improvement': wer_improvement / base_metrics['wer'] if base_metrics['wer'] > 0 else 0,
                'relative_cer_improvement': cer_improvement / base_metrics['cer'] if base_metrics['cer'] > 0 else 0
            }

        return results

    async def run_evaluation(self, dataset: List[Dict], output_path: str):
        """Run full evaluation on the dataset."""
        logger.info(f"Starting evaluation of {len(dataset)} samples")

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        all_results = []
        dialect_summaries = {}

        # Evaluate each sample
        for i, sample in enumerate(dataset):
            logger.info(f"Evaluating sample {i+1}/{len(dataset)}")
            try:
                result = await self.evaluate_sample(sample)
                all_results.append(result)

                # Update dialect summary
                dialect = sample['dialect']
                if dialect not in dialect_summaries:
                    dialect_summaries[dialect] = {
                        'samples': 0,
                        'base_wer': [],
                        'finetuned_wer': [],
                        'improvements': []
                    }

                summary = dialect_summaries[dialect]
                summary['samples'] += 1

                if 'base_whisper' in result['models']:
                    summary['base_wer'].append(result['models']['base_whisper']['metrics']['wer'])

                finetuned_key = f'finetuned_{dialect}'
                if finetuned_key in result['models']:
                    summary['finetuned_wer'].append(result['models'][finetuned_key]['metrics']['wer'])
                    if 'improvements' in result:
                        summary['improvements'].append(result['improvements']['wer_improvement'])

            except Exception as e:
                logger.error(f"Failed to evaluate sample {i+1}: {e}")
                continue

        # Calculate dialect-level summaries
        for dialect, summary in dialect_summaries.items():
            if summary['base_wer']:
                summary['avg_base_wer'] = sum(summary['base_wer']) / len(summary['base_wer'])
            if summary['finetuned_wer']:
                summary['avg_finetuned_wer'] = sum(summary['finetuned_wer']) / len(summary['finetuned_wer'])
            if summary['improvements']:
                summary['avg_improvement'] = sum(summary['improvements']) / len(summary['improvements'])
                summary['improvement_percentage'] = (summary['avg_improvement'] / summary['avg_base_wer']) * 100 if summary['avg_base_wer'] > 0 else 0

        # Overall summary
        overall_summary = {
            'total_samples': len(all_results),
            'dialect_breakdown': dialect_summaries,
            'average_improvements': {
                'wer_improvement': sum(r.get('improvements', {}).get('wer_improvement', 0) for r in all_results) / len(all_results),
                'cer_improvement': sum(r.get('improvements', {}).get('cer_improvement', 0) for r in all_results) / len(all_results)
            }
        }

        # Save detailed results
        with open(output_path / 'detailed_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        # Save summary
        with open(output_path / 'evaluation_summary.json', 'w', encoding='utf-8') as f:
            json.dump(overall_summary, f, indent=2, ensure_ascii=False)

        # Print summary to console
        logger.info("="*60)
        logger.info("EGYPTIAN ARABIC ACCURACY EVALUATION RESULTS")
        logger.info("="*60)
        logger.info(f"Total samples evaluated: {overall_summary['total_samples']}")
        logger.info(".2f")
        logger.info(".2f")

        for dialect, summary in overall_summary['dialect_breakdown'].items():
            logger.info(f"\n{dialect.upper()} DIALECT:")
            logger.info(f"  Samples: {summary['samples']}")
            if 'avg_base_wer' in summary:
                logger.info(".3f")
            if 'avg_finetuned_wer' in summary:
                logger.info(".3f")
            if 'improvement_percentage' in summary:
                logger.info(".1f")

        logger.info("="*60)
        logger.info(f"Results saved to {output_path}")

        return overall_summary

def create_sample_evaluation_data(output_dir: str):
    """Create sample evaluation data for testing."""
    sample_data = [
        {
            "audio_path": "sample_audio/cairo_sample.wav",  # You'll need to provide actual audio
            "transcript": "أهلاً يا جماعة إحنا هنتكلم عن المشروع ده اللي احنا عايزينه",
            "dialect": "cairo"
        },
        {
            "audio_path": "sample_audio/alexandria_sample.wav",
            "transcript": "قوي أوي ده اللي احنا محتاجينه كده برضه",
            "dialect": "alexandria"
        },
        {
            "audio_path": "sample_audio/upper_egypt_sample.wav",
            "transcript": "أهو ده اللي إحنا عايزينه كده كده تمام",
            "dialect": "upper_egypt"
        }
    ]

    output_path = Path(output_dir) / "sample_evaluation_data.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Sample evaluation data created at {output_path}")
    return str(output_path)

async def main():
    parser = argparse.ArgumentParser(description="Evaluate Egyptian Arabic transcription accuracy")
    parser.add_argument('--dataset', help='Path to evaluation dataset')
    parser.add_argument('--output-dir', required=True, help='Output directory for results')
    parser.add_argument('--create-sample-data', action='store_true',
                       help='Create sample evaluation data')
    parser.add_argument('--base-model', default='large-v3',
                       choices=['base', 'small', 'medium', 'large-v3'],
                       help='Base Whisper model size')

    args = parser.parse_args()

    # Create sample data if requested
    if args.create_sample_data:
        dataset_path = create_sample_evaluation_data(args.output_dir)
    elif args.dataset:
        dataset_path = args.dataset
    else:
        raise ValueError("Must provide --dataset or use --create-sample-data")

    # Initialize evaluator
    evaluator = EgyptianAccuracyEvaluator(args.base_model)

    # Load models
    await evaluator.load_models()

    # Load evaluation dataset
    dataset = evaluator.load_evaluation_dataset(dataset_path)

    if not dataset:
        logger.error("No valid evaluation samples found")
        return

    # Run evaluation
    results = await evaluator.run_evaluation(dataset, args.output_dir)

    logger.info("Evaluation completed successfully!")

if __name__ == '__main__':
    asyncio.run(main())