# ClauseIQ Architecture

## System Overview

ClauseIQ implements a Retrieval-Augmented Generation (RAG) pipeline that combines document retrieval with local LLM inference to answer legal questions with cited sources.

```
User Input (Query)
       ↓
Security Check (Guardrails)
       ↓
Intent Classification (DOCUMENT/GENERAL/NONLEGAL)
       ↓
Vector Search (FAISS Index)
       ↓
LLM Prompt Construction
       ↓
Ollama Chat Model
       ↓
Citation Extraction
       ↓
Response to User
```

## Data Flow

### Document Upload Flow

1. User uploads PDF or DOCX file via web interface
2. **upload.py** saves file to disk and creates database record
3. **background.py** triggers async indexing in separate thread
4. **ingestion.py** extracts text from document:
   - PDF: Uses pypdf library to extract text from pages
   - DOCX: Uses python-docx to extract paragraph text
5. Text is chunked into 1200-character segments for embeddings
6. **ollama_client.py** calls Ollama to generate embeddings for each chunk
7. **vector_store.py** adds embeddings to FAISS index with metadata
8. **models.py** saves chunks and embeddings to SQLite database
9. Document status changes from "pending" to "indexed"

### Query/Chat Flow

1. User submits question in chat interface
2. **chat.js** sends POST request to `/api/chat` endpoint
3. **chat.py** receives query and calls `rag_pipeline()`
4. **rag.py** orchestrates the pipeline:
   - **guardrails.py**: Validates query is safe (checks for jailbreak attempts)
   - Intent detection: Classifies query as DOCUMENT, GENERAL, or NONLEGAL
   - **vector_store.py**: Searches FAISS index for similar chunks
   - If no documents found: Returns error response
   - If unsafe query: Returns security warning
5. Top 5 most similar chunks retrieved as context
6. LLM prompt constructed with:
   - System message (legal assistant role)
   - Retrieved context (document chunks with document numbers)
   - User query
7. **ollama_client.py** sends prompt to Ollama phi3:mini model
8. Ollama generates response with inline document citations
9. **rag.py** extracts citation numbers from response
10. Maps document numbers back to source filenames
11. Returns response with citations list to frontend
12. **chat.js** displays response and citations to user

## Component Details

### Frontend (JavaScript/HTML)

**main.js** - Global utilities:
- Authentication session management
- Login/logout handlers
- Form submission helpers
- File upload triggers
- Metrics dashboard

**chat.js** - Chat interface:
- Chat message display (user and assistant)
- Document list management (load, delete)
- File upload for document indexing
- Query submission and response display
- Citation formatting
- Keyboard shortcuts (Ctrl+Enter to send, Escape to clear)

**HTML Templates**:
- base.html: Base layout with navigation
- chat.html: Chat interface with document list
- landing.html: Welcome page

### Backend (Python/Flask)

**app/__init__.py** - Flask application factory:
- Creates Flask app instance
- Initializes database
- Registers route blueprints
- Sets up cache-control headers
- Creates database tables

**config.py** - Configuration management:
- Database URI (SQLite)
- Flask settings
- Upload folder path
- Ollama API endpoints and model names

**models.py** - Database models and fallback search:
- `Document`: Stores uploaded file metadata (name, size, status, hash)
- `DocumentChunk`: Text chunks extracted from documents
- `Embedding`: Vector embeddings for chunks
- `vector_search()`: Fallback search using Jaccard similarity (if FAISS fails)

**vector_store.py** - FAISS vector database:
- `add_to_faiss()`: Adds chunk embeddings to FAISS index
- `search_faiss()`: Finds k most similar chunks
- Uses SentenceTransformer (all-MiniLM-L6-v2) for embeddings
- Stores text and metadata in-memory (resets on server restart)

### Services

**rag.py** - Main RAG orchestration:
- `rag_pipeline()`: Main entry point
- Security validation via guardrails
- Intent classification (DOCUMENT/GENERAL/NONLEGAL)
- Calls vector search
- Constructs LLM prompt with document context
- Extracts citations from LLM response
- Returns final response with citations

**guardrails.py** - Security validation:
- `classify()`: Returns 'SAFE' or 'UNSAFE'
- Checks for SQL injection, prompt injection, jailbreak attempts
- Blocks dangerous prompt patterns

**ingestion.py** - Document processing:
- `extract_pdf_text()`: Extracts text from PDF (max 20 pages)
- `extract_docx_text()`: Extracts paragraphs from DOCX
- `chunk_text()`: Splits text into 1200-char chunks
- `is_likely_legal_document()`: Heuristic classification
- `index_document()`: Main entry point, orchestrates entire flow

**ollama_client.py** - Ollama LLM API:
- `chat_with_ollama()`: Sends message to Ollama chat endpoint
- `embed_texts()`: Generates embeddings for text chunks
- Handles connection errors with fallback responses

**background.py** - Async indexing:
- `index_document_async()`: Spawns background thread
- Calls sync indexing function
- Updates document status: "indexed", "index_failed"
- Handles exceptions in background thread

### Routes (Flask Blueprints)

**pages.py** - Page routes:
- GET `/`: Renders landing page
- GET `/chat`: Renders chat interface
- GET `/landing`: Renders welcome page

**chat.py** - Chat API:
- POST `/api/chat`: Submit query, returns LLM response with citations

**upload.py** - Document management API:
- POST `/api/upload`: Upload document file
- GET `/api/documents`: List all documents
- DELETE `/api/documents/<id>`: Delete document
- GET `/api/documents/<id>/status`: Check indexing status

**ingest.py** - Indexing API:
- POST `/api/index/<id>`: Manually trigger document indexing

## Data Storage

### SQLite Database
- **documents**: File metadata and status
- **document_chunks**: Text segments with document references
- **embeddings**: Vector embeddings for chunks

### In-Memory FAISS Index
- Stores embeddings during runtime (cleared on server restart)
- Dimension: 384 (from all-MiniLM-L6-v2 model)
- Search type: Flat L2 distance scoring
- Persists with metadata: chunk text, document ID, chunk position

### File System
- Uploaded documents stored in `uploads/` directory
- Hashed for duplicate detection
- Preserved after indexing (not deleted)

## Intent Classification

The system classifies queries as:

- **DOCUMENT**: Contains legal keywords and is specific to documents
- **GENERAL**: General legal knowledge question
- **NONLEGAL**: Not a legal question

Based on classification:
- DOCUMENT: Returns answer from vector search results
- GENERAL: Returns general legal knowledge (if documents insufficient)
- NONLEGAL: Returns message that system answers legal questions only

## Citation Format

Citations extracted from LLM response show:
- Document number: [Document 1], [Document 2], etc.
- Maps to source filename
- Displayed inline in response

Example response with citations:
```
The contract term is 5 years [Document 1]. 
Extensions are possible with written notice [Document 2].
```

## Model Information

**LLM**: phi3:mini via Ollama
- Lightweight model suitable for local inference
- ~4GB memory footprint
- Balanced speed and quality for legal questions

**Embeddings**: nomic-embed-text via Ollama
- Generates 384-dimensional vectors
- Optimized for semantic similarity
- Runs locally for privacy

**Search Model**: SentenceTransformer all-MiniLM-L6-v2
- Alternative embedding for fallback search
- Pre-trained on semantic similarity tasks
