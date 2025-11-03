"""
Unit tests for NIM clients (LLM and Embedding)
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from src.nim_clients.llm_client import NIMClient
from src.nim_clients.embedding_client import NIMEmbeddingClient


class TestNIMClient:
    """Tests for NIM LLM Client"""

    def test_init_with_api_key(self):
        """Test initialization with provided API key"""
        client = NIMClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.model == "llama-3.1-nemotron-nano-8b-instruct"
        assert client.temperature == 0.7
        assert client.max_tokens == 2048

    def test_init_without_api_key(self):
        """Test initialization without API key raises error"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="NIM_API_KEY must be provided"):
                NIMClient()

    @pytest.mark.asyncio
    async def test_generate(self):
        """Test generate method"""
        with patch('src.nim_clients.llm_client.AsyncOpenAI') as mock_openai:
            # Setup mock
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Test response"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            # Create client and test
            client = NIMClient(api_key="test_key")
            messages = [{"role": "user", "content": "Hello"}]
            response = await client.generate(messages)

            assert response == "Test response"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_override_params(self):
        """Test generate with temperature and max_tokens overrides"""
        with patch('src.nim_clients.llm_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Test response"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            client = NIMClient(api_key="test_key")
            messages = [{"role": "user", "content": "Hello"}]
            await client.generate(messages, temperature=0.5, max_tokens=1024)

            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs['temperature'] == 0.5
            assert call_args.kwargs['max_tokens'] == 1024

    @pytest.mark.asyncio
    async def test_generate_error_handling(self):
        """Test error handling in generate"""
        with patch('src.nim_clients.llm_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
            mock_openai.return_value = mock_client

            client = NIMClient(api_key="test_key")
            messages = [{"role": "user", "content": "Hello"}]

            with pytest.raises(Exception, match="API Error"):
                await client.generate(messages)

    @pytest.mark.asyncio
    async def test_generate_stream(self):
        """Test streaming generation"""
        with patch('src.nim_clients.llm_client.AsyncOpenAI') as mock_openai:
            # Setup mock stream
            mock_client = AsyncMock()

            async def mock_stream():
                chunks = ["Hello", " ", "world"]
                for text in chunks:
                    chunk = Mock()
                    chunk.choices = [Mock()]
                    chunk.choices[0].delta.content = text
                    yield chunk

            mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
            mock_openai.return_value = mock_client

            client = NIMClient(api_key="test_key")
            messages = [{"role": "user", "content": "Hello"}]

            result = []
            async for chunk in client.generate_stream(messages):
                result.append(chunk)

            assert result == ["Hello", " ", "world"]

    @pytest.mark.asyncio
    async def test_generate_with_system(self):
        """Test generate_with_system helper method"""
        with patch('src.nim_clients.llm_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Test response"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            client = NIMClient(api_key="test_key")
            response = await client.generate_with_system(
                system_prompt="You are helpful",
                user_message="Hello"
            )

            assert response == "Test response"
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs['messages']
            assert len(messages) == 2
            assert messages[0]['role'] == 'system'
            assert messages[1]['role'] == 'user'


class TestNIMEmbeddingClient:
    """Tests for NIM Embedding Client"""

    def test_init_with_api_key(self):
        """Test initialization with provided API key"""
        client = NIMEmbeddingClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.model == "nvidia/nv-embedqa-e5-v5"

    def test_init_without_api_key(self):
        """Test initialization without API key raises error"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="NIM_API_KEY must be provided"):
                NIMEmbeddingClient()

    @pytest.mark.asyncio
    async def test_embed_text(self):
        """Test embed_text method"""
        with patch('src.nim_clients.embedding_client.AsyncOpenAI') as mock_openai:
            # Setup mock
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.data = [Mock()]
            mock_response.data[0].embedding = [0.1, 0.2, 0.3]
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            # Create client and test
            client = NIMEmbeddingClient(api_key="test_key")
            embedding = await client.embed_text("Hello world")

            assert embedding == [0.1, 0.2, 0.3]
            mock_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_embed_texts(self):
        """Test embed_texts method for multiple texts"""
        with patch('src.nim_clients.embedding_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.data = [Mock(), Mock()]
            mock_response.data[0].embedding = [0.1, 0.2, 0.3]
            mock_response.data[1].embedding = [0.4, 0.5, 0.6]
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            client = NIMEmbeddingClient(api_key="test_key")
            embeddings = await client.embed_texts(["Hello", "World"])

            assert len(embeddings) == 2
            assert embeddings[0] == [0.1, 0.2, 0.3]
            assert embeddings[1] == [0.4, 0.5, 0.6]

    @pytest.mark.asyncio
    async def test_embed_query(self):
        """Test embed_query alias method"""
        with patch('src.nim_clients.embedding_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.data = [Mock()]
            mock_response.data[0].embedding = [0.1, 0.2, 0.3]
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            client = NIMEmbeddingClient(api_key="test_key")
            embedding = await client.embed_query("test query")

            assert embedding == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_embed_documents(self):
        """Test embed_documents alias method"""
        with patch('src.nim_clients.embedding_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.data = [Mock()]
            mock_response.data[0].embedding = [0.1, 0.2, 0.3]
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_client

            client = NIMEmbeddingClient(api_key="test_key")
            embeddings = await client.embed_documents(["doc1"])

            assert len(embeddings) == 1
            assert embeddings[0] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_embed_text_error_handling(self):
        """Test error handling in embed_text"""
        with patch('src.nim_clients.embedding_client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(side_effect=Exception("API Error"))
            mock_openai.return_value = mock_client

            client = NIMEmbeddingClient(api_key="test_key")

            with pytest.raises(Exception, match="API Error"):
                await client.embed_text("test")
