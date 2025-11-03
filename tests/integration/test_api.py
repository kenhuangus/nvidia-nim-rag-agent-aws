"""
Integration tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock, patch


@pytest.fixture
def mock_llm_client():
    """Mock LLM client"""
    mock = AsyncMock()
    mock.generate.return_value = "Test response"
    mock.generate_with_system.return_value = "Test plan"
    return mock


@pytest.fixture
def mock_embedding_client():
    """Mock embedding client"""
    mock = AsyncMock()
    mock.embed_text.return_value = [0.1] * 384
    mock.embed_texts.return_value = [[0.1] * 384]
    return mock


@pytest.fixture
def mock_vector_store(mock_embedding_client):
    """Mock vector store"""
    mock = Mock()
    mock.get_document_count.return_value = 10
    mock.add_documents = AsyncMock(return_value=["doc_1"])
    mock.similarity_search = AsyncMock(return_value=[
        {
            'id': 'doc_1',
            'document': 'Test document',
            'metadata': {'source': 'test.txt'},
            'distance': 0.5
        }
    ])
    return mock


@pytest.fixture
def client(mock_llm_client, mock_embedding_client, mock_vector_store):
    """Create test client with mocked dependencies"""
    with patch('src.api.main.llm_client', mock_llm_client), \
         patch('src.api.main.embedding_client', mock_embedding_client), \
         patch('src.api.main.vector_store', mock_vector_store), \
         patch('src.api.main.agent') as mock_agent:

        # Mock agent
        mock_agent.run = AsyncMock(return_value={
            'answer': 'Test answer',
            'plan': 'Test plan',
            'tool_outputs': ['Tool output 1'],
            'reasoning_steps': [{'action': 'answer', 'content': 'Test'}]
        })
        mock_agent.run_simple = AsyncMock(return_value='Test answer')

        from src.api.main import app
        with TestClient(app) as test_client:
            yield test_client


def test_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    # Root serves frontend HTML or JSON fallback
    assert response.status_code == 200


def test_health(client):
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert 'vector_store_docs' in data


def test_query_agent(client):
    """Test query endpoint"""
    response = client.post(
        "/query",
        json={"query": "What is machine learning?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'answer' in data
    assert 'plan' in data
    assert 'tool_outputs' in data
    assert 'reasoning_steps' in data


def test_query_simple(client):
    """Test simple query endpoint"""
    response = client.post(
        "/query/simple",
        json={"query": "What is AI?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'answer' in data


def test_ingest_document(client):
    """Test document ingestion endpoint"""
    response = client.post(
        "/documents/ingest",
        json={
            "text": "This is a test document.",
            "metadata": {"source": "test"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert 'message' in data
    assert 'document_id' in data
    assert 'total_documents' in data


def test_get_document_count(client):
    """Test document count endpoint"""
    response = client.get("/documents/count")
    assert response.status_code == 200
    data = response.json()
    assert 'count' in data


def test_search_documents(client):
    """Test document search endpoint"""
    response = client.post(
        "/documents/search?query=test&k=5"
    )
    assert response.status_code == 200
    data = response.json()
    assert 'results' in data
