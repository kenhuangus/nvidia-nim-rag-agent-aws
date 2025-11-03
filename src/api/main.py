"""
FastAPI REST API for the RAG Agent
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from loguru import logger
import sys

from src.nim_clients.llm_client import NIMClient
from src.nim_clients.embedding_client import NIMEmbeddingClient
from src.retrieval.vector_store import VectorStore
from src.retrieval.document_processor import DocumentProcessor
from src.agent.rag_agent import RAGAgent
from src.agent.tools import RetrievalTool, CalculatorTool
from src.utils.config import settings

# Configure logging
logger.remove()
logger.add(sys.stderr, level=settings.log_level)

# Initialize FastAPI app
app = FastAPI(
    title="NIM RAG Agent API",
    description="Agentic RAG system using NVIDIA NIM and LangGraph",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend) - Note: This should be AFTER all route definitions


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    max_iterations: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    plan: str
    tool_outputs: List[str]
    reasoning_steps: List[Dict[str, Any]]


class DocumentRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None


class IngestResponse(BaseModel):
    message: str
    document_id: str
    total_documents: int


class HealthResponse(BaseModel):
    status: str
    vector_store_docs: int


# Global instances (initialized on startup)
llm_client: Optional[NIMClient] = None
embedding_client: Optional[NIMEmbeddingClient] = None
vector_store: Optional[VectorStore] = None
agent: Optional[RAGAgent] = None
document_processor: Optional[DocumentProcessor] = None


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global llm_client, embedding_client, vector_store, agent, document_processor

    try:
        logger.info("Initializing NIM RAG Agent...")

        # Initialize clients
        llm_client = NIMClient(
            api_key=settings.nim_api_key,
            base_url=settings.nim_inference_url,
            model=settings.nim_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

        embedding_client = NIMEmbeddingClient(
            api_key=settings.nim_api_key,
            base_url=settings.nim_inference_url,
            model=settings.nim_embedding_model,
        )

        # Initialize vector store
        vector_store = VectorStore(
            embedding_client=embedding_client,
            persist_dir=settings.chroma_persist_dir,
            collection_name=settings.collection_name,
        )

        # Initialize tools
        retrieval_tool = RetrievalTool(vector_store)
        calculator_tool = CalculatorTool()
        tools = [retrieval_tool, calculator_tool]

        # Initialize agent
        agent = RAGAgent(
            llm_client=llm_client,
            tools=tools,
            max_iterations=settings.max_iterations,
        )

        # Initialize document processor
        document_processor = DocumentProcessor()

        logger.info("NIM RAG Agent initialized successfully!")

    except Exception as e:
        logger.error(f"Error initializing agent: {e}")
        raise


@app.get("/")
async def root():
    """Serve the frontend index page"""
    try:
        return FileResponse("frontend/index.html")
    except FileNotFoundError:
        return {
            "message": "NIM RAG Agent API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }


@app.get("/api/info", response_model=Dict[str, str])
async def api_info():
    """API information endpoint"""
    return {
        "message": "NIM RAG Agent API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        vector_store_docs=vector_store.get_document_count(),
    )


@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Query the RAG agent

    Args:
        request: Query request with query text

    Returns:
        Agent response with answer, plan, and reasoning
    """
    try:
        logger.info(f"Received query: {request.query}")

        # Run agent
        result = await agent.run(request.query)

        return QueryResponse(
            answer=result['answer'],
            plan=result['plan'],
            tool_outputs=result['tool_outputs'],
            reasoning_steps=result['reasoning_steps'],
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/simple")
async def query_simple(request: QueryRequest):
    """
    Query the agent and return just the answer

    Args:
        request: Query request

    Returns:
        Simple answer string
    """
    try:
        answer = await agent.run_simple(request.query)
        return {"answer": answer}

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents/ingest", response_model=IngestResponse)
async def ingest_document(request: DocumentRequest):
    """
    Ingest a document into the vector store

    Args:
        request: Document text and metadata

    Returns:
        Ingestion confirmation
    """
    try:
        logger.info(f"Ingesting document (length: {len(request.text)})")

        # Chunk document
        chunks = document_processor.chunk_text(request.text)

        # Add to vector store
        texts = chunks
        metadatas = [request.metadata or {} for _ in chunks]
        ids = await vector_store.add_documents(texts, metadatas)

        return IngestResponse(
            message=f"Successfully ingested document with {len(chunks)} chunks",
            document_id=ids[0] if ids else "unknown",
            total_documents=vector_store.get_document_count(),
        )

    except Exception as e:
        logger.error(f"Error ingesting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/count")
async def get_document_count():
    """Get the number of documents in the vector store"""
    return {
        "count": vector_store.get_document_count()
    }


@app.post("/documents/search")
async def search_documents(query: str, k: int = 5):
    """
    Search for similar documents

    Args:
        query: Search query
        k: Number of results

    Returns:
        List of similar documents
    """
    try:
        results = await vector_store.similarity_search(query, k=k)
        return {"results": results}

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files AFTER all API routes
# Note: Order matters - API routes defined above take precedence
try:
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
except RuntimeError:
    logger.warning("Static directory not found, skipping static files mount")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
