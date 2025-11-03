# Architecture Documentation

## System Overview

The NIM RAG Agent is a production-ready agentic AI system that combines retrieval-augmented generation with multi-step reasoning capabilities. The system is designed to be deployed on AWS EKS with GPU support for optimal performance.

## Core Components

### 1. Agent Layer (`src/agent/`)

**RAGAgent** (`rag_agent.py`)
- Implements the main agent loop using LangGraph concepts
- Manages multi-step planning and execution
- Coordinates between LLM and tools
- Key methods:
  - `plan()`: Creates execution plan for user queries
  - `reason_and_act()`: Decides next action based on plan
  - `execute_tool_call()`: Executes agent tools
  - `run()`: Main agent execution loop

**Tools** (`tools.py`)
- `RetrievalTool`: Searches vector database for relevant documents
- `CalculatorTool`: Performs basic calculations (demo)
- Extensible design allows adding new tools easily

### 2. NVIDIA NIM Integration (`src/nim_clients/`)

**LLM Client** (`llm_client.py`)
- OpenAI-compatible API client for NVIDIA NIM
- Uses llama-3.1-nemotron-nano-8B-v1 model
- Features:
  - Async/await support
  - Retry logic with exponential backoff
  - Streaming responses
  - Temperature and token control

**Embedding Client** (`embedding_client.py`)
- Generates embeddings using NVIDIA NIM
- Uses nv-embedqa-e5-v5 model
- Batch processing support
- Optimized for retrieval tasks

### 3. Retrieval System (`src/retrieval/`)

**Vector Store** (`vector_store.py`)
- ChromaDB integration for vector storage
- Features:
  - Persistent storage
  - Cosine similarity search
  - Metadata filtering
  - Document management (add, delete, reset)

**Document Processor** (`document_processor.py`)
- Handles multiple file formats (PDF, DOCX, Markdown, Text)
- Intelligent text chunking with overlap
- Preserves document metadata
- Batch directory processing

### 4. API Layer (`src/api/`)

**FastAPI Application** (`main.py`)
- RESTful API with async support
- Endpoints:
  - `POST /query`: Query the agent
  - `POST /documents/ingest`: Add documents
  - `POST /documents/search`: Search vector store
  - `GET /health`: Health check
- CORS enabled for frontend access
- Static file serving for web UI

### 5. Frontend (`frontend/`)

**Web Interface**
- Modern, responsive design
- Real-time agent reasoning display
- Shows planning steps and tool outputs
- System status monitoring
- Built with vanilla JavaScript (no framework dependencies)

## Data Flow

### Query Processing Flow

```
1. User Query
   ↓
2. FastAPI Endpoint (/query)
   ↓
3. RAG Agent
   ├─→ Planning Phase
   │   └─→ LLM generates execution plan
   │
   ├─→ Execution Phase (iterative)
   │   ├─→ Reasoning: Decide next action
   │   ├─→ Tool Use (if needed)
   │   │   └─→ Retrieval Tool
   │   │       ├─→ Generate query embedding
   │   │       ├─→ Search vector store
   │   │       └─→ Return relevant docs
   │   └─→ Continue or Answer
   │
   └─→ Final Answer Generation
       └─→ LLM synthesizes response
```

### Document Ingestion Flow

```
1. Document Upload
   ↓
2. Document Processor
   ├─→ Parse file (PDF/DOCX/etc)
   ├─→ Chunk text (with overlap)
   └─→ Add metadata
   ↓
3. Embedding Generation
   └─→ NIM Embedding API
   ↓
4. Vector Store
   └─→ ChromaDB persistence
```

## AWS Infrastructure

### EKS Cluster Architecture

```
┌─────────────────────────────────────────┐
│          AWS EKS Cluster                │
│                                          │
│  ┌────────────────────────────────┐    │
│  │  Control Plane                 │    │
│  │  (Managed by AWS)              │    │
│  └────────────────────────────────┘    │
│                                          │
│  ┌────────────────┐  ┌───────────────┐ │
│  │  CPU Nodes     │  │  GPU Nodes    │ │
│  │  (t3.large)    │  │  (g4dn.xlarge)│ │
│  │                │  │               │ │
│  │  - General     │  │  - NIM        │ │
│  │    workloads   │  │    inference  │ │
│  │  - API pods    │  │  - GPU tasks  │ │
│  └────────────────┘  └───────────────┘ │
│                                          │
│  ┌────────────────────────────────┐    │
│  │  Load Balancer                 │    │
│  │  (AWS ELB)                     │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### Kubernetes Components

**Namespace**: `nim-rag-agent`
- Isolates application resources
- Enables RBAC policies

**Deployments**
- Application pods (replicas: 2-10)
- Rolling update strategy
- Resource limits and requests
- Liveness and readiness probes

**Services**
- LoadBalancer type for external access
- Internal DNS for inter-pod communication

**Storage**
- PersistentVolumeClaim for ChromaDB data
- EBS gp2 volumes (10GB)

**Autoscaling**
- HorizontalPodAutoscaler
- CPU-based scaling (70% threshold)
- Memory-based scaling (80% threshold)
- Min: 2 replicas, Max: 10 replicas

## Security Considerations

### Secrets Management
- NVIDIA API keys stored in Kubernetes Secrets
- Not committed to version control
- Mounted as environment variables

### Network Security
- Private subnets for worker nodes
- Security groups restrict traffic
- VPC isolation

### API Security
- CORS configured for frontend access
- Health endpoints don't expose sensitive data
- Input validation on all endpoints

## Performance Optimization

### Caching Strategy
- ChromaDB persistent storage
- Embedding cache (implicit in vector store)
- Connection pooling for database

### Async Processing
- All I/O operations are async
- Concurrent request handling
- Non-blocking agent execution

### Resource Management
- Pod resource limits prevent resource exhaustion
- HPA scales based on load
- GPU nodes dedicated for NIM inference

## Monitoring and Observability

### Health Checks
- Kubernetes liveness probes
- Kubernetes readiness probes
- Custom health endpoint

### Logging
- Structured logging with loguru
- Configurable log levels
- Pod logs accessible via kubectl

### Metrics (Future Enhancement)
- Prometheus integration ready
- Custom metrics for agent performance
- Query latency tracking

## Scalability

### Horizontal Scaling
- HPA automatically scales pods
- Load balancer distributes traffic
- Stateless API design

### Vertical Scaling
- Node groups can be resized
- GPU instances for compute-heavy tasks
- Memory-optimized for vector operations

### Data Scaling
- ChromaDB supports millions of vectors
- Can be migrated to managed vector DB
- Sharding possible for large deployments

## Development Workflow

### Local Development
1. Use `.env` file for configuration
2. Run locally with `uvicorn`
3. Test with pytest
4. Use docker-compose for isolated environment

### CI/CD (Recommended)
1. Build Docker image
2. Run tests in container
3. Push to ECR
4. Update Kubernetes deployment
5. Rolling update to EKS

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| LLM | NVIDIA NIM (Llama 3.1) | Reasoning and generation |
| Embeddings | NVIDIA NIM Embeddings | Semantic search |
| Vector DB | ChromaDB | Document storage |
| Agent Framework | LangGraph concepts | Planning and execution |
| API | FastAPI | REST endpoints |
| Frontend | HTML/CSS/JS | User interface |
| Container | Docker | Application packaging |
| Orchestration | Kubernetes | Container management |
| Cloud | AWS EKS | Infrastructure |
| IaC | Terraform | Infrastructure provisioning |

## Extension Points

### Adding New Tools
1. Create tool class in `src/agent/tools.py`
2. Implement `run()` method
3. Add to agent initialization

### Custom Document Processors
1. Extend `DocumentProcessor` class
2. Add new file type handlers
3. Register in `read_file()` method

### Alternative Vector Stores
1. Implement `VectorStore` interface
2. Update configuration
3. Minimal code changes required

## Deployment Checklist

- [ ] NVIDIA API key configured
- [ ] AWS credentials set up
- [ ] EKS cluster provisioned
- [ ] Docker image built and pushed
- [ ] Kubernetes secrets created
- [ ] Application deployed
- [ ] Health checks passing
- [ ] Frontend accessible
- [ ] Test queries working
- [ ] Monitoring configured

## Maintenance

### Regular Tasks
- Monitor pod health
- Check HPA scaling events
- Review logs for errors
- Update dependencies
- Rotate API keys

### Troubleshooting
- Check pod logs: `kubectl logs`
- Describe resources: `kubectl describe`
- Test endpoints: `curl /health`
- Verify secrets: `kubectl get secrets`

## Future Enhancements

1. **Authentication**: Add user authentication
2. **Streaming**: Server-sent events for real-time responses
3. **Multi-tenancy**: Support multiple users/orgs
4. **Analytics**: Track usage and performance metrics
5. **RAG Improvements**: Hybrid search, reranking
6. **More Tools**: Web search, code execution, etc.
7. **Fine-tuning**: Custom model fine-tuning
8. **Caching**: Response caching for common queries
