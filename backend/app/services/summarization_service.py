"""Summarization service using BART."""

from typing import Optional

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None
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
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available - summarization disabled")
            return
            
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

            # Handle long texts by chunking and hierarchical summarization
            max_input_length = 1024  # BART limit
            if len(text) > max_input_length:
                # Use hierarchical approach for long texts
                return await self._hierarchical_summarize(text, config)
            else:
                # Direct summarization for shorter texts
                return await self._direct_summarize(text, config)

        except Exception as e:
            logger.error("Summarization failed", error=str(e), text_length=len(text))
            return None

    async def _direct_summarize(self, text: str, config: dict) -> str:
        """Direct summarization for shorter texts."""
        logger.info(
            "Direct summarization",
            text_length=len(text),
            config=config
        )

        result = self.summarizer(
            text,
            max_length=config["max_length"],
            min_length=config["min_length"],
            do_sample=False,
            truncation=True,
        )

        summary = result[0]["summary_text"]
        logger.info("Direct summarization completed", summary_length=len(summary))
        return summary

    async def _hierarchical_summarize(self, text: str, config: dict) -> str:
        """Hierarchical summarization for long texts."""
        from app.utils.text import split_into_chunks

        logger.info(
            "Hierarchical summarization",
            text_length=len(text),
            config=config
        )

        # Split text into manageable chunks
        chunks = split_into_chunks(text, chunk_size=800, overlap=100)

        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            try:
                chunk_config = {
                    "max_length": min(150, config["max_length"] // len(chunks)),
                    "min_length": 20
                }

                result = self.summarizer(
                    chunk,
                    max_length=chunk_config["max_length"],
                    min_length=chunk_config["min_length"],
                    do_sample=False,
                    truncation=True,
                )

                chunk_summary = result[0]["summary_text"]
                chunk_summaries.append(chunk_summary)

            except Exception as e:
                logger.warning(f"Chunk {i} summarization failed", error=str(e))
                # Use first 100 characters as fallback
                chunk_summaries.append(chunk[:100] + "...")

        # Combine chunk summaries
        combined_summary_text = " ".join(chunk_summaries)

        # If combined summary is still too long, summarize again
        if len(combined_summary_text) > config["max_length"] * 2:
            final_result = self.summarizer(
                combined_summary_text,
                max_length=config["max_length"],
                min_length=config["min_length"],
                do_sample=False,
                truncation=True,
            )
            final_summary = final_result[0]["summary_text"]
        else:
            final_summary = combined_summary_text[:config["max_length"]]

        logger.info(
            "Hierarchical summarization completed",
            chunks=len(chunks),
            summary_length=len(final_summary)
        )
        return final_summary

    async def generate_hierarchical_summary(self, text: str) -> dict:
        """
        Generate hierarchical summary with multiple levels.

        Returns:
            Dict with different summary levels and metadata
        """
        if not text or len(text.strip()) == 0:
            return {}

        try:
            await self.load_model()

            # Level 1: Very short summary (elevator pitch)
            level1 = await self._direct_summarize(text, {
                "max_length": 50,
                "min_length": 15
            })

            # Level 2: Medium summary (key points)
            level2 = await self._direct_summarize(text, {
                "max_length": 150,
                "min_length": 50
            })

            # Level 3: Detailed summary (comprehensive)
            level3 = await self._hierarchical_summarize(text, {
                "max_length": 300,
                "min_length": 100
            })

            hierarchical_summary = {
                "level_1_elevator_pitch": level1,
                "level_2_key_points": level2,
                "level_3_comprehensive": level3,
                "metadata": {
                    "original_length": len(text),
                    "levels_generated": 3,
                    "method": "hierarchical_bart"
                }
            }

            logger.info("Hierarchical summary generated", levels=3)
            return hierarchical_summary

        except Exception as e:
            logger.error("Hierarchical summarization failed", error=str(e))
            return {}


# Global summarization service instance
summarization_service = SummarizationService()