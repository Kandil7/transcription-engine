"""Tests for enhanced translation and summarization services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.translation_service import TranslationService
from app.services.summarization_service import SummarizationService


@pytest.mark.asyncio
async def test_translation_service_initialization():
    """Test translation service initialization."""
    service = TranslationService()

    # Mock the pipeline
    with patch('app.services.translation_service.pipeline') as mock_pipeline:
        mock_translator = MagicMock()
        mock_pipeline.return_value = mock_translator
        service.translator = mock_translator

        await service.load_model()

        assert service.loaded
        mock_pipeline.assert_called_once()


@pytest.mark.asyncio
async def test_arabic_to_english_translation():
    """Test Arabic to English translation."""
    service = TranslationService()

    # Mock the translator
    mock_result = [{"translation_text": "Hello, how are you?"}]
    service.translator = MagicMock(return_value=mock_result)
    service.loaded = True

    result = await service.translate_text(
        "مرحباً، كيف حالك؟",
        source_lang="ar",
        target_lang="en"
    )

    assert result == "Hello, how are you?"
    service.translator.assert_called_once()


@pytest.mark.asyncio
async def test_translation_with_fallback():
    """Test translation with fallback languages."""
    service = TranslationService()

    # Mock translator to fail first, succeed second
    service.translator = MagicMock()
    service.translator.side_effect = [
        Exception("Translation failed"),
        [{"translation_text": "Success with fallback"}]
    ]
    service.loaded = True

    result = await service.translate_with_fallback(
        "test text",
        source_lang="unknown",
        target_lang="en",
        fallback_langs=["ar", "en"]
    )

    assert result == "Success with fallback"
    assert service.translator.call_count == 2


@pytest.mark.asyncio
async def test_hierarchical_summarization():
    """Test hierarchical summarization."""
    service = SummarizationService()

    # Mock the summarizer
    mock_result = [{"summary_text": "Short summary"}]
    service.summarizer = MagicMock(return_value=mock_result)
    service.loaded = True

    # Mock hierarchical summary method
    service._direct_summarize = AsyncMock(return_value="Level 1 summary")
    service._hierarchical_summarize = AsyncMock(return_value="Level 3 summary")

    result = await service.generate_hierarchical_summary("Long text content here...")

    assert "level_1_elevator_pitch" in result
    assert "level_2_key_points" in result
    assert "level_3_comprehensive" in result
    assert "metadata" in result


@pytest.mark.asyncio
async def test_hierarchical_summarize_long_text():
    """Test hierarchical summarization of long text."""
    service = SummarizationService()

    # Mock components
    service.summarizer = MagicMock()
    service.summarizer.return_value = [{"summary_text": "Chunk summary"}]
    service.loaded = True

    long_text = "This is a very long text. " * 1000  # Make it long

    result = await service._hierarchical_summarize(long_text, {"max_length": 200, "min_length": 50})

    assert isinstance(result, str)
    assert len(result) > 0
    service.summarizer.assert_called()


@pytest.mark.asyncio
async def test_direct_summarize_short_text():
    """Test direct summarization of short text."""
    service = SummarizationService()

    # Mock the summarizer
    mock_result = [{"summary_text": "This is a summary."}]
    service.summarizer = MagicMock(return_value=mock_result)
    service.loaded = True

    short_text = "This is a short text to summarize."
    config = {"max_length": 100, "min_length": 20}

    result = await service._direct_summarize(short_text, config)

    assert result == "This is a summary."
    service.summarizer.assert_called_once()


@pytest.mark.asyncio
async def test_summarization_with_different_lengths():
    """Test summarization with different length preferences."""
    service = SummarizationService()

    # Mock the summarizer
    service.summarizer = MagicMock(return_value=[{"summary_text": "Summary"}])
    service.loaded = True
    service.generate_hierarchical_summary = AsyncMock(return_value={
        "level_1_elevator_pitch": "Short summary",
        "level_2_key_points": "Medium summary",
        "level_3_comprehensive": "Long summary"
    })

    # Test short length
    result = await service.summarize_text("Test text", length="short")
    assert result == "Short summary"

    # Test medium length
    result = await service.summarize_text("Test text", length="medium")
    assert result == "Medium summary"

    # Test long length
    result = await service.summarize_text("Test text", length="long")
    assert result == "Long summary"


def test_arabic_post_processing():
    """Test Arabic text post-processing."""
    service = TranslationService()

    # Test punctuation fixes
    text = "مرحباً   . كيف حالك ؟"
    processed = service._post_process_arabic(text)

    assert "  ." not in processed
    assert ". " in processed or "؟" in processed


@pytest.mark.asyncio
async def test_empty_text_handling():
    """Test handling of empty or whitespace-only text."""
    trans_service = TranslationService()
    sum_service = SummarizationService()

    # Test translation
    result = await trans_service.translate_text("")
    assert result == ""

    result = await trans_service.translate_text("   ")
    assert result == "   "

    # Test summarization
    result = await sum_service.summarize_text("")
    assert result == ""

    result = await sum_service.summarize_text("   ")
    assert result == "   "