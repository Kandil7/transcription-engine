"""RAG (Retrieval-Augmented Generation) service for Arabic text correction and QA."""

import os
from typing import Dict, List, Optional, Tuple

from structlog import get_logger

from app.config import settings

# Optional imports for AI/ML features
try:
    from chromadb import Client, Settings
    from chromadb.utils import embedding_functions
    from langchain.chains import RetrievalQA
    from langchain.docstore.document import Document
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.llms import HuggingFacePipeline
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.vectorstores import Chroma
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger = get_logger(__name__)
    logger.warning("RAG dependencies not available. RAG features will be disabled.")

logger = get_logger(__name__)


class RAGService:
    """Service for RAG operations on Arabic text."""

    def __init__(self):
        self.chroma_client = None
        self.embedding_function = None
        self.llm = None
        self.qa_chain = None
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the RAG service components."""
        if not RAG_AVAILABLE:
            logger.warning("RAG service not available - dependencies not installed")
            return
            
        if self.initialized:
            return

        try:
            logger.info("Initializing RAG service")

            # Initialize ChromaDB client
            self.chroma_client = Client(Settings(
                chroma_server_host=settings.vector_db_url.replace("http://", "").split(":")[0],
                chroma_server_http_port=int(settings.vector_db_url.split(":")[-1]),
                chroma_api_impl="rest",
            ))

            # Initialize Arabic embeddings
            self.embedding_function = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                model_kwargs={"device": "cuda" if settings.gpu_memory_gb > 0 else "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )

            # Initialize LLM for correction and QA
            model_name = "aubmindlab/aragpt2-base"  # Arabic GPT-2 for correction
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

            # Create text generation pipeline
            text_gen_pipeline = pipeline(
                "text2text-generation",
                model=model,
                tokenizer=tokenizer,
                max_length=512,
                device=0 if settings.gpu_memory_gb > 0 else -1,
            )

            self.llm = HuggingFacePipeline(pipeline=text_gen_pipeline)

            self.initialized = True
            logger.info("RAG service initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize RAG service", error=str(e))
            if not RAG_AVAILABLE:
                logger.warning("RAG dependencies not installed - service will operate in limited mode")
            else:
                raise

    async def correct_transcription(self, transcript: str, job_id: str) -> str:
        """
        Correct transcription errors using RAG.

        Args:
            transcript: Raw transcript text
            job_id: Job identifier for context

        Returns:
            Corrected transcript
        """
        if not RAG_AVAILABLE or not self.initialized:
            logger.debug("RAG not available, returning original transcript")
            return transcript
            
        await self.initialize()

        try:
            # Create a temporary collection for this job
            collection_name = f"job_{job_id}"

            # Split transcript into chunks for embedding
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", " ", ""]
            )

            chunks = text_splitter.split_text(transcript)

            # Create documents
            documents = [
                Document(page_content=chunk, metadata={"chunk_id": i, "job_id": job_id})
                for i, chunk in enumerate(chunks)
            ]

            # Create vector store
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embedding_function,
                collection_name=collection_name,
                client=self.chroma_client
            )

            # For each chunk, retrieve similar correct examples and use LLM to correct
            corrected_chunks = []
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

            for i, chunk in enumerate(chunks):
                # Retrieve similar chunks (could be from a knowledge base of correct transcripts)
                similar_docs = retriever.get_relevant_documents(chunk)

                # Use LLM to correct the chunk
                correction_prompt = f"""
                Correct any transcription errors in the following Arabic text.
                Maintain the original meaning but fix obvious mistakes:

                Original: {chunk}

                Corrected:
                """

                corrected_chunk = self.llm(correction_prompt)
                corrected_chunks.append(corrected_chunk)

            # Join corrected chunks
            corrected_transcript = " ".join(corrected_chunks)

            logger.info(
                "Transcription correction completed",
                job_id=job_id,
                original_length=len(transcript),
                corrected_length=len(corrected_transcript)
            )

            return corrected_transcript

        except Exception as e:
            logger.error("Transcription correction failed", job_id=job_id, error=str(e))
            return transcript  # Return original if correction fails

    async def setup_qa_system(self, transcript: str, job_id: str) -> None:
        """
        Set up QA system for a transcript.

        Args:
            transcript: Transcript text to make searchable
            job_id: Job identifier
        """
        await self.initialize()

        try:
            collection_name = f"qa_{job_id}"

            # Split transcript into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )

            chunks = text_splitter.split_text(transcript)
            documents = [
                Document(page_content=chunk, metadata={"chunk_id": i, "job_id": job_id})
                for i, chunk in enumerate(chunks)
            ]

            # Create vector store for QA
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embedding_function,
                collection_name=collection_name,
                client=self.chroma_client
            )

            # Create QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
                return_source_documents=True
            )

            logger.info("QA system set up", job_id=job_id, chunks=len(chunks))

        except Exception as e:
            logger.error("QA system setup failed", job_id=job_id, error=str(e))
            raise

    async def ask_question(self, question: str, job_id: str) -> Dict:
        """
        Ask a question about the transcript.

        Args:
            question: Question to ask
            job_id: Job identifier

        Returns:
            Answer with sources
        """
        await self.initialize()

        try:
            if not self.qa_chain:
                await self.setup_qa_system("", job_id)  # Need to load from existing collection

            # Query the QA system
            result = self.qa_chain({"query": question})

            answer = result.get("result", "")
            sources = result.get("source_documents", [])

            # Format sources
            source_texts = []
            for doc in sources[:3]:  # Top 3 sources
                source_texts.append({
                    "text": doc.page_content,
                    "chunk_id": doc.metadata.get("chunk_id"),
                    "score": getattr(doc, 'score', None)
                })

            logger.info("Question answered", job_id=job_id, question_length=len(question))

            return {
                "answer": answer,
                "sources": source_texts,
                "confidence": 0.85  # Placeholder confidence score
            }

        except Exception as e:
            logger.error("Question answering failed", job_id=job_id, error=str(e))
            return {
                "answer": "Sorry, I couldn't answer that question.",
                "sources": [],
                "confidence": 0.0
            }

    async def index_arabic_knowledge_base(self, documents: List[str]) -> None:
        """
        Index a knowledge base of correct Arabic transcripts for better corrections.

        Args:
            documents: List of correct Arabic transcript documents
        """
        await self.initialize()

        try:
            collection_name = "arabic_kb"

            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )

            all_chunks = []
            for doc in documents:
                chunks = text_splitter.split_text(doc)
                all_chunks.extend(chunks)

            # Create documents
            kb_documents = [
                Document(
                    page_content=chunk,
                    metadata={"source": "knowledge_base", "chunk_id": i}
                )
                for i, chunk in enumerate(all_chunks)
            ]

            # Create vector store
            Chroma.from_documents(
                documents=kb_documents,
                embedding=self.embedding_function,
                collection_name=collection_name,
                client=self.chroma_client
            )

            logger.info("Arabic knowledge base indexed", documents=len(documents), chunks=len(all_chunks))

        except Exception as e:
            logger.error("Knowledge base indexing failed", error=str(e))
            raise

    def get_collection_stats(self, collection_name: str) -> Dict:
        """
        Get statistics about a vector collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection statistics
        """
        try:
            collection = self.chroma_client.get_collection(collection_name)
            count = collection.count()

            return {
                "collection_name": collection_name,
                "document_count": count,
                "status": "active"
            }

        except Exception as e:
            logger.error("Failed to get collection stats", collection=collection_name, error=str(e))
            return {
                "collection_name": collection_name,
                "document_count": 0,
                "status": "error",
                "error": str(e)
            }


# Global RAG service instance
rag_service = RAGService()