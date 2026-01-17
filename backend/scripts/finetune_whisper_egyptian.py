#!/usr/bin/env python3
"""
Egyptian Arabic Whisper Fine-tuning Script

This script fine-tunes OpenAI's Whisper model on Egyptian Arabic datasets
for improved accuracy on local dialects and colloquial speech patterns.
"""

import os
import json
import argparse
import logging
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from transformers import (
    WhisperForConditionalGeneration,
    WhisperProcessor,
    Trainer,
    TrainingArguments,
    EarlyStoppingCallback
)
from datasets import load_from_disk, load_dataset
import evaluate
from dataclasses import dataclass
from typing import Any, Dict, List, Union
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    """Data collator for Whisper fine-tuning."""
    processor: Any
    decoder_start_token_id: int

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        # split inputs and labels since they have to be of different lengths and need different padding methods
        model_input_name = self.processor.model_input_names[0]
        input_features = [{model_input_name: feature[model_input_name]} for feature in features]
        label_features = [{"input_ids": feature["labels"]} for feature in features]

        batch = self.processor.feature_extractor.pad(
            input_features,
            padding=True,
            return_tensors="pt",
        )

        labels_batch = self.processor.tokenizer.pad(
            label_features,
            padding=True,
            return_tensors="pt",
        )

        # replace padding with -100 to ignore loss correctly
        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)

        # if bos token is appended in previous tokenization step,
        # cut bos token here as it's append later anyways
        if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels

        return batch

class EgyptianWhisperFinetuner:
    """Handles fine-tuning of Whisper models for Egyptian Arabic."""

    def __init__(self, model_size: str = "large-v3", device: str = "auto"):
        self.model_size = model_size
        self.device = device if device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")

        # Model configuration
        self.model_name = f"openai/whisper-{model_size}"
        self.language = "ar"
        self.task = "transcribe"

        logger.info(f"Initializing fine-tuner with model: {self.model_name}, device: {self.device}")

    def load_model_and_processor(self):
        """Load Whisper model and processor."""
        logger.info("Loading model and processor...")

        self.processor = WhisperProcessor.from_pretrained(
            self.model_name,
            language=self.language,
            task=self.task
        )

        self.model = WhisperForConditionalGeneration.from_pretrained(
            self.model_name,
            device_map=self.device
        )

        # Set forced decoder ids for Arabic transcription
        self.model.config.forced_decoder_ids = self.processor.get_decoder_prompt_ids(
            language=self.language,
            task=self.task
        )

        # Set generation config
        self.model.generation_config.language = self.language
        self.model.generation_config.task = self.task

        # Enable gradient checkpointing to save memory
        self.model.gradient_checkpointing_enable()

    def load_dataset(self, dataset_path: str) -> Dict[str, any]:
        """Load processed dataset for fine-tuning."""
        logger.info(f"Loading dataset from {dataset_path}")

        if Path(dataset_path).exists():
            # Load from local disk
            dataset = load_from_disk(dataset_path)
        else:
            # Load from HuggingFace Hub
            dataset = load_dataset(dataset_path)

        logger.info(f"Dataset loaded: {dataset}")
        return dataset

    def prepare_data_collator(self):
        """Prepare data collator for training."""
        self.data_collator = DataCollatorSpeechSeq2SeqWithPadding(
            processor=self.processor,
            decoder_start_token_id=self.model.config.decoder_start_token_id,
        )

    def compute_metrics(self, pred):
        """Compute WER and CER metrics during evaluation."""
        pred_logits = pred.predictions
        pred_ids = np.argmax(pred_logits, axis=-1)

        pred.label_ids[pred.label_ids == -100] = self.processor.tokenizer.pad_token_id

        pred_str = self.processor.batch_decode(pred_ids)
        # we do not want to group tokens when computing the metrics
        label_str = self.processor.batch_decode(pred.label_ids, skip_special_tokens=True)

        # Load metrics
        wer_metric = evaluate.load("wer")
        cer_metric = evaluate.load("cer")

        wer = wer_metric.compute(predictions=pred_str, references=label_str)
        cer = cer_metric.compute(predictions=pred_str, references=label_str)

        return {"wer": wer, "cer": cer}

    def create_training_args(self, output_dir: str, num_epochs: int = 5,
                           batch_size: int = 8, learning_rate: float = 1e-5,
                           gradient_accumulation_steps: int = 2):
        """Create training arguments."""
        return TrainingArguments(
            output_dir=output_dir,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=500,
            max_steps=-1,  # Use num_train_epochs instead
            num_train_epochs=num_epochs,
            gradient_checkpointing=True,
            fp16=True,  # Use mixed precision
            evaluation_strategy="steps",
            per_device_eval_batch_size=batch_size,
            save_steps=500,
            eval_steps=500,
            logging_steps=100,
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="wer",
            greater_is_better=False,
            dataloader_pin_memory=False,
            remove_unused_columns=False,
            label_names=["labels"],
            push_to_hub=False,
            report_to="none",  # Disable wandb/tensorboard
        )

    def train(self, train_dataset, eval_dataset, output_dir: str,
             num_epochs: int = 5, batch_size: int = 8):
        """Run the fine-tuning training."""
        logger.info("Starting fine-tuning...")

        # Prepare data collator
        self.prepare_data_collator()

        # Create training arguments
        training_args = self.create_training_args(
            output_dir=output_dir,
            num_epochs=num_epochs,
            batch_size=batch_size
        )

        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=self.data_collator,
            compute_metrics=self.compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
        )

        # Start training
        trainer.train()

        # Save the final model
        final_model_path = Path(output_dir) / "final_model"
        trainer.save_model(str(final_model_path))
        self.processor.save_pretrained(str(final_model_path))

        logger.info(f"Model saved to {final_model_path}")
        return trainer

    def evaluate_model(self, test_dataset, model_path: str = None):
        """Evaluate the fine-tuned model on test data."""
        logger.info("Evaluating model...")

        if model_path:
            # Load fine-tuned model
            model = WhisperForConditionalGeneration.from_pretrained(model_path)
            processor = WhisperProcessor.from_pretrained(model_path)
        else:
            # Use current model
            model = self.model
            processor = self.processor

        # Create trainer for evaluation
        trainer = Trainer(
            model=model,
            data_collator=self.data_collator,
            compute_metrics=self.compute_metrics,
        )

        # Run evaluation
        results = trainer.evaluate(test_dataset)

        logger.info(f"Evaluation results: {results}")
        return results

    def benchmark_egyptian_dialects(self, test_dataset, model_path: str = None):
        """Benchmark performance on different Egyptian dialect features."""
        logger.info("Benchmarking Egyptian dialect performance...")

        if model_path:
            model = WhisperForConditionalGeneration.from_pretrained(model_path)
            processor = WhisperProcessor.from_pretrained(model_path)
        else:
            model = self.model
            processor = self.processor

        dialect_results = {
            'cairo_colloquial': {'samples': 0, 'wer': 0, 'cer': 0},
            'alexandria_colloquial': {'samples': 0, 'wer': 0, 'cer': 0},
            'upper_egypt_colloquial': {'samples': 0, 'wer': 0, 'cer': 0},
            'mixed_dialect': {'samples': 0, 'wer': 0, 'cer': 0},
            'standard_arabic': {'samples': 0, 'wer': 0, 'cer': 0}
        }

        def classify_sample(sample):
            features = sample.get('dialect_features', {})
            if not features.get('has_egyptian_colloquial', False):
                return 'standard_arabic'

            regional_markers = features.get('regional_markers', [])
            if regional_markers:
                # Take the most prominent region
                region = max(regional_markers, key=lambda x: x['count'])['region']
                return f"{region}_colloquial"
            else:
                return 'mixed_dialect'

        # Process test samples
        model.eval()
        device = next(model.parameters()).device

        for sample in test_dataset:
            dialect_type = classify_sample(sample)

            # Prepare input
            input_features = torch.tensor(sample['input_features']).unsqueeze(0).to(device)

            # Generate prediction
            with torch.no_grad():
                generated_ids = model.generate(
                    input_features,
                    forced_decoder_ids=processor.get_decoder_prompt_ids(language="ar", task="transcribe"),
                    max_length=448,
                    num_beams=5
                )

            # Decode prediction and reference
            pred_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            ref_text = sample['transcript']

            # Calculate metrics
            wer_metric = evaluate.load("wer")
            cer_metric = evaluate.load("cer")

            wer = wer_metric.compute(predictions=[pred_text], references=[ref_text])
            cer = cer_metric.compute(predictions=[pred_text], references=[ref_text])

            # Accumulate results
            dialect_results[dialect_type]['samples'] += 1
            dialect_results[dialect_type]['wer'] += wer
            dialect_results[dialect_type]['cer'] += cer

        # Calculate averages
        for dialect_type, results in dialect_results.items():
            if results['samples'] > 0:
                results['wer'] /= results['samples']
                results['cer'] /= results['samples']

        logger.info(f"Dialect benchmarking results: {dialect_results}")
        return dialect_results

def main():
    parser = argparse.ArgumentParser(description="Fine-tune Whisper for Egyptian Arabic")
    parser.add_argument('--dataset-path', required=True, help='Path to processed dataset')
    parser.add_argument('--output-dir', required=True, help='Output directory for model')
    parser.add_argument('--model-size', default='large-v3', choices=['base', 'small', 'medium', 'large-v3'],
                       help='Whisper model size')
    parser.add_argument('--num-epochs', type=int, default=5, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=8, help='Batch size')
    parser.add_argument('--learning-rate', type=float, default=1e-5, help='Learning rate')
    parser.add_argument('--device', default='auto', help='Device to use (auto/cuda/cpu)')

    args = parser.parse_args()

    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize fine-tuner
    finetuner = EgyptianWhisperFinetuner(args.model_size, args.device)

    # Load model and processor
    finetuner.load_model_and_processor()

    # Load dataset
    dataset = finetuner.load_dataset(args.dataset_path)

    # Train model
    trainer = finetuner.train(
        train_dataset=dataset['train'],
        eval_dataset=dataset['validation'],
        output_dir=str(output_path / "checkpoints"),
        num_epochs=args.num_epochs,
        batch_size=args.batch_size
    )

    # Evaluate on test set
    test_results = finetuner.evaluate_model(dataset['test'])
    logger.info(f"Test results: {test_results}")

    # Benchmark dialect performance
    dialect_results = finetuner.benchmark_egyptian_dialects(dataset['test'])
    logger.info(f"Dialect benchmark: {dialect_results}")

    # Save results
    results = {
        'test_metrics': test_results,
        'dialect_benchmark': dialect_results,
        'training_config': {
            'model_size': args.model_size,
            'epochs': args.num_epochs,
            'batch_size': args.batch_size,
            'learning_rate': args.learning_rate,
            'device': args.device
        }
    }

    with open(output_path / 'finetuning_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    logger.info("Fine-tuning complete!")
    logger.info(f"Results saved to {output_path / 'finetuning_results.json'}")

if __name__ == '__main__':
    main()