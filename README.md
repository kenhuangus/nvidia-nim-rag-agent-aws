# NIM RAG Agent: Intelligent Research Assistant

An advanced agentic RAG (Retrieval-Augmented Generation) system powered by NVIDIA NIM and deployed on AWS EKS. This application demonstrates multi-step reasoning, document retrieval, and intelligent planning capabilities using the llama-3.1-nemotron-nano-8B-v1 model.

## 🎯 Project Overview

This project implements an intelligent research assistant that:
- **Plans and Reasons**: Uses multi-step planning to break down complex questions
- **Retrieves Context**: Searches through a knowledge base using NVIDIA NIM embeddings
- **Provides Answers**: Generates accurate responses with source citations
- **Scales on AWS**: Deploys on Amazon EKS with GPU support for optimal performance

### Key Features
- ✅ Multi-step agentic reasoning with LangGraph
- ✅ NVIDIA NIM for LLM inference (llama-3.1-nemotron-nano-8B-v1)
- ✅ NVIDIA NIM Embeddings for retrieval (nv-embedqa-e5-v5)
- ✅ ChromaDB vector database for document storage
- ✅ FastAPI REST API with async support
- ✅ Modern web interface with real-time updates
- ✅ Production-ready AWS EKS deployment
- ✅ Horizontal pod autoscaling
- ✅ Health checks and monitoring

## 🏗️ Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Web Frontend       │
│  (HTML/CSS/JS)      │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  FastAPI Backend    │
│  - Query Handler    │
│  - Doc Ingestion    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  RAG Agent          │
│  - Planning         │
│  - Tool Execution   │
│  - Reasoning        │
└───┬─────────────┬───┘
    │             │
    ▼             ▼
┌──────────┐  ┌──────────────┐
│ NIM LLM  │  │ Retrieval    │
│ (Llama)  │  │ Tool         │
└──────────┘  └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │ Vector Store │
              │ (ChromaDB)   │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │ NIM Embeddings│
              └──────────────┘
```

## 📋 Prerequisites

### For Local Development
- Python 3.11+
- NVIDIA API Key (get from [NVIDIA API Catalog](https://build.nvidia.com))
- Docker (optional, for containerized deployment)

### For AWS Deployment
- AWS Account with EKS access
- AWS CLI configured
- kubectl installed
- Terraform 1.0+ (for infrastructure provisioning)
- Sufficient AWS quota for GPU instances (g4dn.xlarge)

## ✅ Code Quality & Testing

All code has been thoroughly tested and debugged:
- **3 Critical bugs fixed** (see [BUGFIXES.md](BUGFIXES.md))
- All Python modules compile without errors
- Type hints and async/await correctly implemented
- Comprehensive test suite included
- Verification script to check setup

Run verification:
```bash
python scripts/verify_setup.py
```

## 🚀 Quick Start (Local Development)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd aws-contest

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your NVIDIA API key
# NIM_API_KEY=your_nvidia_api_key_here
```

### 3. Ingest Sample Documents (Optional)

```bash
# Create a docs directory with sample files
mkdir -p docs
echo "Machine learning is a subset of artificial intelligence..." > docs/ml.txt

# Ingest documents
python scripts/ingest_documents.py --directory docs --pattern "*.txt"
```

### 4. Run the Application

**Recommended: Run with Streamlit (Interactive UI)**

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the Streamlit app
streamlit run streamlit_app.py --server.port 8501 --server.headless true
```

**Alternative Options:**

```bash
# Option 1: FastAPI backend (REST API)
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Using script
bash scripts/run_local.sh

# Option 3: Using Docker Compose
docker-compose up
```

### 5. Access the Application

**Streamlit Interface (Recommended)**
- **Interactive UI**: http://localhost:8501
- Features: Chat interface, document upload, agent reasoning visualization, API call logging

**FastAPI Backend**
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

**To Stop the Streamlit App:**
```bash
# Press Ctrl+C in the terminal, or
pkill -f "streamlit run"
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_document_processor.py
```

## ☁️ AWS Deployment

### Step 1: Provision EKS Infrastructure

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply infrastructure
terraform apply

# Configure kubectl
aws eks update-kubeconfig --region us-east-1 --name nim-rag-agent-cluster
```

### Step 2: Build and Push Docker Image

```bash
# Build Docker image
docker build -t nim-rag-agent:latest .

# Tag for ECR (replace with your AWS account ID and region)
docker tag nim-rag-agent:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/nim-rag-agent:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository if it doesn't exist
aws ecr create-repository --repository-name nim-rag-agent --region us-east-1

# Push image
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/nim-rag-agent:latest
```

### Step 3: Deploy to Kubernetes

```bash
cd infrastructure/kubernetes

# Create namespace
kubectl apply -f namespace.yaml

# Create secrets (edit with your API key first)
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with your NVIDIA API key
kubectl apply -f secrets.yaml

# Apply configurations
kubectl apply -f configmap.yaml
kubectl apply -f pvc.yaml

# Update deployment.yaml with your Docker image URL
# Then deploy
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml

# Wait for pods to be ready
kubectl get pods -n nim-rag-agent -w
```

### Step 4: Access the Application

```bash
# Get the LoadBalancer URL
kubectl get svc nim-rag-agent -n nim-rag-agent

# Access the application at the EXTERNAL-IP
# Example: http://a1b2c3d4.us-east-1.elb.amazonaws.com
```

## 📊 Monitoring and Scaling

### Check Application Health

```bash
# View pods
kubectl get pods -n nim-rag-agent

# View logs
kubectl logs -f deployment/nim-rag-agent -n nim-rag-agent

# Check HPA status
kubectl get hpa -n nim-rag-agent

# View service
kubectl get svc -n nim-rag-agent
```

### Scale Manually

```bash
# Scale to 5 replicas
kubectl scale deployment nim-rag-agent -n nim-rag-agent --replicas=5

# Check scaling status
kubectl get pods -n nim-rag-agent
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NIM_API_KEY` | NVIDIA API key (required) | - |
| `NIM_INFERENCE_URL` | NIM inference endpoint | `https://integrate.api.nvidia.com/v1` |
| `NIM_MODEL` | LLM model name | `llama-3.1-nemotron-nano-8b-instruct` |
| `NIM_EMBEDDING_MODEL` | Embedding model name | `nvidia/nv-embedqa-e5-v5` |
| `CHROMA_PERSIST_DIR` | ChromaDB data directory | `./data/chroma` |
| `MAX_ITERATIONS` | Max agent iterations | `10` |
| `TEMPERATURE` | LLM temperature | `0.7` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 📁 Project Structure

```
.
├── src/
│   ├── agent/              # Agent logic and tools
│   │   ├── rag_agent.py   # Main agent implementation
│   │   └── tools.py       # Agent tools (retrieval, calculator)
│   ├── nim_clients/       # NVIDIA NIM clients
│   │   ├── llm_client.py  # LLM inference client
│   │   └── embedding_client.py  # Embedding client
│   ├── retrieval/         # Document processing and retrieval
│   │   ├── vector_store.py      # ChromaDB integration
│   │   └── document_processor.py # Document parsing
│   ├── api/               # FastAPI application
│   │   └── main.py        # API endpoints
│   └── utils/             # Utilities
│       └── config.py      # Configuration management
├── frontend/              # Web interface
│   ├── index.html         # Main HTML
│   └── static/            # CSS and JavaScript
├── infrastructure/        # Infrastructure as Code
│   ├── terraform/         # EKS cluster setup
│   └── kubernetes/        # K8s manifests
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container image
├── docker-compose.yaml   # Local Docker setup
└── README.md             # This file
```

## 🎯 API Endpoints

### Query Agent
```bash
POST /query
{
  "query": "What is machine learning?"
}
```

### Ingest Document
```bash
POST /documents/ingest
{
  "text": "Document content...",
  "metadata": {"source": "example.txt"}
}
```

### Search Documents
```bash
POST /documents/search?query=machine%20learning&k=5
```

### Health Check
```bash
GET /health
```

## 💰 Cost Estimation

### AWS Resources (Monthly)
- EKS Control Plane: ~$72
- EC2 Instances (CPU): ~$140 (2x t3.large)
- EC2 GPU Instances: ~$150 (1x g4dn.xlarge)
- EBS Storage: ~$10 (100GB)
- Load Balancer: ~$20
- Data Transfer: Variable

**Total: ~$400-500/month**

### NVIDIA NIM API
- Pricing varies based on usage
- Check [NVIDIA pricing](https://build.nvidia.com/pricing) for current rates

## 🧹 Cleanup

### Remove Kubernetes Resources
```bash
kubectl delete namespace nim-rag-agent
```

### Destroy AWS Infrastructure
```bash
cd infrastructure/terraform
terraform destroy
```

## 🐛 Troubleshooting

### Issue: Pods not starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n nim-rag-agent

# Check logs
kubectl logs <pod-name> -n nim-rag-agent
```

### Issue: NVIDIA API errors
- Verify API key is correct in secrets
- Check NVIDIA API status
- Verify model names are correct

### Issue: ChromaDB errors
- Ensure PVC is mounted correctly
- Check volume permissions
- Verify sufficient disk space

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **NVIDIA** for NIM inference platform
- **AWS** for EKS hosting
- **LangChain/LangGraph** for agent framework
- **ChromaDB** for vector storage

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check documentation at `/docs`
- Review API docs at `/docs` endpoint

---

**Built for the NVIDIA NIM + AWS Hackathon**

Demonstrates advanced agentic AI with production-ready deployment on AWS infrastructure.
