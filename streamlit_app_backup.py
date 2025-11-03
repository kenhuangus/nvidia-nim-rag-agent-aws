"""
Streamlit App for Testing NIM RAG Agent
Interactive interface to test the agentic RAG system with NVIDIA NIM
"""

import streamlit as st
import asyncio
from pathlib import Path
import sys
import os
from dotenv import load_dotenv

# Load .env file FIRST before anything else
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.nim_clients.llm_client import NIMClient
from src.nim_clients.embedding_client import NIMEmbeddingClient
from src.retrieval.vector_store import VectorStore
from src.retrieval.document_processor import DocumentProcessor
from src.agent.rag_agent import RAGAgent
from src.agent.tools import RetrievalTool, CalculatorTool
from src.utils.config import settings


# Page configuration
st.set_page_config(
    page_title="NIM RAG Agent Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #76B900;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stExpander {
        background-color: #f0f2f6;
        border-radius: 5px;
    }
    .reasoning-step {
        background-color: #e8f4f8;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_clients():
    """Initialize NIM clients (cached to avoid re-initialization)"""
    try:
        # Check if API key is set
        api_key = os.getenv("NIM_API_KEY")
        if not api_key or api_key == "your_nvidia_api_key_here":
            st.error("⚠️ Please set NIM_API_KEY in .env file with your actual NVIDIA API key")
            st.stop()

        llm_client = NIMClient(
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )

        embedding_client = NIMEmbeddingClient()

        return llm_client, embedding_client
    except Exception as e:
        st.error(f"Error initializing NIM clients: {e}")
        st.info("Make sure you have set NIM_API_KEY in your .env file")
        st.stop()


@st.cache_resource
def initialize_vector_store(_embedding_client):
    """Initialize vector store (cached)"""
    try:
        vector_store = VectorStore(
            embedding_client=_embedding_client,
            persist_dir=settings.chroma_persist_dir,
            collection_name=settings.collection_name
        )
        return vector_store
    except Exception as e:
        st.error(f"Error initializing vector store: {e}")
        st.stop()


@st.cache_resource
def initialize_agent(_llm_client, _vector_store):
    """Initialize RAG agent with tools (cached)"""
    try:
        # Create tools
        retrieval_tool = RetrievalTool(vector_store=_vector_store)
        calculator_tool = CalculatorTool()
        tools = [retrieval_tool, calculator_tool]

        # Create agent
        agent = RAGAgent(
            llm_client=_llm_client,
            tools=tools,
            max_iterations=settings.max_iterations
        )

        return agent
    except Exception as e:
        st.error(f"Error initializing agent: {e}")
        st.stop()


def add_sample_documents(vector_store):
    """Add sample documents to the vector store"""
    sample_docs = [
        {
            "text": "NVIDIA NIM is a set of accelerated inference microservices that allow organizations to run AI models anywhere. NIM supports multiple frameworks including PyTorch, TensorFlow, and ONNX.",
            "metadata": {"source": "nvidia_nim_overview.txt", "category": "technology"}
        },
        {
            "text": "The llama-3.1-nemotron-nano-8B model is a compact language model optimized for instruction following and dialogue. It features 8 billion parameters and is designed for efficient inference.",
            "metadata": {"source": "model_specs.txt", "category": "models"}
        },
        {
            "text": "Retrieval Augmented Generation (RAG) combines language models with document retrieval systems to provide more accurate and contextual responses. RAG systems fetch relevant documents before generating answers.",
            "metadata": {"source": "rag_explanation.txt", "category": "concepts"}
        },
        {
            "text": "AWS EKS (Elastic Kubernetes Service) is a managed Kubernetes service that makes it easy to run Kubernetes on AWS without needing to install and operate your own Kubernetes control plane.",
            "metadata": {"source": "aws_eks.txt", "category": "infrastructure"}
        },
        {
            "text": "Vector databases like ChromaDB enable semantic search by storing embeddings of documents. They allow finding similar content based on meaning rather than exact keyword matches.",
            "metadata": {"source": "vector_db.txt", "category": "technology"}
        }
    ]

    with st.spinner("Adding sample documents..."):
        try:
            documents = [doc["text"] for doc in sample_docs]
            metadatas = [doc["metadata"] for doc in sample_docs]
            asyncio.run(vector_store.add_documents(documents, metadatas))
            st.success(f"✅ Added {len(sample_docs)} sample documents to vector store!")
        except Exception as e:
            st.error(f"Error adding sample documents: {e}")


def process_uploaded_file(file, vector_store):
    """Process and add uploaded file to vector store"""
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.name}"
        with open(temp_path, "wb") as f:
            f.write(file.getbuffer())

        # Process file with custom chunk settings
        processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
        chunks = processor.process_file(temp_path)

        # Add to vector store
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]

        asyncio.run(vector_store.add_documents(documents, metadatas))

        # Clean up
        os.remove(temp_path)

        return len(chunks)
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return 0


def display_reasoning_process(result):
    """Display the agent's reasoning process"""
    # Display plan
    with st.expander("📋 Agent's Plan", expanded=True):
        st.markdown(f"```\n{result['plan']}\n```")

    # Display reasoning steps
    if result['reasoning_steps']:
        with st.expander("🧠 Reasoning Steps", expanded=True):
            for i, step in enumerate(result['reasoning_steps'], 1):
                st.markdown(f"**Step {i}:** `{step['action']}`")
                st.code(step['content'], language="text")

    # Display tool outputs
    if result['tool_outputs']:
        with st.expander("🔧 Tool Outputs", expanded=False):
            for i, output in enumerate(result['tool_outputs'], 1):
                st.markdown(f"**Tool Output {i}:**")
                st.text(output)


def main():
    # Header
    st.markdown('<div class="main-header">🤖 NVIDIA NIM RAG Agent Demo</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Intelligent Agentic RAG with llama-3.1-nemotron-nano-8B</div>', unsafe_allow_html=True)

    # Initialize components
    llm_client, embedding_client = initialize_clients()
    vector_store = initialize_vector_store(embedding_client)
    agent = initialize_agent(llm_client, vector_store)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Display current settings
        st.subheader("Current Settings")
        st.write(f"**Model:** {settings.nim_model}")
        st.write(f"**Embedding Model:** {settings.nim_embedding_model}")
        st.write(f"**Temperature:** {settings.temperature}")
        st.write(f"**Max Iterations:** {settings.max_iterations}")

        st.divider()

        # Vector store info
        st.subheader("📚 Vector Store")
        doc_count = vector_store.get_document_count()
        st.metric("Documents in Store", doc_count)

        # Add sample documents button
        if st.button("➕ Add Sample Documents", use_container_width=True):
            add_sample_documents(vector_store)
            st.rerun()

        # File upload
        st.subheader("📄 Upload Document")
        uploaded_file = st.file_uploader(
            "Upload a document to add to knowledge base",
            type=['txt', 'pdf', 'docx', 'md'],
            help="Supported formats: TXT, PDF, DOCX, Markdown"
        )

        if uploaded_file is not None:
            if st.button("Process & Add Document", use_container_width=True):
                with st.spinner("Processing document..."):
                    num_chunks = process_uploaded_file(uploaded_file, vector_store)
                    if num_chunks > 0:
                        st.success(f"✅ Added {num_chunks} chunks to vector store!")
                        st.rerun()

        st.divider()

        # Reset collection
        if st.button("🗑️ Clear All Documents", use_container_width=True):
            if st.checkbox("I confirm this action"):
                vector_store.reset_collection()
                st.success("✅ Collection cleared!")
                st.rerun()

    # Main content area
    st.header("💬 Chat with the Agent")

    # Initialize session state for chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Display reasoning for assistant messages
            if message["role"] == "assistant" and "reasoning" in message:
                display_reasoning_process(message["reasoning"])

    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Agent is thinking..."):
                try:
                    # Run agent
                    result = asyncio.run(agent.run(prompt))

                    # Display answer
                    st.markdown(result['answer'])

                    # Display reasoning process
                    display_reasoning_process(result)

                    # Add to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result['answer'],
                        "reasoning": result
                    })

                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>Powered by NVIDIA NIM | llama-3.1-nemotron-nano-8B | Built for AWS Hackathon</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
