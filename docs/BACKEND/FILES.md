# Backend Files Documentation

## Core Files

### app/config.py
**Purpose**: Centralized configuration management for the Flask application.

**Key Variables**:
- `SQLALCHEMY_DATABASE_URI`: SQLite database path
- `SQLALCHEMY_TRACK_MODIFICATIONS`: Disable SQLAlchemy modification tracking
- `UPLOAD_FOLDER`: Directory for uploaded files
- `MAX_CONTENT_LENGTH`: Max file size limit
- `OLLAMA_BASE_URL`: Ollama service address
- `OLLAMA_CHAT_MODEL`: Model name for chat ("phi3:mini")
- `OLLAMA_EMBED_MODEL`: Model name for embeddings ("nomic-embed-text")

**Usage**: Loaded by Flask app factory via `app.config.from_object(Config)`

**Dependencies**: None

---

### app/extensions.py
**Purpose**: Initialize Flask extensions (database ORM).

**Key Variables**:
- `db`: SQLAlchemy database object for ORM operations

**Usage**: Imported and used throughout the app for database access

**Dependencies**: Flask-SQLAlchemy

---

### app/__init__.py
**Purpose**: Flask application factory - creates and configures the app instance.

**Key Functions**:
- `create_app()`: Main factory function
  - Creates Flask instance
  - Loads configuration
  - Initializes database
  - Registers route blueprints
  - Sets up cache-control headers
  - Creates database tables

**Route Registration**:
- pages_bp: "/" routes (home, chat, landing)
- upload_bp: "/api" + upload/document routes
- ingest_bp: "/api" + indexing routes
- chat_bp: "/api" + chat endpoint

**Middleware**:
- `add_no_cache_headers()`: Prevents browser caching of non-static routes

**Usage**: Entry point called by `run.py`

**Dependencies**: Flask, SQLAlchemy, dotenv

---

## Database & Models

### app/models.py
**Purpose**: SQLAlchemy ORM models and vector search implementation.

**Database Models**:

**Document**:
- `id`: Primary key
- `name`: Original filename
- `file_hash`: SHA256 hash for duplicate detection
- `size`: File size in bytes
- `status`: "pending", "indexed", "index_failed", "rejected_non_legal"
- `created_at`: Upload timestamp
- Relationship: One-to-many with DocumentChunk

**DocumentChunk**:
- `id`: Primary key
- `document_id`: Foreign key to Document
- `chunk_index`: Position in document
- `text`: Chunk text content (up to 1200 chars)
- `created_at`: Creation timestamp

**Embedding**:
- `id`: Primary key
- `document_chunk_id`: Foreign key to DocumentChunk
- `embedding`: Vector embedding (stored as binary)
- Relationship: One-to-one with DocumentChunk

**Key Functions**:

`vector_search(qvec, limit=4)`:
- Fallback search using Jaccard similarity (if FAISS unavailable)
- Takes query embedding vector as input
- Returns top `limit` chunks by similarity score
- Algorithm: Intersection/union ratio of query words vs chunk words
- Returns tuples: (chunk_text, document_id, score)

**Dependencies**: SQLAlchemy, numpy

---

### app/vector_store.py
**Purpose**: FAISS vector database operations for semantic search.

**Global Variables**:
- `texts[]`: List of chunk text content
- `metadatas[]`: List of metadata dicts {chunk_id, document_id, ...}
- `index`: FAISS IndexFlatIP instance
- `model`: SentenceTransformer("all-MiniLM-L6-v2")

**Key Functions**:

`add_to_faiss(chunks, metadata_list)`:
- Input: List of DocumentChunk objects and metadata
- Generates embeddings for each chunk
- Adds embeddings to FAISS index
- Stores text and metadata in global lists

`search_faiss(query, k=5)`:
- Input: Query string, number of results
- Generates embedding for query text
- Searches FAISS index for k nearest neighbors
- Returns: List of tuples (chunk_text, metadata)

**Index Details**:
- Type: IndexFlatIP (inner product)
- Dimension: 384 (from all-MiniLM-L6-v2 model)
- Distance metric: L2 normalization
- In-memory only (cleared on server restart)

**Dependencies**: FAISS, SentenceTransformer

---

## Services

### app/services/rag.py
**Purpose**: Main RAG pipeline orchestration - coordinates query flow.

**Key Functions**:

`rag_pipeline(query)`:
- Main entry point for chat requests
- Orchestrates entire RAG flow
- Returns dict: {answer, classification, citations, contexts}

**Pipeline Steps**:
1. Security check via `guardrails.classify(query)`
   - If UNSAFE: Return "Query blocked for security"
2. Intent classification:
   - Count legal keywords in query
   - Classify as DOCUMENT, GENERAL, or NONLEGAL
3. Vector search via `search_faiss(query, k=5)`
   - Get top 5 similar document chunks
4. If no documents found:
   - Return "No documents to search"
5. Format LLM prompt:
   - System message: Role-play as legal assistant
   - Context: Document chunks with [Document N] references
   - User query
6. Call Ollama chat model
7. Extract citations:
   - Regex-free parsing of "[Document N]" patterns
   - Map document numbers to filenames
8. Return response with citations

**Citation Extraction**:
- Parses response for patterns like "[Document 1]"
- No regex used (manual string parsing)
- Returns list of source document names

**Key Keyword Lists**:
- `LEGAL_KEYWORDS`: Contract, agreement, liability, etc.
- `DOCUMENT_KEYWORDS`: Clause, section, paragraph, etc.

**Dependencies**: guardrails, ollama_client, vector_store, models

---

### app/services/guardrails.py
**Purpose**: Security validation - block unsafe/malicious queries.

**Key Functions**:

`classify(text)`:
- Input: User query string
- Output: "SAFE" or "UNSAFE"
- Checks query against dangerous patterns

**Safety Checks**:
- SQL injection patterns (SELECT, DROP, DELETE, etc.)
- Prompt injection attempts (ignore, forget, override, etc.)
- Jailbreak attempts (confused, pretend, act as, etc.)
- Character escaping (quotes, semicolons in dangerous contexts)

**Pattern Matching**:
- Case-insensitive search
- Space-separated keyword detection
- Simple string containment (no regex)

**Dependencies**: None

---

### app/services/ingestion.py
**Purpose**: Document processing pipeline - extract, chunk, embed, index.

**Key Functions**:

`extract_pdf_text(file_path)`:
- Input: Path to PDF file
- Output: Full text concatenation
- Uses pypdf library
- Limit: First 20 pages only
- Returns: Combined text from all pages

`extract_docx_text(file_path)`:
- Input: Path to DOCX file
- Output: Full text concatenation
- Uses python-docx library
- Extracts all non-empty paragraph text
- Returns: Newline-separated paragraphs

`chunk_text(text)`:
- Input: Full document text
- Output: List of 1200-character chunks
- Chunks on paragraph boundaries when possible
- Overlap: None (no duplication)

`is_likely_legal_document(text)`:
- Input: Document text
- Output: Boolean (legal or not)
- Checks for legal keywords: party, hereby, whereas, etc.
- Heuristic only (not strict classification)

`index_document(document_id)`:
- Main entry point
- Orchestrates entire indexing flow
- Returns: {ok, chunks, message/error}

**Indexing Flow**:
1. Get document record from database
2. Check document status
3. Extract text based on file extension
4. Legal document check (informational)
5. Split text into chunks
6. Generate embeddings via Ollama
7. Save chunks to database
8. Add chunks to FAISS index
9. Update document status to "indexed"
10. Return success with chunk count

**Dependencies**: models, vector_store, ollama_client, database, pypdf, python-docx

---

### app/services/ollama_client.py
**Purpose**: Wrapper for Ollama LLM API - chat and embeddings.

**Key Functions**:

`chat_with_ollama(messages)`:
- Input: List of message dicts [{role, content}, ...]
- Output: String response from model
- Calls Ollama /api/chat endpoint
- Streams response and concatenates
- Error handling: Returns error message on connection failure

`embed_texts(texts)`:
- Input: List of strings to embed
- Output: List of embedding vectors
- Calls Ollama /api/embeddings endpoint
- Returns embeddings as numpy arrays
- Error handling: Returns fallback embeddings on failure

**API Details**:
- Base URL: From config.OLLAMA_BASE_URL (default: http://localhost:11434)
- Chat model: phi3:mini
- Embed model: nomic-embed-text
- Timeout: 60 seconds for requests

**Error Handling**:
- Connection errors: Return default responses
- Parse errors: Log and return fallback data
- No retry logic (single attempt)

**Dependencies**: requests, numpy, config

---

### app/services/background.py
**Purpose**: Async document indexing - prevents blocking user requests.

**Key Functions**:

`index_document_async(document_id)`:
- Spawns background thread for indexing
- Main thread returns immediately
- Background thread orchestrates indexing

**Background Processing**:
1. Creates Flask app context (for DB access)
2. Calls sync `index_document()` from ingestion
3. Updates document status:
   - "indexed" if successful
   - "index_failed" if error
4. Commits status change to database
5. Handles exceptions gracefully

**Threading**:
- Daemon thread (exits when main app exits)
- No thread pooling (each document = new thread)
- Suitable for small-to-medium scale usage

**Dependencies**: threading, Flask app context, ingestion, database

---

## Routes (Flask Blueprints)

### app/routes/pages.py
**Purpose**: HTML page routing - serve templates.

**Routes**:
- `GET /`: Renders landing.html (welcome page)
- `GET /chat`: Renders chat.html (main chat interface)
- `GET /landing`: Renders landing.html (alternate path)

**Template Variables**: None (static pages)

**Dependencies**: Flask, templates

---

### app/routes/chat.py
**Purpose**: Chat API endpoint - process user queries.

**Routes**:
- `POST /api/chat`: Submit query, get LLM response

**Request Body**:
```json
{
  "query": "What is the contract term?"
}
```

**Response Body**:
```json
{
  "response": "The contract term is 5 years...",
  "classification": "DOCUMENT",
  "citations": ["contract.pdf", "agreement.docx"],
  "contexts": [...]
}
```

**Error Handling**:
- Empty query: 400 "Query required"
- NO_DOCUMENTS: 400 with error message
- UNSAFE query: 400 with security message
- Success: 200 with response and citations

**Validation**:
- Query stripped of whitespace
- Empty queries rejected

**Dependencies**: Flask, rag_pipeline

---

### app/routes/upload.py
**Purpose**: Document management API - upload, list, delete documents.

**Routes**:

`POST /api/upload`:
- Upload new document file
- Request: multipart form data with file
- Response: {ok, document_id, status, message,index_path}
- Creates database record
- Saves file to disk
- Triggers async indexing

`GET /api/documents`:
- List all uploaded documents
- Response: {ok, documents: [{id, name, size, status, ...}]}
- No pagination

`DELETE /api/documents/<id>`:
- Delete document and related data
- Deletes: document record, chunks, embeddings
- Removes: file from disk
- Updates: vector store indices

`GET /api/documents/<id>/status`:
- Check document indexing status
- Response: {ok, status, message}

**Validation**:
- Duplicate detection via SHA256 hash
- File size limits via config
- Allowed extensions: PDF, DOCX

**Dependencies**: Flask, request, database, ingestion, background

---

### app/routes/ingest.py
**Purpose**: Document indexing API - trigger manual indexing.

**Routes**:

`POST /api/index/<document_id>`:
- Manually trigger document indexing
- For documents that failed auto-indexing
- Response: {ok, chunks, message/error}
- Calls sync `index_document()` directly

**Error Handling**:
- Document not found: 404
- Indexing failed: 400 with error
- Success: 200 with chunk count

**Dependencies**: Flask, database, ingestion
