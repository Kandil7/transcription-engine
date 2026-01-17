"""Voice analytics service for speaker diarization and emotion detection."""

import os
import tempfile
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
from pyannote.audio import Pipeline
from structlog import get_logger

from app.config import settings

logger = get_logger(__name__)


class VoiceAnalyticsService:
    """Service for voice analytics including speaker diarization and emotion detection."""

    def __init__(self):
        self.diarization_pipeline: Optional[Pipeline] = None
        self.emotion_model = None
        self.diarization_loaded = False
        self.emotion_loaded = False

    async def load_diarization_model(self) -> None:
        """Load the speaker diarization model."""
        if self.diarization_loaded:
            return

        try:
            logger.info("Loading speaker diarization model")

            # Use PyAnnote's pre-trained speaker diarization pipeline
            # Note: Requires huggingface token for some models
            self.diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=os.getenv("HF_TOKEN")  # Optional: for accessing private models
            )

            # Use GPU if available
            if torch.cuda.is_available():
                self.diarization_pipeline.to(torch.device("cuda"))

            self.diarization_loaded = True
            logger.info("Speaker diarization model loaded successfully")

        except Exception as e:
            logger.error("Failed to load diarization model", error=str(e))
            raise

    async def load_emotion_model(self) -> None:
        """Load emotion detection model."""
        if self.emotion_loaded:
            return

        try:
            logger.info("Loading emotion detection model")

            # For emotion detection, we'll use a simple rule-based approach initially
            # In production, you might want to use more sophisticated models like:
            # - Wav2Vec2 + emotion classification head
            # - SER (Speech Emotion Recognition) models

            self.emotion_loaded = True
            logger.info("Emotion detection model loaded successfully")

        except Exception as e:
            logger.error("Failed to load emotion model", error=str(e))
            raise

    async def perform_diarization(self, audio_path: str) -> List[Dict]:
        """
        Perform speaker diarization on audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            List of speaker segments with timestamps
        """
        await self.load_diarization_model()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            logger.info("Starting speaker diarization", audio_path=audio_path)

            # Run diarization
            diarization = self.diarization_pipeline(audio_path)

            # Convert to list of segments
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segment = {
                    "speaker": speaker,
                    "start": turn.start,
                    "end": turn.end,
                    "duration": turn.end - turn.start,
                }
                segments.append(segment)

            # Sort by start time
            segments.sort(key=lambda x: x["start"])

            logger.info(
                "Speaker diarization completed",
                speakers_found=len(set(s["speaker"] for s in segments)),
                segments=len(segments)
            )

            return segments

        except Exception as e:
            logger.error("Speaker diarization failed", error=str(e))
            return []

    async def analyze_emotions(self, audio_path: str, segments: List[Dict]) -> List[Dict]:
        """
        Analyze emotions in audio segments.

        Args:
            audio_path: Path to audio file
            segments: Audio segments with speaker information

        Returns:
            Segments with emotion analysis
        """
        await self.load_emotion_model()

        try:
            logger.info("Starting emotion analysis", segments=len(segments))

            # For now, implement a basic emotion detection based on audio features
            # In production, you would use more sophisticated models

            enhanced_segments = []

            for segment in segments:
                # Extract audio segment (simplified - in production use proper audio processing)
                emotion = await self._detect_emotion_basic(segment)

                enhanced_segment = {
                    **segment,
                    "emotion": emotion,
                    "confidence": 0.7,  # Placeholder confidence score
                }
                enhanced_segments.append(enhanced_segment)

            logger.info("Emotion analysis completed", segments_processed=len(enhanced_segments))
            return enhanced_segments

        except Exception as e:
            logger.error("Emotion analysis failed", error=str(e))
            # Return segments without emotion analysis
            return segments

    async def _detect_emotion_basic(self, segment: Dict) -> str:
        """
        Basic emotion detection based on segment characteristics.

        This is a simplified implementation. In production, you would use:
        - Acoustic features (pitch, energy, MFCCs)
        - Machine learning models trained on emotion datasets
        - Pre-trained emotion recognition models
        """
        # Simulate emotion detection based on segment duration and position
        duration = segment["duration"]

        # Very basic rules (replace with actual ML model)
        if duration < 1.0:
            return "neutral"  # Short utterances often neutral
        elif duration > 10.0:
            return "confident"  # Long utterances might indicate confidence
        else:
            # Random emotion for demonstration (replace with actual detection)
            emotions = ["happy", "sad", "angry", "neutral", "excited", "calm"]
            return emotions[hash(str(segment)) % len(emotions)]

    async def combine_transcription_and_diarization(
        self,
        transcription_segments: List[Dict],
        diarization_segments: List[Dict]
    ) -> List[Dict]:
        """
        Combine transcription segments with speaker diarization results.

        Args:
            transcription_segments: Segments from Whisper transcription
            diarization_segments: Segments from speaker diarization

        Returns:
            Combined segments with speaker attribution
        """
        try:
            logger.info(
                "Combining transcription and diarization",
                transcription_segments=len(transcription_segments),
                diarization_segments=len(diarization_segments)
            )

            combined_segments = []

            for trans_seg in transcription_segments:
                # Find overlapping diarization segment
                speaker = "Unknown"
                emotion = "neutral"

                trans_start = trans_seg["start"]
                trans_end = trans_seg["end"]

                # Find the diarization segment that overlaps most with this transcription segment
                max_overlap = 0
                for dia_seg in diarization_segments:
                    dia_start = dia_seg["start"]
                    dia_end = dia_seg["end"]

                    # Calculate overlap
                    overlap_start = max(trans_start, dia_start)
                    overlap_end = min(trans_end, dia_end)
                    overlap = max(0, overlap_end - overlap_start)

                    if overlap > max_overlap:
                        max_overlap = overlap
                        speaker = dia_seg["speaker"]
                        emotion = dia_seg.get("emotion", "neutral")

                # Create combined segment
                combined_segment = {
                    **trans_seg,
                    "speaker": speaker,
                    "emotion": emotion,
                    "speaker_confidence": max_overlap / (trans_end - trans_start) if trans_end > trans_start else 0,
                }
                combined_segments.append(combined_segment)

            logger.info(
                "Transcription and diarization combined",
                combined_segments=len(combined_segments),
                speakers_identified=len(set(s["speaker"] for s in combined_segments))
            )

            return combined_segments

        except Exception as e:
            logger.error("Failed to combine transcription and diarization", error=str(e))
            # Return transcription segments without speaker info
            return transcription_segments

    async def analyze_meeting_dynamics(self, segments: List[Dict]) -> Dict:
        """
        Analyze meeting dynamics from speaker segments.

        Args:
            segments: Speaker-attributed segments

        Returns:
            Meeting analysis statistics
        """
        try:
            if not segments:
                return {}

            # Calculate speaker statistics
            speaker_stats = {}
            total_duration = 0

            for segment in segments:
                speaker = segment["speaker"]
                duration = segment["duration"]
                emotion = segment.get("emotion", "neutral")

                if speaker not in speaker_stats:
                    speaker_stats[speaker] = {
                        "total_speech_time": 0,
                        "segment_count": 0,
                        "emotions": {},
                        "avg_segment_length": 0,
                    }

                speaker_stats[speaker]["total_speech_time"] += duration
                speaker_stats[speaker]["segment_count"] += 1

                # Track emotions
                if emotion not in speaker_stats[speaker]["emotions"]:
                    speaker_stats[speaker]["emotions"][emotion] = 0
                speaker_stats[speaker]["emotions"][emotion] += 1

                total_duration += duration

            # Calculate percentages and averages
            for speaker, stats in speaker_stats.items():
                stats["speech_percentage"] = (stats["total_speech_time"] / total_duration) * 100 if total_duration > 0 else 0
                stats["avg_segment_length"] = stats["total_speech_time"] / stats["segment_count"] if stats["segment_count"] > 0 else 0

            # Meeting-level statistics
            meeting_stats = {
                "total_duration": total_duration,
                "total_speakers": len(speaker_stats),
                "speaker_stats": speaker_stats,
                "dominant_speaker": max(speaker_stats.items(), key=lambda x: x[1]["total_speech_time"])[0] if speaker_stats else None,
                "meeting_balance_score": self._calculate_balance_score(speaker_stats),
            }

            logger.info("Meeting dynamics analyzed", speakers=len(speaker_stats))
            return meeting_stats

        except Exception as e:
            logger.error("Meeting dynamics analysis failed", error=str(e))
            return {}

    def _calculate_balance_score(self, speaker_stats: Dict) -> float:
        """
        Calculate a balance score for the meeting (0-100).
        Higher scores indicate more balanced participation.
        """
        if not speaker_stats:
            return 0.0

        # Calculate speech time variance
        speech_times = [stats["total_speech_time"] for stats in speaker_stats.values()]
        mean_time = sum(speech_times) / len(speech_times)

        if mean_time == 0:
            return 100.0  # Perfect balance if no one spoke

        variance = sum((time - mean_time) ** 2 for time in speech_times) / len(speech_times)
        std_dev = variance ** 0.5

        # Convert to balance score (lower variance = higher balance)
        balance_score = max(0, 100 - (std_dev / mean_time) * 50)

        return round(balance_score, 1)

    def get_model_status(self) -> Dict:
        """Get status of loaded models."""
        return {
            "diarization_loaded": self.diarization_loaded,
            "emotion_loaded": self.emotion_loaded,
            "device": "cuda" if torch.cuda.is_available() else "cpu",
        }


# Global voice analytics service instance
voice_analytics_service = VoiceAnalyticsService()