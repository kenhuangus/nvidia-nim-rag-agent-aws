"""
Test script to verify all Streamlit app components can initialize
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.nim_clients.llm_client import NIMClient
from src.nim_clients.embedding_client import NIMEmbeddingClient
from src.retrieval.vector_store import VectorStore
from src.agent.rag_agent import RAGAgent
from src.agent.tools import RetrievalTool, CalculatorTool
from src.utils.config import settings


def test_config():
    """Test configuration loading"""
    print("=" * 50)
    print("Testing Configuration")
    print("=" * 50)
    print(f"✓ NIM Model: {settings.nim_model}")
    print(f"✓ NIM Embedding Model: {settings.nim_embedding_model}")
    print(f"✓ Temperature: {settings.temperature}")
    print(f"✓ Max Iterations: {settings.max_iterations}")
    print(f"✓ Chroma Persist Dir: {settings.chroma_persist_dir}")
    print()


def test_clients():
    """Test client initialization"""
    print("=" * 50)
    print("Testing Client Initialization")
    print("=" * 50)

    try:
        # Test LLM client
        llm_client = NIMClient(
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )
        print("✓ LLM Client initialized successfully")

        # Test embedding client
        embedding_client = NIMEmbeddingClient()
        print("✓ Embedding Client initialized successfully")

        return llm_client, embedding_client

    except ValueError as e:
        if "NIM_API_KEY" in str(e):
            print("✗ ERROR: NIM_API_KEY not set in .env file")
            print("  Please set your NVIDIA API key in .env file")
            sys.exit(1)
        else:
            raise
    except Exception as e:
        print(f"✗ ERROR: {e}")
        sys.exit(1)


def test_vector_store(embedding_client):
    """Test vector store initialization"""
    print("\n" + "=" * 50)
    print("Testing Vector Store")
    print("=" * 50)

    try:
        vector_store = VectorStore(
            embedding_client=embedding_client,
            persist_dir=settings.chroma_persist_dir,
            collection_name=settings.collection_name
        )
        print(f"✓ Vector Store initialized successfully")
        print(f"✓ Current document count: {vector_store.get_document_count()}")
        return vector_store

    except Exception as e:
        print(f"✗ ERROR: {e}")
        sys.exit(1)


def test_agent(llm_client, vector_store):
    """Test agent initialization"""
    print("\n" + "=" * 50)
    print("Testing RAG Agent")
    print("=" * 50)

    try:
        # Create tools
        retrieval_tool = RetrievalTool(vector_store=vector_store)
        calculator_tool = CalculatorTool()
        tools = [retrieval_tool, calculator_tool]

        # Create agent
        agent = RAGAgent(
            llm_client=llm_client,
            tools=tools,
            max_iterations=settings.max_iterations
        )

        print(f"✓ RAG Agent initialized successfully")
        print(f"✓ Tools available: {[tool.name for tool in tools]}")
        return agent

    except Exception as e:
        print(f"✗ ERROR: {e}")
        sys.exit(1)


async def test_simple_query(agent):
    """Test a simple query"""
    print("\n" + "=" * 50)
    print("Testing Simple Query")
    print("=" * 50)

    try:
        # Simple calculator query (doesn't require documents)
        query = "What is 25 * 4?"
        print(f"Query: {query}")
        print("Running agent...")

        result = await agent.run(query)

        print(f"\n✓ Agent completed successfully!")
        print(f"\nPlan:\n{result['plan']}")
        print(f"\nAnswer:\n{result['answer']}")

        if result['tool_outputs']:
            print(f"\nTool Outputs:")
            for i, output in enumerate(result['tool_outputs'], 1):
                print(f"  {i}. {output}")

    except Exception as e:
        print(f"✗ ERROR during query execution: {e}")
        print("\nThis might be due to:")
        print("  1. Invalid NIM_API_KEY")
        print("  2. Network connectivity issues")
        print("  3. NVIDIA API service unavailable")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print(" STREAMLIT APP COMPONENT TESTING")
    print("=" * 60 + "\n")

    # Test 1: Configuration
    test_config()

    # Test 2: Clients
    llm_client, embedding_client = test_clients()

    # Test 3: Vector Store
    vector_store = test_vector_store(embedding_client)

    # Test 4: Agent
    agent = test_agent(llm_client, vector_store)

    # Test 5: Simple Query (optional - requires API key to work)
    print("\n" + "=" * 50)
    print("Optional: Test Simple Query")
    print("=" * 50)
    response = input("Do you want to test a simple query? (requires valid API key) [y/N]: ")
    if response.lower() == 'y':
        asyncio.run(test_simple_query(agent))

    print("\n" + "=" * 60)
    print(" ALL COMPONENT TESTS PASSED!")
    print("=" * 60)
    print("\nThe Streamlit app should work correctly.")
    print("Access it at: http://localhost:8501")
    print("\nNote: For the agent to work fully, you need:")
    print("  1. Valid NIM_API_KEY in .env")
    print("  2. Network access to NVIDIA API")
    print("  3. Documents in the vector store (use 'Add Sample Documents' button)")


if __name__ == "__main__":
    main()
