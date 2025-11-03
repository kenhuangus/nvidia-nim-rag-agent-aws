"""
Unit tests for Vector Store
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.retrieval.vector_store import VectorStore


@pytest.fixture
def mock_embedding_client():
    """Mock embedding client"""
    client = AsyncMock()
    client.embed_text = AsyncMock(return_value=[0.1] * 384)
    client.embed_texts = AsyncMock(return_value=[[0.1] * 384, [0.2] * 384])
    client.embed_query = AsyncMock(return_value=[0.1] * 384)
    client.embed_documents = AsyncMock(return_value=[[0.1] * 384, [0.2] * 384])
    return client


def create_mock_chroma_client():
    """Create a mock ChromaDB client"""
    client = Mock()
    collection = Mock()
    collection.count = Mock(return_value=0)
    collection.add = Mock()
    collection.query = Mock(return_value={
        'ids': [['doc_0', 'doc_1']],
        'documents': [['Document 1', 'Document 2']],
        'metadatas': [[{'source': 'test1.txt'}, {'source': 'test2.txt'}]],
        'distances': [[0.1, 0.2]]
    })
    collection.delete = Mock()

    client.get_or_create_collection = Mock(return_value=collection)
    client.create_collection = Mock(return_value=collection)
    client.delete_collection = Mock()

    return client, collection


class TestVectorStore:
    """Tests for VectorStore"""

    @patch('src.retrieval.vector_store.chromadb.PersistentClient')
    @patch('src.retrieval.vector_store.Path')
    def test_init(self, mock_path, mock_chroma, mock_embedding_client):
        """Test vector store initialization"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path.return_value = mock_path_instance

        mock_chroma_instance, mock_collection = create_mock_chroma_client()
        mock_chroma.return_value = mock_chroma_instance

        store = VectorStore(
            embedding_client=mock_embedding_client,
            persist_dir="./test_data",
            collection_name="test_collection"
        )

        assert store.persist_dir == "./test_data"
        assert store.collection_name == "test_collection"
        mock_chroma.assert_called_once()
        mock_chroma_instance.get_or_create_collection.assert_called_once()

    @patch('src.retrieval.vector_store.chromadb.PersistentClient')
    @patch('src.retrieval.vector_store.Path')
    @pytest.mark.asyncio
    async def test_add_documents(self, mock_path, mock_chroma, mock_embedding_client):
        """Test adding documents to vector store"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path.return_value = mock_path_instance

        mock_chroma_instance, mock_collection = create_mock_chroma_client()
        mock_chroma.return_value = mock_chroma_instance

        store = VectorStore(
            embedding_client=mock_embedding_client,
            persist_dir="./test_data"
        )

        documents = ["Doc 1", "Doc 2"]
        metadatas = [{"source": "file1.txt"}, {"source": "file2.txt"}]

        ids = await store.add_documents(documents, metadatas)

        assert len(ids) == 2
        assert ids[0] == "doc_0"
        assert ids[1] == "doc_1"

        mock_embedding_client.embed_documents.assert_called_once_with(documents)
        mock_collection.add.assert_called_once()

    @patch('src.retrieval.vector_store.chromadb.PersistentClient')
    @patch('src.retrieval.vector_store.Path')
    @pytest.mark.asyncio
    async def test_add_documents_with_custom_ids(self, mock_path, mock_chroma, mock_embedding_client):
        """Test adding documents with custom IDs"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path.return_value = mock_path_instance

        mock_chroma_instance, mock_collection = create_mock_chroma_client()
        mock_chroma.return_value = mock_chroma_instance

        store = VectorStore(
            embedding_client=mock_embedding_client,
            persist_dir="./test_data"
        )

        documents = ["Doc 1"]
        custom_ids = ["custom_id_1"]

        ids = await store.add_documents(documents, ids=custom_ids)

        assert ids == custom_ids
        call_args = mock_collection.add.call_args
        assert call_args.kwargs['ids'] == custom_ids

    @patch('src.retrieval.vector_store.chromadb.PersistentClient')
    @patch('src.retrieval.vector_store.Path')
    @pytest.mark.asyncio
    async def test_similarity_search(self, mock_path, mock_chroma, mock_embedding_client):
        """Test similarity search"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path.return_value = mock_path_instance

        mock_chroma_instance, mock_collection = create_mock_chroma_client()
        mock_chroma.return_value = mock_chroma_instance

        store = VectorStore(
            embedding_client=mock_embedding_client,
            persist_dir="./test_data"
        )

        results = await store.similarity_search("test query", k=2)

        assert len(results) == 2
        assert results[0]['id'] == 'doc_0'
        assert results[0]['document'] == 'Document 1'
        assert results[0]['metadata']['source'] == 'test1.txt'
        assert results[0]['distance'] == 0.1

        mock_embedding_client.embed_query.assert_called_once_with("test query")
        mock_collection.query.assert_called_once()

    @patch('src.retrieval.vector_store.chromadb.PersistentClient')
    @patch('src.retrieval.vector_store.Path')
    @pytest.mark.asyncio
    async def test_similarity_search_no_results(self, mock_path, mock_chroma, mock_embedding_client):
        """Test similarity search with no results"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path.return_value = mock_path_instance

        mock_chroma_instance, mock_collection = create_mock_chroma_client()
        mock_collection.query = Mock(return_value={
            'ids': [[]],
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        })
        mock_chroma.return_value = mock_chroma_instance

        store = VectorStore(
            embedding_client=mock_embedding_client,
            persist_dir="./test_data"
        )

        results = await store.similarity_search("test query")

        assert len(results) == 0

    @patch('src.retrieval.vector_store.chromadb.PersistentClient')
    @patch('src.retrieval.vector_store.Path')
    def test_get_document_count(self, mock_path, mock_chroma, mock_embedding_client):
        """Test getting document count"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path.return_value = mock_path_instance

        mock_chroma_instance, mock_collection = create_mock_chroma_client()
        mock_collection.count = Mock(return_value=42)
        mock_chroma.return_value = mock_chroma_instance

        store = VectorStore(
            embedding_client=mock_embedding_client,
            persist_dir="./test_data"
        )

        count = store.get_document_count()
        assert count == 42

    @patch('src.retrieval.vector_store.chromadb.PersistentClient')
    @patch('src.retrieval.vector_store.Path')
    def test_delete_documents(self, mock_path, mock_chroma, mock_embedding_client):
        """Test deleting documents"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path.return_value = mock_path_instance

        mock_chroma_instance, mock_collection = create_mock_chroma_client()
        mock_chroma.return_value = mock_chroma_instance

        store = VectorStore(
            embedding_client=mock_embedding_client,
            persist_dir="./test_data"
        )

        ids_to_delete = ["doc_1", "doc_2"]
        store.delete_documents(ids_to_delete)

        mock_collection.delete.assert_called_once_with(ids=ids_to_delete)

    @patch('src.retrieval.vector_store.chromadb.PersistentClient')
    @patch('src.retrieval.vector_store.Path')
    def test_reset_collection(self, mock_path, mock_chroma, mock_embedding_client):
        """Test resetting collection"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path.return_value = mock_path_instance

        mock_chroma_instance, mock_collection = create_mock_chroma_client()
        mock_chroma.return_value = mock_chroma_instance

        store = VectorStore(
            embedding_client=mock_embedding_client,
            persist_dir="./test_data",
            collection_name="test_collection"
        )

        store.reset_collection()

        mock_chroma_instance.delete_collection.assert_called_once_with(name="test_collection")
        mock_chroma_instance.create_collection.assert_called_once()

    @patch('src.retrieval.vector_store.chromadb.PersistentClient')
    @patch('src.retrieval.vector_store.Path')
    @pytest.mark.asyncio
    async def test_add_document_single(self, mock_path, mock_chroma, mock_embedding_client):
        """Test adding a single document"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path.return_value = mock_path_instance

        mock_chroma_instance, mock_collection = create_mock_chroma_client()
        mock_chroma.return_value = mock_chroma_instance

        store = VectorStore(
            embedding_client=mock_embedding_client,
            persist_dir="./test_data"
        )

        doc_id = await store.add_document(
            document="Single document",
            metadata={"source": "test.txt"},
            doc_id="custom_1"
        )

        assert doc_id == "custom_1"
        mock_collection.add.assert_called_once()

    @patch('src.retrieval.vector_store.chromadb.PersistentClient')
    @patch('src.retrieval.vector_store.Path')
    @pytest.mark.asyncio
    async def test_add_documents_error_handling(self, mock_path, mock_chroma, mock_embedding_client):
        """Test error handling in add_documents"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path.return_value = mock_path_instance

        mock_chroma_instance, mock_collection = create_mock_chroma_client()
        mock_chroma.return_value = mock_chroma_instance

        # Make embedding fail
        mock_embedding_client.embed_documents = AsyncMock(side_effect=Exception("Embedding error"))

        store = VectorStore(
            embedding_client=mock_embedding_client,
            persist_dir="./test_data"
        )

        with pytest.raises(Exception, match="Embedding error"):
            await store.add_documents(["Doc 1"])

    @patch('src.retrieval.vector_store.chromadb.PersistentClient')
    @patch('src.retrieval.vector_store.Path')
    @pytest.mark.asyncio
    async def test_similarity_search_error_handling(self, mock_path, mock_chroma, mock_embedding_client):
        """Test error handling in similarity search"""
        mock_path_instance = Mock()
        mock_path_instance.mkdir = Mock()
        mock_path.return_value = mock_path_instance

        mock_chroma_instance, mock_collection = create_mock_chroma_client()
        mock_chroma.return_value = mock_chroma_instance

        # Make query fail
        mock_embedding_client.embed_query = AsyncMock(side_effect=Exception("Query error"))

        store = VectorStore(
            embedding_client=mock_embedding_client,
            persist_dir="./test_data"
        )

        with pytest.raises(Exception, match="Query error"):
            await store.similarity_search("test")
