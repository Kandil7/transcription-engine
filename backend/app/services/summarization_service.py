"""Summarization service using BART."""

from typing import Optional

from transformers import pipeline
from structlog import get_logger

from app.config import settings

logger = get_logger(__name__)


class SummarizationService:
    """Service for text summarization using BART."""

    def __init__(self):
        self.summarizer = None
        self.loaded = False

    async def load_model(self):
        """Load the summarization model."""
        if self.loaded:
            return

        try:
            logger.info("Loading summarization model", model=settings.summarization_model)

            self.summarizer = pipeline(
                "summarization",
                model=settings.summarization_model,
                device=0 if settings.gpu_memory_gb > 0 else -1,  # Use GPU if available
            )

            self.loaded = True
            logger.info("Summarization model loaded")

        except Exception as e:
            logger.error("Failed to load summarization model", error=str(e))
            raise

    async def summarize_text(
        self,
        text: str,
        length: str = "medium"
    ) -> Optional[str]:
        """
        Summarize text with specified length.

        Args:
            text: Text to summarize
            length: Summary length (short/medium/long)

        Returns:
            Summarized text or None if failed
        """
        if not text or len(text.strip()) == 0:
            return text

        try:
            await self.load_model()

            # Configure summary parameters based on length
            length_configs = {
                "short": {"max_length": 100, "min_length": 30},
                "medium": {"max_length": 200, "min_length": 50},
                "long": {"max_length": 400, "min_length": 100},
            }

            config = length_configs.get(length, length_configs["medium"])

            # Handle long texts by chunking
            max_input_length = 1024  # BART limit
            if len(text) > max_input_length:
                # Simple chunking - take first part for summary
                text = text[:max_input_length]

            logger.info(
                "Summarizing text",
                length=length,
                text_length=len(text),
                config=config
            )

            result = self.summarizer(
                text,
                max_length=config["max_length"],
                min_length=config["min_length"],
                do_sample=False,  # Deterministic for consistency
                truncation=True,
            )

            summary = result[0]["summary_text"]

            logger.info("Summarization completed", summary_length=len(summary))
            return summary

        except Exception as e:
            logger.error("Summarization failed", error=str(e), text_length=len(text))
            return None


# Global summarization service instance
summarization_service = SummarizationService()