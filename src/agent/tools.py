"""
Tools for the agent to use
"""

from typing import Dict, Any, List
from loguru import logger

from src.retrieval.vector_store import VectorStore


class RetrievalTool:
    """Tool for retrieving relevant documents from vector store"""

    def __init__(self, vector_store: VectorStore):
        """
        Initialize retrieval tool

        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store
        self.name = "retrieval"
        self.description = """
        Retrieve relevant documents from the knowledge base.
        Use this tool to find information that can help answer the user's question.
        Input should be a search query string.
        Returns a list of relevant document excerpts with metadata.
        """

    async def run(self, query: str, k: int = 3) -> str:
        """
        Execute retrieval

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            Formatted string with retrieved documents
        """
        try:
            logger.info(f"Retrieval tool called with query: {query}")

            results = await self.vector_store.similarity_search(query, k=k)

            if not results:
                return "No relevant documents found."

            # Format results
            formatted = "Retrieved documents:\n\n"
            for i, result in enumerate(results, 1):
                formatted += f"Document {i}:\n"
                formatted += f"{result['document']}\n"
                if result['metadata']:
                    formatted += f"Source: {result['metadata'].get('source', 'Unknown')}\n"
                formatted += "\n"

            return formatted

        except Exception as e:
            logger.error(f"Error in retrieval tool: {e}")
            return f"Error retrieving documents: {str(e)}"


class CalculatorTool:
    """Simple calculator tool for demonstrations"""

    def __init__(self):
        self.name = "calculator"
        self.description = """
        Perform basic mathematical calculations.
        Input should be a mathematical expression as a string (e.g., "2 + 2" or "10 * 5").
        Returns the result of the calculation.
        """

    async def run(self, expression: str) -> str:
        """
        Execute calculation

        Args:
            expression: Mathematical expression

        Returns:
            Calculation result
        """
        try:
            logger.info(f"Calculator tool called with expression: {expression}")

            # Evaluate safely (limited to basic arithmetic)
            result = eval(expression, {"__builtins__": {}}, {})
            return f"Result: {result}"

        except Exception as e:
            logger.error(f"Error in calculator tool: {e}")
            return f"Error calculating: {str(e)}"


def get_tools_description(tools: List[Any]) -> str:
    """
    Get formatted description of available tools

    Args:
        tools: List of tool instances

    Returns:
        Formatted string describing all tools
    """
    description = "You have access to the following tools:\n\n"
    for tool in tools:
        description += f"- {tool.name}: {tool.description.strip()}\n\n"
    return description
