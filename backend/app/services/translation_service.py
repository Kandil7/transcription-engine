"""Translation service using NLLB."""

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


class TranslationService:
    """Service for text translation using NLLB."""

    def __init__(self):
        self.translator = None
        self.loaded = False

    async def load_model(self):
        """Load the translation model."""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available - translation disabled")
            return
            
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

            # Enhanced language mapping with more Arabic variants
            lang_map = {
                "ar": "arb_Arab",
                "arabic": "arb_Arab",
                "ara": "arb_Arab",  # Egyptian Arabic
                "arz": "arb_Arab",  # Egyptian Arabic
                "en": "eng_Latn",
                "english": "eng_Latn",
                "fr": "fra_Latn",
                "french": "fra_Latn",
                "de": "deu_Latn",
                "german": "deu_Latn",
                "es": "spa_Latn",
                "spanish": "spa_Latn",
                "it": "ita_Latn",
                "italian": "ita_Latn",
                "pt": "por_Latn",
                "portuguese": "por_Latn",
                "ru": "rus_Cyrl",
                "russian": "rus_Cyrl",
                "zh": "zho_Hans",
                "chinese": "zho_Hans",
                "ja": "jpn_Jpan",
                "japanese": "jpn_Jpan",
                "ko": "kor_Hang",
                "korean": "kor_Hang",
            }

            source_lang_nllb = lang_map.get(source_lang.lower(), "arb_Arab")
            target_lang_nllb = lang_map.get(target_lang.lower(), "eng_Latn")

            logger.info(
                "Translating text",
                source_lang=f"{source_lang} -> {source_lang_nllb}",
                target_lang=f"{target_lang} -> {target_lang_nllb}",
                text_length=len(text)
            )

            # Split into sentences first for better translation quality
            from app.utils.text import split_into_sentences
            sentences = split_into_sentences(text)

            # Translate in smaller chunks to maintain context
            translated_sentences = []
            chunk_size = 10  # Translate 10 sentences at a time

            for i in range(0, len(sentences), chunk_size):
                chunk_sentences = sentences[i:i + chunk_size]
                chunk_text = " ".join(chunk_sentences)

                if len(chunk_text) > 500:  # Further split if too long
                    sub_chunks = [chunk_text[j:j + 500] for j in range(0, len(chunk_text), 500)]
                else:
                    sub_chunks = [chunk_text]

                for sub_chunk in sub_chunks:
                    if sub_chunk.strip():
                        try:
                            result = self.translator(
                                sub_chunk,
                                src_lang=source_lang_nllb,
                                tgt_lang=target_lang_nllb
                            )
                            translated_chunk = result[0]["translation_text"]
                            translated_sentences.append(translated_chunk)
                        except Exception as chunk_error:
                            logger.warning("Chunk translation failed", error=str(chunk_error))
                            # Keep original as fallback
                            translated_sentences.append(sub_chunk)

            translated_text = " ".join(translated_sentences)

            # Post-process Arabic text (remove extra spaces, fix punctuation)
            if target_lang.lower() in ["ar", "arabic", "ara", "arz"]:
                translated_text = self._post_process_arabic(translated_text)

            logger.info(
                "Translation completed",
                translated_length=len(translated_text),
                sentences_processed=len(sentences)
            )
            return translated_text

        except Exception as e:
            logger.error("Translation failed", error=str(e), text_length=len(text))
            return None

    def _post_process_arabic(self, text: str) -> str:
        """Post-process Arabic translation for better readability."""
        import re

        # Fix common Arabic punctuation issues
        text = re.sub(r'\s+([.!?،؛:])', r'\1', text)  # Remove space before punctuation
        text = re.sub(r'([.!?،؛:])\s+', r'\1 ', text)  # Ensure space after punctuation
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace

        return text.strip()

    async def translate_with_fallback(
        self,
        text: str,
        source_lang: str = "ar",
        target_lang: str = "en",
        fallback_langs: List[str] = None
    ) -> Optional[str]:
        """
        Translate with fallback languages if primary translation fails.

        Args:
            text: Text to translate
            source_lang: Primary source language
            target_lang: Target language
            fallback_langs: List of fallback source languages to try

        Returns:
            Translated text or None if all attempts fail
        """
        # Try primary translation
        result = await self.translate_text(text, source_lang, target_lang)
        if result:
            return result

        # Try fallback languages
        if fallback_langs:
            for fallback_lang in fallback_langs:
                logger.info("Trying fallback translation", fallback_lang=fallback_lang)
                result = await self.translate_text(text, fallback_lang, target_lang)
                if result:
                    return result

        return None


# Global translation service instance
translation_service = TranslationService()