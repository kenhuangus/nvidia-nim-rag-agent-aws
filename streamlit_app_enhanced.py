"""
Enhanced Streamlit App for Testing NIM RAG Agent
Features: Document viewer, API call logging, detailed agent reasoning
"""

import streamlit as st
import asyncio
from pathlib import Path
import sys
import os
from dotenv import load_dotenv
from datetime import datetime
import json
from collections import defaultdict

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
    page_title="NIM RAG Agent Demo - Enhanced",
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
    .api-call {
        background-color: #fff3cd;
        padding: 8px;
        border-left: 3px solid #ff6b35;
        margin: 5px 0;
        border-radius: 3px;
        font-family: monospace;
        font-size: 0.85em;
    }
    .doc-preview {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #76B900;
        margin: 5px 0;
        max-height: 150px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state for API call logging
if 'api_calls' not in st.session_state:
    st.session_state.api_calls = []

if 'enable_api_logging' not in st.session_state:
    st.session_state.enable_api_logging = True


def log_api_call(api_type, endpoint, params, response=None, error=None):
    """Log an API call with timestamp"""
    if not st.session_state.enable_api_logging:
        return

    call_info = {
        'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
        'type': api_type,
        'endpoint': endpoint,
        'params': params,
        'response': response,
        'error': error,
        'status': 'error' if error else 'success'
    }
    st.session_state.api_calls.append(call_info)


@st.cache_resource
def initialize_clients():
    """Initialize NIM clients (cached to avoid re-initialization)"""
    try:
        # Check if API key is set
        api_key = os.getenv("NIM_API_KEY")
        if not api_key or api_key == "your_nvidia_api_key_here":
            st.error("⚠️ Please set NIM_API_KEY in .env file with your actual NVIDIA API key")
            st.stop()

        log_api_call("INIT", "NIM LLM Client", {"model": settings.nim_model})
        llm_client = NIMClient(
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )

        log_api_call("INIT", "NIM Embedding Client", {"model": settings.nim_embedding_model})
        embedding_client = NIMEmbeddingClient()

        return llm_client, embedding_client
    except Exception as e:
        log_api_call("INIT", "Client Initialization", {}, error=str(e))
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
        log_api_call("INIT", "Vector Store", {
            "collection": settings.collection_name,
            "doc_count": vector_store.get_document_count()
        })
        return vector_store
    except Exception as e:
        log_api_call("INIT", "Vector Store", {}, error=str(e))
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

        log_api_call("INIT", "RAG Agent", {
            "tools": len(tools),
            "max_iterations": settings.max_iterations
        })
        return agent
    except Exception as e:
        log_api_call("INIT", "RAG Agent", {}, error=str(e))
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

            log_api_call("EMBEDDING", "embed_documents", {
                "count": len(documents),
                "type": "sample_docs"
            })
            asyncio.run(vector_store.add_documents(documents, metadatas))

            log_api_call("VECTOR_STORE", "add_documents", {
                "count": len(documents),
                "type": "sample_docs"
            })
            st.success(f"✅ Added {len(sample_docs)} sample documents to vector store!")
        except Exception as e:
            log_api_call("VECTOR_STORE", "add_documents", {}, error=str(e))
            st.error(f"Error adding sample documents: {e}")


def process_uploaded_file(file, vector_store):
    """Process and add uploaded file to vector store"""
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.name}"
        with open(temp_path, "wb") as f:
            f.write(file.getbuffer())

        log_api_call("DOCUMENT", "process_file", {
            "filename": file.name,
            "size": file.size
        })

        # Process file with custom chunk settings
        processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
        chunks = processor.process_file(temp_path)

        # Add to vector store
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]

        log_api_call("EMBEDDING", "embed_documents", {
            "count": len(documents),
            "filename": file.name
        })
        asyncio.run(vector_store.add_documents(documents, metadatas))

        log_api_call("VECTOR_STORE", "add_documents", {
            "count": len(chunks),
            "filename": file.name
        })

        # Clean up
        os.remove(temp_path)

        return len(chunks)
    except Exception as e:
        log_api_call("DOCUMENT", "process_file", {"filename": file.name}, error=str(e))
        st.error(f"Error processing file: {e}")
        return 0


def display_document_viewer(vector_store):
    """Display document viewer with all documents in vector store"""
    with st.expander("📚 View All Documents", expanded=False):
        doc_count = vector_store.get_document_count()
        st.write(f"**Total documents:** {doc_count}")

        if doc_count > 0:
            # Add filters
            col1, col2 = st.columns(2)
            with col1:
                show_limit = st.number_input("Show documents:", min_value=5, max_value=500, value=min(50, doc_count), step=5)
            with col2:
                search_text = st.text_input("Filter by content:", "")

            # Get documents
            try:
                all_docs = vector_store.get_all_documents(limit=show_limit)

                # Group by source file
                docs_by_source = defaultdict(list)
                for doc in all_docs:
                    source = doc['metadata'].get('filename', doc['metadata'].get('source', 'Unknown'))
                    docs_by_source[source].append(doc)

                # Display by source
                for source, docs in docs_by_source.items():
                    with st.expander(f"📄 {source} ({len(docs)} chunks)", expanded=False):
                        for i, doc in enumerate(docs):
                            # Apply search filter
                            if search_text and search_text.lower() not in doc['document'].lower():
                                continue

                            st.markdown(f"""
                            <div class="doc-preview">
                                <strong>Chunk {i+1} (ID: {doc['id']})</strong><br>
                                {doc['document'][:300]}{'...' if len(doc['document']) > 300 else ''}
                            </div>
                            """, unsafe_allow_html=True)

                            # Show metadata
                            if doc['metadata']:
                                st.caption(f"Metadata: {json.dumps(doc['metadata'], indent=2)}")

                            st.divider()
            except Exception as e:
                st.error(f"Error loading documents: {e}")
        else:
            st.info("No documents in vector store. Upload a file or add sample documents.")


def display_api_calls():
    """Display API call log"""
    with st.expander("🔌 API Call Log", expanded=False):
        if not st.session_state.api_calls:
            st.info("No API calls yet")
            return

        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_type = st.multiselect(
                "Filter by type:",
                options=list(set(call['type'] for call in st.session_state.api_calls)),
                default=[]
            )
        with col2:
            show_success = st.checkbox("Show successful", value=True)
        with col3:
            show_errors = st.checkbox("Show errors", value=True)

        if st.button("Clear API Log"):
            st.session_state.api_calls = []
            st.rerun()

        # Display calls
        for call in reversed(st.session_state.api_calls):  # Most recent first
            # Apply filters
            if filter_type and call['type'] not in filter_type:
                continue
            if call['status'] == 'success' and not show_success:
                continue
            if call['status'] == 'error' and not show_errors:
                continue

            status_emoji = "✅" if call['status'] == 'success' else "❌"

            st.markdown(f"""
            <div class="api-call">
                <strong>{status_emoji} [{call['timestamp']}] {call['type']}</strong> → {call['endpoint']}<br>
                <em>Params:</em> {json.dumps(call['params'], indent=2)[:200]}
            </div>
            """, unsafe_allow_html=True)

            if call.get('error'):
                st.error(f"Error: {call['error']}")


def display_reasoning_process(result):
    """Display the agent's reasoning process with enhanced details"""
    # Display plan
    with st.expander("📋 Agent's Plan", expanded=True):
        st.markdown(f"```\n{result['plan']}\n```")

    # Display reasoning steps
    if result['reasoning_steps']:
        with st.expander("🧠 Reasoning Steps & Chain of Thought", expanded=True):
            for i, step in enumerate(result['reasoning_steps'], 1):
                st.markdown(f"### Step {i}: `{step['action']}`")

                # Show the thought process
                st.markdown("**Agent's Reasoning:**")
                st.code(step['content'], language="text")

                # Show timing if available
                if 'timestamp' in step:
                    st.caption(f"⏱️ Executed at: {step['timestamp']}")

                st.divider()

    # Display tool outputs with more detail
    if result['tool_outputs']:
        with st.expander("🔧 Tool Execution & Outputs", expanded=True):
            for i, output in enumerate(result['tool_outputs'], 1):
                st.markdown(f"### Tool Call {i}")

                # Parse and display tool information
                if isinstance(output, dict):
                    st.json(output)
                else:
                    st.text(output)

                st.divider()


def main():
    # Header
    st.markdown('<div class="main-header">🤖 NVIDIA NIM RAG Agent Demo - Enhanced</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Intelligent Agentic RAG with Document Viewer & API Logging</div>', unsafe_allow_html=True)

    # Initialize components
    llm_client, embedding_client = initialize_clients()
    vector_store = initialize_vector_store(embedding_client)
    agent = initialize_agent(llm_client, vector_store)

    # Main layout with tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 System Monitoring", "⚙️ Settings"])

    with tab1:
        # Chat interface (main tab)
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
                        # Log the query
                        log_api_call("AGENT", "run", {"query": prompt[:100]})

                        # Run agent
                        result = asyncio.run(agent.run(prompt))

                        log_api_call("AGENT", "run", {"query": prompt[:100]}, response="success")

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
                        log_api_call("AGENT", "run", {"query": prompt[:100]}, error=str(e))
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

    with tab2:
        # System monitoring tab
        st.header("📊 System Monitoring")

        col1, col2 = st.columns(2)

        with col1:
            # Document viewer
            display_document_viewer(vector_store)

        with col2:
            # API call log
            display_api_calls()

            # System stats
            with st.expander("📈 System Statistics", expanded=True):
                doc_count = vector_store.get_document_count()
                api_call_count = len(st.session_state.api_calls)
                error_count = sum(1 for call in st.session_state.api_calls if call['status'] == 'error')

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Documents", doc_count)
                col_b.metric("API Calls", api_call_count)
                col_c.metric("Errors", error_count, delta_color="inverse")

    with tab3:
        # Settings tab
        st.header("⚙️ Settings & Configuration")

        # API Logging toggle
        st.subheader("🔌 API Logging")
        enable_logging = st.checkbox(
            "Enable API call logging",
            value=st.session_state.enable_api_logging,
            help="Log all API calls for debugging"
        )
        if enable_logging != st.session_state.enable_api_logging:
            st.session_state.enable_api_logging = enable_logging
            st.rerun()

        st.divider()

        # Current configuration
        st.subheader("⚙️ Current Configuration")
        config_data = {
            "LLM Model": settings.nim_model,
            "Embedding Model": settings.nim_embedding_model,
            "Temperature": settings.temperature,
            "Max Tokens": settings.max_tokens,
            "Max Iterations": settings.max_iterations,
            "Collection Name": settings.collection_name
        }
        st.json(config_data)

        st.divider()

        # Vector store management
        st.subheader("📚 Vector Store Management")

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
        st.subheader("🗑️ Danger Zone")
        if st.button("Clear All Documents", use_container_width=True, type="secondary"):
            if st.checkbox("I confirm this action"):
                vector_store.reset_collection()
                st.success("✅ Collection cleared!")
                st.rerun()

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>Powered by NVIDIA NIM | llama-3.1-nemotron-nano-8B | Built for AWS Hackathon</p>
        <p>Enhanced with Document Viewer & API Call Logging</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
