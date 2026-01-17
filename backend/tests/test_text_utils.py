"""Tests for text processing utilities."""

from app.utils.text import (
    split_into_chunks,
    split_into_sentences,
    split_into_paragraphs,
    estimate_reading_time,
    extract_keywords,
    get_text_statistics
)


def test_split_into_chunks():
    """Test text chunking."""
    text = "This is a test. " * 100  # Long text

    chunks = split_into_chunks(text, chunk_size=50, overlap=10)

    assert len(chunks) > 1
    assert all(len(chunk) <= 60 for chunk in chunks)  # Allow some overlap

    # Test overlap
    if len(chunks) > 1:
        # Last part of first chunk should appear in second chunk
        assert chunks[0][-10:] in chunks[1][:20]


def test_split_into_sentences():
    """Test sentence splitting."""
    text = "This is sentence one. This is sentence two! What about this? Another sentence."

    sentences = split_into_sentences(text)

    assert len(sentences) == 4
    assert "This is sentence one." in sentences
    assert "This is sentence two!" in sentences
    assert "What about this?" in sentences


def test_split_into_paragraphs():
    """Test paragraph splitting."""
    text = """First paragraph with some content.

Second paragraph here.

Third paragraph."""

    paragraphs = split_into_paragraphs(text)

    assert len(paragraphs) == 3
    assert "First paragraph" in paragraphs[0]
    assert "Second paragraph" in paragraphs[1]
    assert "Third paragraph" in paragraphs[2]


def test_estimate_reading_time():
    """Test reading time estimation."""
    # Average person reads ~200 words per minute
    text_200_words = "word " * 200

    time_minutes = estimate_reading_time(text_200_words)

    assert abs(time_minutes - 1.0) < 0.1  # Should be close to 1 minute


def test_extract_keywords():
    """Test keyword extraction."""
    text = """
    The artificial intelligence and machine learning are transforming technology.
    AI and ML are key technologies for the future. Artificial intelligence helps solve complex problems.
    Machine learning algorithms are powerful tools.
    """

    keywords = extract_keywords(text, max_keywords=5)

    # Should extract meaningful keywords
    assert len(keywords) <= 5
    assert isinstance(keywords, list)

    # Common words should be filtered out
    assert "the" not in [kw.lower() for kw in keywords]
    assert "and" not in [kw.lower() for kw in keywords]


def test_get_text_statistics():
    """Test comprehensive text statistics."""
    text = """First paragraph. This has multiple sentences!

Second paragraph with different content.
More text here."""

    stats = get_text_statistics(text)

    assert stats["character_count"] == len(text)
    assert stats["word_count"] > 0
    assert stats["sentence_count"] > 0
    assert stats["paragraph_count"] == 2
    assert "estimated_reading_time_minutes" in stats
    assert "top_keywords" in stats
    assert "language_hint" in stats


def test_empty_text_handling():
    """Test handling of empty or minimal text."""
    # Empty text
    chunks = split_into_chunks("")
    assert chunks == []

    sentences = split_into_sentences("")
    assert sentences == []

    paragraphs = split_into_paragraphs("")
    assert paragraphs == []

    # Whitespace only
    chunks = split_into_chunks("   ")
    assert chunks == ["   "]

    sentences = split_into_sentences("   ")
    assert sentences == []


def test_arabic_text_processing():
    """Test processing of Arabic text."""
    arabic_text = """
    الذكاء الاصطناعي يغير العالم. التعلم الآلي مهم جداً.
    التكنولوجيا تتطور بسرعة كبيرة.
    """

    sentences = split_into_sentences(arabic_text)
    assert len(sentences) > 0

    keywords = extract_keywords(arabic_text)
    assert isinstance(keywords, list)

    stats = get_text_statistics(arabic_text)
    assert stats["language_hint"] == "ar"
    assert stats["character_count"] > 0


def test_mixed_language_text():
    """Test processing of mixed language text."""
    mixed_text = "Hello world. مرحباً بالعالم. This is English and Arabic mixed."

    sentences = split_into_sentences(mixed_text)
    assert len(sentences) > 0

    stats = get_text_statistics(mixed_text)
    # Should detect as containing non-ASCII characters
    assert stats["language_hint"] == "ar" or len(stats["top_keywords"]) > 0


def test_chunk_overlap():
    """Test that chunk overlap works correctly."""
    text = "word " * 100

    chunks = split_into_chunks(text, chunk_size=20, overlap=5)

    assert len(chunks) > 1

    # Verify overlap
    for i in range(len(chunks) - 1):
        current_end = chunks[i].split()[-3:]  # Last 3 words of current chunk
        next_start = chunks[i + 1].split()[:3]  # First 3 words of next chunk

        # There should be some overlap
        overlap_found = any(word in next_start for word in current_end)
        assert overlap_found, f"No overlap between chunks {i} and {i+1}"