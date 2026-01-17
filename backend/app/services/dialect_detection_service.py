"""
Egyptian Arabic Dialect Detection Service

This service provides dialect detection capabilities for Egyptian Arabic,
including region identification, colloquial pattern recognition, and
model routing for optimal transcription accuracy.
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class DialectFeatures:
    """Features extracted for dialect classification."""
    has_colloquial_markers: bool
    regional_markers_count: Dict[str, int]
    formality_score: float
    vocabulary_richness: float
    dialect_confidence: float
    predicted_dialect: str

@dataclass
class DialectDetectionResult:
    """Result of dialect detection analysis."""
    primary_dialect: str
    confidence_score: float
    regional_features: Dict[str, float]
    recommended_model: str
    preprocessing_hints: List[str]

class EgyptianDialectDetector:
    """Detects and classifies Egyptian Arabic dialects."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = Path(model_path) if model_path else None
        self.classifier = None
        self.vectorizer = None
        self.is_trained = False

        # Egyptian dialect patterns and markers
        self.dialect_patterns = {
            'cairo': {
                'markers': [
                    'أه', 'شوية', 'كتير', 'زي', 'ده', 'دي', 'كده', 'بقى',
                    'أوي', 'تمام', 'كويس', 'عامل إيه', 'إيه اللي', 'مش هقولك',
                    'يلا', 'خلاص', 'إحنا', 'إنتوا', 'أنا عايز', 'مش عارف'
                ],
                'weight': 1.0
            },
            'alexandria': {
                'markers': [
                    'قوي', 'كده برضه', 'أصل', 'أنا مش', 'إحنا كده', 'تمام كده',
                    'كويس أوي', 'مش كده', 'أه برضه', 'إيه ده'
                ],
                'weight': 0.9
            },
            'upper_egypt': {
                'markers': [
                    'أهو', 'كده كده', 'تمام كده', 'أوي كده', 'إحنا هنا',
                    'مش كده', 'أنا هقولك', 'يلا يا', 'خلاص يا'
                ],
                'weight': 0.8
            },
            'delta': {
                'markers': [
                    'أه يا', 'كده يا', 'تمام يا', 'إحنا يا', 'مش يا',
                    'أنا يا', 'إيه يا', 'يلا يا', 'خلاص يا'
                ],
                'weight': 0.7
            },
            'mixed_egyptian': {
                'markers': [],  # General Egyptian without specific regional markers
                'weight': 0.6
            },
            'standard_arabic': {
                'markers': [
                    'أنا أريد', 'ماذا تفعل', 'كيف حالك', 'لا أعرف',
                    'أين أنت', 'ما الذي', 'هل تود', 'أعتقد أن'
                ],
                'weight': 0.3
            }
        }

        # Load pre-trained model if available
        if self.model_path and self.model_path.exists():
            self.load_model()

    def extract_features(self, text: str) -> DialectFeatures:
        """Extract dialect features from text."""
        # Normalize text
        text = self._normalize_text(text)
        words = text.split()

        # Count regional markers
        regional_markers = {}
        total_markers = 0

        for dialect, patterns in self.dialect_patterns.items():
            if dialect == 'mixed_egyptian':
                continue

            count = sum(1 for marker in patterns['markers'] if marker in text)
            regional_markers[dialect] = count
            total_markers += count

        # Calculate features
        has_colloquial = total_markers > 0

        # Formality score (inverse of colloquial markers density)
        formality_score = 1.0 - min(1.0, total_markers / max(1, len(words)))

        # Vocabulary richness (unique words ratio)
        unique_words = len(set(words))
        vocabulary_richness = unique_words / max(1, len(words))

        # Determine primary dialect
        if total_markers == 0:
            predicted_dialect = 'standard_arabic'
            confidence = formality_score
        else:
            # Find dialect with most markers
            primary_dialect = max(regional_markers.keys(), key=lambda x: regional_markers[x])
            max_markers = regional_markers[primary_dialect]

            if max_markers > 0:
                confidence = min(1.0, max_markers / total_markers)
                predicted_dialect = primary_dialect
            else:
                predicted_dialect = 'mixed_egyptian'
                confidence = 0.5

        return DialectFeatures(
            has_colloquial_markers=has_colloquial,
            regional_markers_count=regional_markers,
            formality_score=formality_score,
            vocabulary_richness=vocabulary_richness,
            dialect_confidence=confidence,
            predicted_dialect=predicted_dialect
        )

    def detect_dialect(self, text: str, use_ml_model: bool = True) -> DialectDetectionResult:
        """Detect dialect from text input."""
        features = self.extract_features(text)

        # Use ML model if available and requested
        if use_ml_model and self.is_trained:
            ml_prediction = self._predict_with_ml(text)
            if ml_prediction['confidence'] > features.dialect_confidence:
                features.predicted_dialect = ml_prediction['dialect']
                features.dialect_confidence = ml_prediction['confidence']

        # Calculate regional feature scores
        regional_features = {}
        total_markers = sum(features.regional_markers_count.values())

        for dialect, count in features.regional_markers_count.items():
            if total_markers > 0:
                regional_features[dialect] = count / total_markers
            else:
                regional_features[dialect] = 0.0

        # Determine recommended model
        recommended_model = self._get_recommended_model(features.predicted_dialect, features.dialect_confidence)

        # Generate preprocessing hints
        preprocessing_hints = self._generate_preprocessing_hints(features)

        return DialectDetectionResult(
            primary_dialect=features.predicted_dialect,
            confidence_score=features.dialect_confidence,
            regional_features=regional_features,
            recommended_model=recommended_model,
            preprocessing_hints=preprocessing_hints
        )

    def _predict_with_ml(self, text: str) -> Dict[str, any]:
        """Predict dialect using trained ML model."""
        if not self.is_trained:
            return {'dialect': 'unknown', 'confidence': 0.0}

        try:
            # Vectorize text
            text_vector = self.vectorizer.transform([text])

            # Get prediction and probabilities
            prediction = self.classifier.predict(text_vector)[0]
            probabilities = self.classifier.predict_proba(text_vector)[0]

            confidence = max(probabilities)

            return {
                'dialect': prediction,
                'confidence': confidence
            }
        except Exception as e:
            logger.warning(f"ML prediction failed: {e}")
            return {'dialect': 'unknown', 'confidence': 0.0}

    def _get_recommended_model(self, dialect: str, confidence: float) -> str:
        """Get recommended Whisper model based on dialect."""
        model_recommendations = {
            'cairo': 'egyptian_cairo_finetuned',
            'alexandria': 'egyptian_alexandria_finetuned',
            'upper_egypt': 'egyptian_upper_egypt_finetuned',
            'delta': 'egyptian_delta_finetuned',
            'mixed_egyptian': 'egyptian_mixed_finetuned',
            'standard_arabic': 'whisper_large_v3'
        }

        # Use fine-tuned model if confidence is high enough
        if confidence > 0.6:
            return model_recommendations.get(dialect, 'whisper_large_v3')
        else:
            # Fall back to base Egyptian model or standard Whisper
            return 'egyptian_mixed_finetuned' if dialect in ['cairo', 'alexandria', 'upper_egypt', 'delta', 'mixed_egyptian'] else 'whisper_large_v3'

    def _generate_preprocessing_hints(self, features: DialectFeatures) -> List[str]:
        """Generate preprocessing hints based on dialect features."""
        hints = []

        if features.has_colloquial_markers:
            hints.append("egyptian_colloquial_patterns")
        else:
            hints.append("standard_arabic_formality")

        if features.predicted_dialect == 'cairo':
            hints.extend(["cairo_slang_normalization", "local_pronunciation_adjustment"])
        elif features.predicted_dialect == 'alexandria':
            hints.extend(["alexandria_coastal_dialect", "rapid_speech_patterns"])
        elif features.predicted_dialect == 'upper_egypt':
            hints.extend(["upper_egypt_rural_patterns", "traditional_pronunciation"])
        elif features.predicted_dialect == 'delta':
            hints.extend(["delta_regional_variants", "mixed_influences"])

        if features.vocabulary_richness < 0.3:
            hints.append("limited_vocabulary_compensation")
        elif features.vocabulary_richness > 0.8:
            hints.append("rich_vocabulary_preservation")

        return hints

    def _normalize_text(self, text: str) -> str:
        """Normalize Arabic text for processing."""
        # Remove diacritics
        text = re.sub(r'[\u064B-\u065F]', '', text)

        # Normalize different forms of characters
        normalizations = {
            'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
            'ة': 'ه', 'ى': 'ي'
        }

        for old, new in normalizations.items():
            text = text.replace(old, new)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        return text.lower()

    def train_ml_model(self, training_data: List[Tuple[str, str]],
                      save_path: Optional[str] = None):
        """Train ML model for dialect classification."""
        logger.info("Training ML model for dialect detection...")

        texts, labels = zip(*training_data)

        # Create vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            analyzer='char'  # Character-level features work better for Arabic
        )

        # Transform texts
        X = self.vectorizer.fit_transform(texts)
        y = np.array(labels)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train classifier
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight='balanced'
        )

        self.classifier.fit(X_train, y_train)

        # Evaluate
        train_score = self.classifier.score(X_train, y_train)
        test_score = self.classifier.score(X_test, y_test)

        logger.info(f"Training accuracy: {train_score:.3f}")
        logger.info(f"Test accuracy: {test_score:.3f}")

        # Detailed classification report
        y_pred = self.classifier.predict(X_test)
        report = classification_report(y_test, y_pred)
        logger.info(f"Classification report:\n{report}")

        self.is_trained = True

        # Save model if path provided
        if save_path:
            self.save_model(save_path)

        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'classification_report': report
        }

    def save_model(self, path: str):
        """Save trained model and vectorizer."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        if self.classifier and self.vectorizer:
            joblib.dump(self.classifier, path / 'dialect_classifier.joblib')
            joblib.dump(self.vectorizer, path / 'dialect_vectorizer.joblib')

            # Save metadata
            metadata = {
                'dialects': list(self.dialect_patterns.keys()),
                'trained': True
            }

            with open(path / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"Model saved to {path}")
        else:
            logger.warning("No trained model to save")

    def load_model(self, path: Optional[str] = None):
        """Load trained model and vectorizer."""
        path = Path(path or self.model_path)

        try:
            self.classifier = joblib.load(path / 'dialect_classifier.joblib')
            self.vectorizer = joblib.load(path / 'dialect_vectorizer.joblib')

            with open(path / 'metadata.json', 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            self.is_trained = metadata.get('trained', False)
            logger.info(f"Model loaded from {path}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.is_trained = False

class DialectAdaptiveTranscriptionService:
    """Service that adapts transcription based on detected dialect."""

    def __init__(self, detector: EgyptianDialectDetector):
        self.detector = detector

        # Model configurations for different dialects
        self.model_configs = {
            'egyptian_cairo_finetuned': {
                'model_path': 'models/egyptian/cairo',
                'language_code': 'ar-EG-cairo',
                'boost_colloquial': True
            },
            'egyptian_alexandria_finetuned': {
                'model_path': 'models/egyptian/alexandria',
                'language_code': 'ar-EG-alexandria',
                'boost_colloquial': True
            },
            'egyptian_upper_egypt_finetuned': {
                'model_path': 'models/egyptian/upper_egypt',
                'language_code': 'ar-EG-upper',
                'boost_colloquial': True
            },
            'egyptian_mixed_finetuned': {
                'model_path': 'models/egyptian/mixed',
                'language_code': 'ar-EG',
                'boost_colloquial': True
            },
            'whisper_large_v3': {
                'model_path': 'openai/whisper-large-v3',
                'language_code': 'ar',
                'boost_colloquial': False
            }
        }

    def get_adaptive_config(self, text_sample: str) -> Dict[str, any]:
        """Get adaptive transcription configuration based on dialect detection."""
        detection_result = self.detector.detect_dialect(text_sample)

        model_config = self.model_configs.get(
            detection_result.recommended_model,
            self.model_configs['whisper_large_v3']
        )

        return {
            'model_name': detection_result.recommended_model,
            'model_config': model_config,
            'dialect_info': {
                'primary_dialect': detection_result.primary_dialect,
                'confidence': detection_result.confidence_score,
                'regional_features': detection_result.regional_features
            },
            'preprocessing_hints': detection_result.preprocessing_hints,
            'boost_colloquial': model_config['boost_colloquial'],
            'expected_improvement': self._estimate_improvement(detection_result)
        }

    def _estimate_improvement(self, detection_result: DialectDetectionResult) -> float:
        """Estimate expected WER improvement with dialect-specific model."""
        base_improvements = {
            'cairo': 0.25,  # 25% WER reduction
            'alexandria': 0.20,
            'upper_egypt': 0.18,
            'delta': 0.15,
            'mixed_egyptian': 0.12,
            'standard_arabic': 0.05
        }

        base_improvement = base_improvements.get(detection_result.primary_dialect, 0.05)
        confidence_multiplier = min(1.0, detection_result.confidence_score * 2)

        return base_improvement * confidence_multiplier