"""
Unit tests for agent tools
"""

import pytest
from unittest.mock import AsyncMock, Mock
from src.agent.tools import RetrievalTool, CalculatorTool, get_tools_description


class TestRetrievalTool:
    """Tests for RetrievalTool"""

    @pytest.mark.asyncio
    async def test_retrieval_tool_basic(self):
        """Test basic retrieval tool functionality"""
        # Mock vector store
        mock_vector_store = Mock()
        mock_vector_store.similarity_search = AsyncMock(return_value=[
            {
                'document': 'Test document content',
                'metadata': {'source': 'test.txt'},
                'distance': 0.1
            }
        ])

        tool = RetrievalTool(mock_vector_store)

        assert tool.name == "retrieval"
        assert "knowledge base" in tool.description.lower()

        result = await tool.run("test query")

        assert "Retrieved documents" in result
        assert "Test document content" in result
        assert "test.txt" in result
        mock_vector_store.similarity_search.assert_called_once_with("test query", k=3)

    @pytest.mark.asyncio
    async def test_retrieval_tool_with_k(self):
        """Test retrieval tool with custom k parameter"""
        mock_vector_store = Mock()
        mock_vector_store.similarity_search = AsyncMock(return_value=[])

        tool = RetrievalTool(mock_vector_store)
        await tool.run("test query", k=5)

        mock_vector_store.similarity_search.assert_called_once_with("test query", k=5)

    @pytest.mark.asyncio
    async def test_retrieval_tool_no_results(self):
        """Test retrieval tool when no documents found"""
        mock_vector_store = Mock()
        mock_vector_store.similarity_search = AsyncMock(return_value=[])

        tool = RetrievalTool(mock_vector_store)
        result = await tool.run("test query")

        assert "No relevant documents found" in result

    @pytest.mark.asyncio
    async def test_retrieval_tool_multiple_results(self):
        """Test retrieval tool with multiple results"""
        mock_vector_store = Mock()
        mock_vector_store.similarity_search = AsyncMock(return_value=[
            {
                'document': 'Document 1',
                'metadata': {'source': 'file1.txt'},
                'distance': 0.1
            },
            {
                'document': 'Document 2',
                'metadata': {'source': 'file2.txt'},
                'distance': 0.2
            },
            {
                'document': 'Document 3',
                'metadata': {},
                'distance': 0.3
            }
        ])

        tool = RetrievalTool(mock_vector_store)
        result = await tool.run("test query")

        assert "Document 1:" in result
        assert "Document 2:" in result
        assert "Document 3:" in result
        assert "file1.txt" in result
        assert "file2.txt" in result

    @pytest.mark.asyncio
    async def test_retrieval_tool_error_handling(self):
        """Test retrieval tool error handling"""
        mock_vector_store = Mock()
        mock_vector_store.similarity_search = AsyncMock(side_effect=Exception("Search error"))

        tool = RetrievalTool(mock_vector_store)
        result = await tool.run("test query")

        assert "Error retrieving documents" in result


class TestCalculatorTool:
    """Tests for CalculatorTool"""

    @pytest.mark.asyncio
    async def test_calculator_basic_addition(self):
        """Test basic addition"""
        tool = CalculatorTool()

        assert tool.name == "calculator"
        assert "mathematical" in tool.description.lower()

        result = await tool.run("2 + 2")
        assert "Result: 4" in result

    @pytest.mark.asyncio
    async def test_calculator_multiplication(self):
        """Test multiplication"""
        tool = CalculatorTool()
        result = await tool.run("5 * 10")
        assert "Result: 50" in result

    @pytest.mark.asyncio
    async def test_calculator_division(self):
        """Test division"""
        tool = CalculatorTool()
        result = await tool.run("10 / 2")
        assert "Result: 5" in result

    @pytest.mark.asyncio
    async def test_calculator_complex_expression(self):
        """Test complex expression"""
        tool = CalculatorTool()
        result = await tool.run("(10 + 5) * 2")
        assert "Result: 30" in result

    @pytest.mark.asyncio
    async def test_calculator_error_invalid_expression(self):
        """Test calculator with invalid expression"""
        tool = CalculatorTool()
        result = await tool.run("invalid expression")
        assert "Error calculating" in result

    @pytest.mark.asyncio
    async def test_calculator_error_unsafe_code(self):
        """Test calculator rejects unsafe code execution"""
        tool = CalculatorTool()
        # This should fail because __builtins__ is restricted
        result = await tool.run("__import__('os').system('ls')")
        assert "Error calculating" in result


class TestGetToolsDescription:
    """Tests for get_tools_description helper"""

    def test_get_tools_description_empty(self):
        """Test with no tools"""
        result = get_tools_description([])
        assert "You have access to the following tools" in result

    def test_get_tools_description_single_tool(self):
        """Test with single tool"""
        tool = Mock()
        tool.name = "test_tool"
        tool.description = "   Test tool description   "

        result = get_tools_description([tool])

        assert "You have access to the following tools" in result
        assert "test_tool" in result
        assert "Test tool description" in result

    def test_get_tools_description_multiple_tools(self):
        """Test with multiple tools"""
        tool1 = Mock()
        tool1.name = "tool1"
        tool1.description = "First tool"

        tool2 = Mock()
        tool2.name = "tool2"
        tool2.description = "Second tool"

        result = get_tools_description([tool1, tool2])

        assert "tool1" in result
        assert "tool2" in result
        assert "First tool" in result
        assert "Second tool" in result

    def test_get_tools_description_with_real_tools(self):
        """Test with real tool instances"""
        mock_vector_store = Mock()
        retrieval_tool = RetrievalTool(mock_vector_store)
        calculator_tool = CalculatorTool()

        result = get_tools_description([retrieval_tool, calculator_tool])

        assert "retrieval" in result
        assert "calculator" in result
        assert "knowledge base" in result.lower()
        assert "mathematical" in result.lower()
