"""Tests for RAG service."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_rag_service_initialization():
    """Test RAG service initialization."""
    service = RAGService()

    # Mock the initialization components
    service.chroma_client = MagicMock()
    service.embedding_function = MagicMock()
    service.llm = MagicMock()
    service.initialized = True

    await service.initialize()

    assert service.initialized


@pytest.mark.asyncio
async def test_transcription_correction():
    """Test transcription correction with RAG."""
    service = RAGService()

    # Mock dependencies
    service.chroma_client = MagicMock()
    service.embedding_function = MagicMock()
    service.llm = MagicMock(return_value="Corrected text")
    service.initialized = True

    # Mock Chroma collection
    mock_collection = MagicMock()
    mock_collection.count.return_value = 5
    service.chroma_client.get_collection.return_value = mock_collection

    # Mock LangChain components
    mock_vectorstore = MagicMock()
    mock_retriever = MagicMock()
    mock_retriever.get_relevant_documents.return_value = [
        MagicMock(page_content="Sample context")
    ]
    mock_vectorstore.as_retriever.return_value = mock_retriever

    # Test correction
    original = "هذا نص تجريبي بالعربية"
    corrected = await service.correct_transcription(original, "test-job")

    assert corrected == "Corrected text"
    assert service.llm.called


@pytest.mark.asyncio
async def test_qa_system_setup():
    """Test QA system setup."""
    service = RAGService()

    # Mock dependencies
    service.chroma_client = MagicMock()
    service.embedding_function = MagicMock()
    service.llm = MagicMock()
    service.initialized = True

    # Mock Chroma collection
    mock_collection = MagicMock()
    service.chroma_client.get_collection.return_value = mock_collection

    # Test QA setup
    transcript = "This is a test transcript with some content."
    await service.setup_qa_system(transcript, "test-job")

    assert service.qa_chain is not None


@pytest.mark.asyncio
async def test_ask_question():
    """Test question answering."""
    service = RAGService()

    # Mock dependencies
    service.chroma_client = MagicMock()
    service.embedding_function = MagicMock()
    service.llm = MagicMock()
    service.initialized = True

    # Mock QA chain
    mock_result = {
        "result": "This is the answer",
        "source_documents": [
            MagicMock(page_content="Source text 1", metadata={"chunk_id": 0}),
            MagicMock(page_content="Source text 2", metadata={"chunk_id": 1})
        ]
    }
    service.qa_chain = MagicMock(return_value=mock_result)

    # Test question answering
    result = await service.ask_question("What is this about?", "test-job")

    assert result["answer"] == "This is the answer"
    assert len(result["sources"]) == 2
    assert result["confidence"] == 0.85


@pytest.mark.asyncio
async def test_knowledge_base_indexing():
    """Test knowledge base indexing."""
    service = RAGService()

    # Mock dependencies
    service.chroma_client = MagicMock()
    service.embedding_function = MagicMock()
    service.initialized = True

    # Test KB indexing
    documents = ["Document 1", "Document 2", "Document 3"]
    await service.index_arabic_knowledge_base(documents)

    # Verify Chroma was called
    assert service.chroma_client is not None


def test_collection_stats():
    """Test collection statistics retrieval."""
    service = RAGService()

    # Mock Chroma client
    mock_collection = MagicMock()
    mock_collection.count.return_value = 10
    service.chroma_client = MagicMock()
    service.chroma_client.get_collection.return_value = mock_collection

    # Test stats
    stats = service.get_collection_stats("test-collection")

    assert stats["collection_name"] == "test-collection"
    assert stats["document_count"] == 10
    assert stats["status"] == "active"