"""
Vector Store using ChromaDB with NVIDIA NIM Embeddings
"""

from typing import List, Dict, Optional, Tuple
import chromadb
from chromadb.config import Settings
from loguru import logger
import os
from pathlib import Path

from src.nim_clients.embedding_client import NIMEmbeddingClient


class VectorStore:
    """Vector store for document retrieval using ChromaDB"""

    def __init__(
        self,
        embedding_client: NIMEmbeddingClient,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        """
        Initialize vector store

        Args:
            embedding_client: NIM embedding client for generating embeddings
            persist_dir: Directory to persist ChromaDB data
            collection_name: Name of the collection
        """
        self.embedding_client = embedding_client
        self.persist_dir = persist_dir or os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "documents")

        # Ensure persist directory exists
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(f"Initialized vector store with collection: {self.collection_name}")
        logger.info(f"Current document count: {self.collection.count()}")

    async def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add documents to the vector store

        Args:
            documents: List of document texts
            metadatas: Optional list of metadata dicts for each document
            ids: Optional list of IDs for each document

        Returns:
            List of document IDs
        """
        try:
            # Generate embeddings using NIM
            embeddings = await self.embedding_client.embed_documents(documents)

            # Generate IDs if not provided
            if ids is None:
                existing_count = self.collection.count()
                ids = [f"doc_{existing_count + i}" for i in range(len(documents))]

            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(f"Added {len(documents)} documents to vector store")
            return ids

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Search for similar documents

        Args:
            query: Query text
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of result dicts with 'id', 'document', 'metadata', and 'distance'
        """
        try:
            # Generate query embedding using NIM
            query_embedding = await self.embedding_client.embed_query(query)

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter,
            )

            # Format results
            formatted_results = []
            if results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None,
                    })

            logger.debug(f"Found {len(formatted_results)} similar documents")
            return formatted_results

        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            raise

    def get_document_count(self) -> int:
        """Get the number of documents in the collection"""
        return self.collection.count()

    def get_all_documents(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all documents from the collection

        Args:
            limit: Optional limit on number of documents to return

        Returns:
            List of document dicts with 'id', 'document', and 'metadata'
        """
        try:
            # Get all documents from ChromaDB
            results = self.collection.get(
                limit=limit,
                include=['documents', 'metadatas']
            )

            # Format results
            formatted_results = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    formatted_results.append({
                        'id': results['ids'][i],
                        'document': results['documents'][i] if results['documents'] else '',
                        'metadata': results['metadatas'][i] if results['metadatas'] else {},
                    })

            logger.debug(f"Retrieved {len(formatted_results)} documents")
            return formatted_results

        except Exception as e:
            logger.error(f"Error getting all documents: {e}")
            raise

    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by IDs

        Args:
            ids: List of document IDs to delete
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise

    def reset_collection(self) -> None:
        """Reset the collection (delete all documents)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Reset collection")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise

    async def add_document(
        self,
        document: str,
        metadata: Optional[Dict] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """
        Add a single document to the vector store

        Args:
            document: Document text
            metadata: Optional metadata dict
            doc_id: Optional document ID

        Returns:
            Document ID
        """
        ids = await self.add_documents(
            documents=[document],
            metadatas=[metadata] if metadata else None,
            ids=[doc_id] if doc_id else None,
        )
        return ids[0]
