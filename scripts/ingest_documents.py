"""
Script to ingest documents into the vector store
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nim_clients.embedding_client import NIMEmbeddingClient
from src.retrieval.vector_store import VectorStore
from src.retrieval.document_processor import DocumentProcessor
from src.utils.config import settings
from loguru import logger


async def ingest_directory(directory_path: str, file_pattern: str = "*.*"):
    """
    Ingest all documents from a directory

    Args:
        directory_path: Path to directory containing documents
        file_pattern: Glob pattern for files to process
    """
    logger.info(f"Initializing ingestion from {directory_path}")

    # Initialize clients
    embedding_client = NIMEmbeddingClient(
        api_key=settings.nim_api_key,
        base_url=settings.nim_inference_url,
        model=settings.nim_embedding_model,
    )

    # Initialize vector store
    vector_store = VectorStore(
        embedding_client=embedding_client,
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.collection_name,
    )

    # Initialize document processor
    document_processor = DocumentProcessor()

    # Process directory
    logger.info("Processing documents...")
    processed_chunks = document_processor.process_directory(directory_path, file_pattern)

    if not processed_chunks:
        logger.warning("No documents found to process")
        return

    logger.info(f"Processed {len(processed_chunks)} chunks from documents")

    # Extract texts and metadatas
    texts = [chunk['text'] for chunk in processed_chunks]
    metadatas = [chunk['metadata'] for chunk in processed_chunks]

    # Ingest into vector store
    logger.info("Ingesting into vector store...")
    ids = await vector_store.add_documents(texts, metadatas)

    logger.info(f"Successfully ingested {len(ids)} document chunks")
    logger.info(f"Total documents in store: {vector_store.get_document_count()}")


async def ingest_text(text: str, metadata: dict = None):
    """
    Ingest a single text

    Args:
        text: Text to ingest
        metadata: Optional metadata
    """
    logger.info("Initializing ingestion for text")

    # Initialize clients
    embedding_client = NIMEmbeddingClient(
        api_key=settings.nim_api_key,
        base_url=settings.nim_inference_url,
        model=settings.nim_embedding_model,
    )

    # Initialize vector store
    vector_store = VectorStore(
        embedding_client=embedding_client,
        persist_dir=settings.chroma_persist_dir,
        collection_name=settings.collection_name,
    )

    # Initialize document processor
    document_processor = DocumentProcessor()

    # Chunk text
    chunks = document_processor.chunk_text(text)
    logger.info(f"Split text into {len(chunks)} chunks")

    # Add metadata to chunks
    metadatas = [metadata or {} for _ in chunks]

    # Ingest into vector store
    logger.info("Ingesting into vector store...")
    ids = await vector_store.add_documents(chunks, metadatas)

    logger.info(f"Successfully ingested {len(ids)} chunks")
    logger.info(f"Total documents in store: {vector_store.get_document_count()}")


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest documents into vector store")
    parser.add_argument("--directory", "-d", help="Directory path to ingest")
    parser.add_argument("--pattern", "-p", default="*.*", help="File pattern (default: *.*)")
    parser.add_argument("--text", "-t", help="Text to ingest")
    parser.add_argument("--source", "-s", help="Source name for text metadata")

    args = parser.parse_args()

    if args.directory:
        await ingest_directory(args.directory, args.pattern)
    elif args.text:
        metadata = {"source": args.source} if args.source else None
        await ingest_text(args.text, metadata)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
