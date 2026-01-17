"""Text-to-Speech service for generating audio summaries."""

import asyncio
import os
import tempfile
from typing import Optional

from structlog import get_logger

from app.config import settings

logger = get_logger(__name__)


class TTSService:
    """Service for generating speech from text using various TTS engines."""

    def __init__(self):
        self.tts_engine = settings.tts_engine if hasattr(settings, 'tts_engine') else "edge-tts"
        self.voice = settings.tts_voice if hasattr(settings, 'tts_voice') else "ar-EG-SalmaNeural"
        self._initialized = False

    async def initialize(self):
        """Initialize the TTS service."""
        if self._initialized:
            return

        try:
            if self.tts_engine == "coqui":
                # Import Coqui TTS
                from TTS.api import TTS

                # List available models (you might want to choose a specific Arabic model)
                available_models = TTS.list_models()
                arabic_models = [model for model in available_models if 'ar' in model.lower()]

                if arabic_models:
                    self.tts_model = TTS(arabic_models[0])
                    logger.info("Initialized Coqui TTS", model=arabic_models[0])
                else:
                    # Fallback to English model
                    self.tts_model = TTS("tts_models/en/ljspeech/tacotron2-DDC_ph")
                    logger.info("Initialized Coqui TTS with English fallback")

            elif self.tts_engine == "edge-tts":
                # Edge TTS is imported when needed
                pass

            self._initialized = True
            logger.info("TTS service initialized", engine=self.tts_engine)

        except Exception as e:
            logger.error("Failed to initialize TTS service", error=str(e))
            raise

    async def generate_speech(self, text: str, output_path: Optional[str] = None) -> str:
        """
        Generate speech from text.

        Args:
            text: Text to convert to speech
            output_path: Optional output path for the audio file

        Returns:
            Path to the generated audio file
        """
        await self.initialize()

        if not output_path:
            # Create temporary file
            temp_dir = os.path.join(settings.processed_dir, "tts")
            os.makedirs(temp_dir, exist_ok=True)
            output_path = os.path.join(temp_dir, f"tts_summary_{hash(text)}.mp3")

        try:
            if self.tts_engine == "coqui":
                # Use Coqui TTS
                self.tts_model.tts_to_file(text=text, file_path=output_path)

            elif self.tts_engine == "edge-tts":
                # Use Microsoft Edge TTS
                import edge_tts

                communicate = edge_tts.Communicate(text, self.voice)
                await communicate.save(output_path)

            else:
                raise ValueError(f"Unsupported TTS engine: {self.tts_engine}")

            logger.info("TTS audio generated", output_path=output_path, text_length=len(text))
            return output_path

        except Exception as e:
            logger.error("TTS generation failed", error=str(e), text_preview=text[:100])
            raise

    async def get_available_voices(self) -> list:
        """Get list of available voices for the current TTS engine."""
        await self.initialize()

        try:
            if self.tts_engine == "edge-tts":
                import edge_tts

                voices = await edge_tts.list_voices()
                return [voice['ShortName'] for voice in voices if voice.get('Locale', '').startswith('ar')]

            elif self.tts_engine == "coqui":
                # Coqui TTS doesn't have a simple voice listing API
                return ["default_arabic_voice"]

            return []

        except Exception as e:
            logger.error("Failed to get available voices", error=str(e))
            return []


# Global TTS service instance
tts_service = TTSService()