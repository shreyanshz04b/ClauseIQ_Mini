# ClauseIQ - Legal Document RAG System

A retrieval-augmented generation (RAG) system for legal document analysis and question-answering using local LLMs.

## Features

- Upload and index legal documents (PDF, DOCX)
- Query documents using natural language
- Retrieval-augmented generation with local Ollama LLM
- Document classification and intent detection
- Security guardrails for safe query execution
- Vector-based semantic search with FAISS
- Inline document citations in responses

## Quick Start

### Prerequisites

- Python 3.9+
- Ollama running locally with `phi3:mini` and `nomic-embed-text` models
- Flask 3.0.3
- SQLAlchemy 3.1.1

### Installation

1. Clone the repository:
```bash
cd clauseiq
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

Start the application:
```bash
python run.py
```

The application will be available at `http://localhost:5000`

### How to Use

1. **Upload Documents**: Click "Upload Document" and select PDF or DOCX files
2. **Index Documents**: Wait for automatic indexing or click "Index" button
3. **Ask Questions**: Type questions in the chat interface
4. **View Citations**: Response includes document citations with sources

## System Architecture

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md)

### Core Components

- **Flask Web Framework**: HTTP request routing and page serving
- **SQLAlchemy ORM**: Database models for documents and embeddings
- **Ollama LLM Service**: Local language model for chat and embeddings
- **FAISS Vector Store**: Semantic similarity search
- **SentenceTransformer**: Text-to-embedding conversion
- **pypdf/python-docx**: Document content extraction

## Project Structure

```
app/
  config.py           - Configuration settings
  extensions.py       - Flask extensions initialization
  __init__.py         - Flask app factory
  models.py           - Database models and vector search
  vector_store.py     - FAISS vector database operations
  
  routes/
    pages.py          - HTML page routes (home, chat, landing)
    chat.py           - Chat API endpoint
    upload.py         - Document upload API
    ingest.py         - Document indexing API
  
  services/
    rag.py            - Main RAG pipeline orchestration
    guardrails.py     - Security validation for queries
    ingestion.py      - Document processing and embedding
    ollama_client.py   - Ollama LLM API wrapper
    background.py     - Async document indexing
  
  static/
    css/app.css       - Custom CSS styling
    js/main.js        - Global JavaScript utilities
    js/chat.js        - Chat interface logic
  
  templates/
    base.html         - HTML base template
    chat.html         - Chat page template
    landing.html      - Landing page template
  
  data/               - Reference data (CSV, JSON files)

docs/                 - Documentation
run.py                - Application entry point
requirements.txt      - Python dependencies
```

## File Descriptions

See the [BACKEND](BACKEND/) and [FRONTEND](FRONTEND/) documentation folders for detailed descriptions of each file's purpose and functionality.
