"""
NVIDIA NIM Embedding Client
Uses OpenAI-compatible API for embeddings
"""

from typing import List, Union, Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
import os


class NIMEmbeddingClient:
    """Client for NVIDIA NIM Embedding inference"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize NIM Embedding client

        Args:
            api_key: NVIDIA API key
            base_url: NIM embedding endpoint URL
            model: Embedding model name (default: nvidia/nv-embedqa-e5-v5)
        """
        self.api_key = api_key or os.getenv("NIM_API_KEY")
        self.base_url = base_url or os.getenv("NIM_INFERENCE_URL", "https://integrate.api.nvidia.com/v1")
        self.model = model or os.getenv("NIM_EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5")

        if not self.api_key:
            raise ValueError("NIM_API_KEY must be provided or set in environment")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        logger.info(f"Initialized NIM Embedding client with model: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def embed_text(self, text: str, input_type: str = "query") -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed
            input_type: Type of input - "query" for queries, "passage" for documents

        Returns:
            Embedding vector as list of floats
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float",
                extra_body={"input_type": input_type}
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of dimension: {len(embedding)} with input_type: {input_type}")
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def embed_texts(self, texts: List[str], input_type: str = "passage") -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed
            input_type: Type of input - "query" for queries, "passage" for documents

        Returns:
            List of embedding vectors
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float",
                extra_body={"input_type": input_type}
            )

            embeddings = [item.embedding for item in response.data]
            logger.debug(f"Generated {len(embeddings)} embeddings with input_type: {input_type}")
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query (uses input_type="query")

        Args:
            query: Query text to embed

        Returns:
            Embedding vector as list of floats
        """
        return await self.embed_text(query, input_type="query")

    async def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents (uses input_type="passage")

        Args:
            documents: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        return await self.embed_texts(documents, input_type="passage")
