"""Translation service using NLLB."""

from typing import Optional

from transformers import pipeline
from structlog import get_logger

from app.config import settings

logger = get_logger(__name__)


class TranslationService:
    """Service for text translation using NLLB."""

    def __init__(self):
        self.translator = None
        self.loaded = False

    async def load_model(self):
        """Load the translation model."""
        if self.loaded:
            return

        try:
            logger.info("Loading translation model", model=settings.translation_model)

            self.translator = pipeline(
                "translation",
                model=settings.translation_model,
                device=0 if settings.gpu_memory_gb > 0 else -1,  # Use GPU if available
            )

            self.loaded = True
            logger.info("Translation model loaded")

        except Exception as e:
            logger.error("Failed to load translation model", error=str(e))
            raise

    async def translate_text(
        self,
        text: str,
        source_lang: str = "ar",
        target_lang: str = "en"
    ) -> Optional[str]:
        """
        Translate text from source to target language.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code

        Returns:
            Translated text or None if failed
        """
        if not text or len(text.strip()) == 0:
            return text

        try:
            await self.load_model()

            # Map language codes to NLLB format
            lang_map = {
                "ar": "arb_Arab",
                "en": "eng_Latn",
                "fr": "fra_Latn",
                "de": "deu_Latn",
                "es": "spa_Latn",
            }

            source_lang_nllb = lang_map.get(source_lang, "arb_Arab")
            target_lang_nllb = lang_map.get(target_lang, "eng_Latn")

            logger.info(
                "Translating text",
                source_lang=source_lang,
                target_lang=target_lang,
                text_length=len(text)
            )

            # Split long text into chunks to avoid model limits
            max_chunk_length = 512
            chunks = [text[i:i + max_chunk_length] for i in range(0, len(text), max_chunk_length)]

            translated_chunks = []
            for chunk in chunks:
                if chunk.strip():
                    result = self.translator(
                        chunk,
                        src_lang=source_lang_nllb,
                        tgt_lang=target_lang_nllb
                    )
                    translated_chunks.append(result[0]["translation_text"])

            translated_text = " ".join(translated_chunks)

            logger.info("Translation completed", translated_length=len(translated_text))
            return translated_text

        except Exception as e:
            logger.error("Translation failed", error=str(e), text_length=len(text))
            return None


# Global translation service instance
translation_service = TranslationService()