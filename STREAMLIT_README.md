# Streamlit App - NIM RAG Agent Demo

## Overview

An interactive Streamlit application for testing the NVIDIA NIM RAG Agent with a beautiful UI.

## Features

- 🤖 **Interactive Chat Interface**: Chat with the AI agent in real-time
- 📋 **Transparent Reasoning**: View the agent's plan, reasoning steps, and tool outputs
- 📚 **Document Management**: Upload documents or add sample documents to the knowledge base
- 🔧 **Tool Integration**: Agent uses retrieval and calculator tools intelligently
- 📊 **Real-time Metrics**: See document count and system status
- 💬 **Chat History**: Full conversation history with reasoning traces

## Prerequisites

1. **NVIDIA API Key**: Get your free API key from [https://build.nvidia.com/](https://build.nvidia.com/)
2. **Python 3.12+** with virtual environment
3. **Dependencies installed** (see Installation section)

## Installation

### 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit the `.env` file and set your NVIDIA API key:

```bash
# CRITICAL: Replace with your actual API key
NIM_API_KEY=your_actual_nvidia_api_key_here

# Model Configuration (defaults are fine)
NIM_MODEL=llama-3.1-nemotron-nano-8b-instruct
NIM_EMBEDDING_MODEL=nvidia/nv-embedqa-e5-v5
NIM_INFERENCE_URL=https://integrate.api.nvidia.com/v1
```

**Important Model Names:**
- ✅ Correct: `llama-3.1-nemotron-nano-8b-instruct` (with dots and `-instruct`)
- ❌ Wrong: `llama-3_1-nemotron-nano-8b-v1` (underscores or wrong suffix)

## Running the App

### Start the Streamlit App

```bash
# Activate virtual environment
source venv/bin/activate

# Run Streamlit
streamlit run streamlit_app.py
```

The app will start and display:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

### Access the App

Open your browser and navigate to:
- **Local**: http://localhost:8501
- **Network** (other devices on same network): Use the Network URL shown

## Using the App

### 1. Add Documents (First Time Setup)

The agent needs documents in its knowledge base to answer questions:

**Option A: Add Sample Documents**
1. Click **"➕ Add Sample Documents"** in the sidebar
2. This adds 5 sample documents about NIM, RAG, AWS, etc.

**Option B: Upload Your Own Documents**
1. Use the **"📄 Upload Document"** section
2. Supported formats: TXT, PDF, DOCX, Markdown
3. Click **"Process & Add Document"**

### 2. Chat with the Agent

1. Type your question in the chat input at the bottom
2. Press Enter or click Send
3. Watch the agent:
   - Create a plan
   - Execute reasoning steps
   - Use tools (retrieval, calculator)
   - Generate the final answer

### 3. View Reasoning Process

Each response shows expandable sections:
- **📋 Agent's Plan**: The step-by-step plan the agent created
- **🧠 Reasoning Steps**: Each decision the agent made
- **🔧 Tool Outputs**: Results from tool executions

### 4. Example Queries

**Simple Calculation:**
```
What is 123 * 456?
```

**Knowledge Retrieval:**
```
What is NVIDIA NIM?
```

**Complex Multi-step:**
```
Explain how RAG works and calculate how many documents we have in the store.
```

**Agentic Reasoning:**
```
Find information about AWS EKS and tell me why it's useful for deploying AI models.
```

## Sidebar Features

### Configuration Display
- Current model name
- Embedding model
- Temperature setting
- Max iterations

### Vector Store Management
- **Document Count**: Shows how many documents are in the store
- **Add Sample Documents**: Quick way to populate the knowledge base
- **Upload Document**: Add your own files
- **Clear All Documents**: Reset the vector store (requires confirmation)

### Chat History
- **Clear Chat History**: Clears the conversation (doesn't affect documents)

## Troubleshooting

### Error: "NIM_API_KEY not set"

**Problem**: API key is missing or still has placeholder value

**Solution**:
1. Edit `.env` file
2. Replace `your_nvidia_api_key_here` with your actual API key from build.nvidia.com
3. Restart the Streamlit app

### Error: "Invalid API Key"

**Problem**: API key is incorrect or expired

**Solution**:
1. Verify your API key at https://build.nvidia.com/
2. Get a new API key if needed
3. Update `.env` file
4. Restart the app

### Error: "Module not found"

**Problem**: Dependencies not installed

**Solution**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### App is slow or timing out

**Problem**: Network issues or API rate limits

**Solution**:
1. Check your internet connection
2. Verify NVIDIA API service status
3. Try again in a few moments
4. Reduce `MAX_ITERATIONS` in `.env` if needed

### Documents not being found

**Problem**: No documents in vector store

**Solution**:
1. Check document count in sidebar (should be > 0)
2. Use "Add Sample Documents" button
3. Or upload your own documents
4. Wait for "Added X documents" success message

### Wrong model name error

**Problem**: Incorrect model name in `.env`

**Solution**:
Edit `.env` and ensure:
```bash
NIM_MODEL=llama-3.1-nemotron-nano-8b-instruct
# NOT: llama-3_1-nemotron-nano-8b-v1
```

## Testing Without API Key

You can test the app's UI and component initialization:

```bash
# Run component test script
python test_streamlit_components.py
```

This will verify:
- ✓ Configuration loading
- ✓ Client initialization (will show API key needed)
- ✓ Vector store setup
- ✓ Agent initialization

## Architecture

```
┌─────────────────────────────────────────┐
│         Streamlit Frontend              │
│  (Chat UI, Document Upload, Display)    │
└─────────────┬───────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────┐
│          RAG Agent Core                 │
│  (Planning, Reasoning, Tool Execution)  │
└─────────────┬───────────────────────────┘
              │
              ↓
      ┌───────┴────────┐
      │                │
      ↓                ↓
┌──────────┐    ┌──────────┐
│ Retrieval│    │Calculator│
│   Tool   │    │   Tool   │
└────┬─────┘    └──────────┘
     │
     ↓
┌──────────────┐
│ Vector Store │
│  (ChromaDB)  │
└──────────────┘
```

## Configuration Reference

### Model Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `NIM_MODEL` | `llama-3.1-nemotron-nano-8b-instruct` | LLM model name |
| `NIM_EMBEDDING_MODEL` | `nvidia/nv-embedqa-e5-v5` | Embedding model |
| `TEMPERATURE` | `0.7` | Sampling temperature (0.0-1.0) |
| `MAX_TOKENS` | `2048` | Maximum tokens per response |
| `MAX_ITERATIONS` | `10` | Max agent reasoning steps |

### Storage Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB storage path |
| `COLLECTION_NAME` | `documents` | Collection name in ChromaDB |

## Performance Tips

1. **Document Chunking**: Large documents are automatically split into 500-token chunks
2. **Retrieval Results**: Default k=3 documents retrieved per query
3. **Caching**: Clients are cached using `@st.cache_resource` for faster reloads
4. **Temperature**: Lower values (0.3) for more focused responses, higher (0.9) for creativity

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit `.env` with real API keys** - Already protected by `.gitignore`
2. **API keys are transmitted over HTTPS** to NVIDIA endpoints
3. **Calculator tool is sandboxed** - Only allows safe mathematical expressions
4. **Local deployment** - Streamlit runs on localhost by default

## Customization

### Adding New Tools

Edit `src/agent/tools.py`:

```python
class YourCustomTool:
    def __init__(self):
        self.name = "your_tool"
        self.description = "What your tool does"

    async def run(self, input: str) -> str:
        # Your tool logic
        return result
```

Then add to agent in `streamlit_app.py`:

```python
your_tool = YourCustomTool()
tools = [retrieval_tool, calculator_tool, your_tool]
```

### Changing UI Theme

Edit CSS in `streamlit_app.py`:

```python
st.markdown("""
<style>
    .main-header {
        color: #YOUR_COLOR;
    }
</style>
""", unsafe_allow_html=True)
```

## Production Deployment

For production deployment, see:
- `README.md` - Main deployment guide
- `infrastructure/` - AWS EKS deployment files
- `.env.example` - Template for production secrets

## Support

- **Issues**: Check `BUGFIXES.md` for known issues
- **Testing**: See `TESTING.md` for test documentation
- **API Docs**: https://docs.nvidia.com/nim/

## License

See LICENSE file in project root.

---

**Built with NVIDIA NIM | llama-3.1-nemotron-nano-8B | For AWS Hackathon**
