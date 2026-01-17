"""Text processing utilities."""

import re
from typing import List

from structlog import get_logger

logger = get_logger(__name__)


def split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split text into chunks with optional overlap.

    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        # Find the end of this chunk
        end = start + chunk_size

        # If we're not at the end, try to break at a sentence or word boundary
        if end < len(text):
            # Look for sentence endings within the last 100 characters
            sentence_endings = ['. ', '! ', '? ', '\n\n', '\n']
            best_break = end

            for ending in sentence_endings:
                last_ending = text.rfind(ending, start, end)
                if last_ending != -1 and last_ending > best_break - 200:
                    best_break = last_ending + len(ending)
                    break

            # If no good sentence break, try word boundary
            if best_break == end:
                space_pos = text.rfind(' ', start, end)
                if space_pos != -1:
                    best_break = space_pos + 1

            end = best_break

        # Extract chunk
        chunk = text[start:end].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)

        # Move start position with overlap
        start = max(start + 1, end - overlap)

        # Prevent infinite loops
        if start >= len(text):
            break

        # Safety check to prevent too many chunks
        if len(chunks) > 1000:
            logger.warning("Too many chunks generated, truncating")
            break

    logger.info(
        "Text split into chunks",
        original_length=len(text),
        chunk_count=len(chunks),
        avg_chunk_size=sum(len(c) for c in chunks) / len(chunks) if chunks else 0
    )

    return chunks


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Arabic sentence endings
    sentence_pattern = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_pattern, text.strip())

    # Filter out empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs.

    Args:
        text: Text to split

    Returns:
        List of paragraphs
    """
    # Split on double newlines (common paragraph separator)
    paragraphs = re.split(r'\n\s*\n', text.strip())

    # Filter out empty paragraphs
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    return paragraphs


def estimate_reading_time(text: str, words_per_minute: int = 200) -> float:
    """
    Estimate reading time for text in minutes.

    Args:
        text: Text to analyze
        words_per_minute: Average reading speed

    Returns:
        Estimated reading time in minutes
    """
    # Simple word count (split on whitespace)
    words = len(text.split())
    minutes = words / words_per_minute

    return round(minutes, 2)


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text (simple frequency-based approach).

    Args:
        text: Text to analyze
        max_keywords: Maximum number of keywords to return

    Returns:
        List of keywords
    """
    # Simple keyword extraction based on word frequency
    words = re.findall(r'\b\w+\b', text.lower())

    # Remove common Arabic stop words (basic list)
    stop_words = {
        'و', 'في', 'من', 'على', 'إلى', 'عن', 'مع', 'هو', 'هي', 'هم', 'هما',
        'كان', 'كانت', 'يكون', 'تكون', 'أنا', 'نحن', 'أنت', 'أنتي', 'أنتم',
        'هذا', 'هذه', 'هؤلاء', 'ذلك', 'تلك', 'هناك', 'كيف', 'متى', 'أين',
        'لماذا', 'ماذا', 'ما', 'لا', 'نعم', 'كلا', 'أو', 'لكن', 'بل', 'ثم'
    }

    # Filter words
    filtered_words = [
        word for word in words
        if len(word) > 2 and word not in stop_words
    ]

    # Count frequency
    word_freq = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1

    # Sort by frequency and return top keywords
    sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

    keywords = [word for word, freq in sorted_keywords[:max_keywords]]

    logger.info(
        "Keywords extracted",
        text_length=len(text),
        keywords_found=len(keywords)
    )

    return keywords


def get_text_statistics(text: str) -> dict:
    """
    Get comprehensive text statistics.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with various text statistics
    """
    sentences = split_into_sentences(text)
    paragraphs = split_into_paragraphs(text)
    keywords = extract_keywords(text)

    stats = {
        "character_count": len(text),
        "word_count": len(text.split()),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "keyword_count": len(keywords),
        "top_keywords": keywords[:5],  # Top 5 keywords
        "avg_words_per_sentence": round(len(text.split()) / len(sentences), 1) if sentences else 0,
        "avg_sentences_per_paragraph": round(len(sentences) / len(paragraphs), 1) if paragraphs else 0,
        "estimated_reading_time_minutes": estimate_reading_time(text),
        "language_hint": "ar" if any(ord(c) > 127 for c in text) else "en"
    }

    logger.info("Text statistics calculated", stats=stats)
    return stats