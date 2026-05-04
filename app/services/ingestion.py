from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader

from ..extensions import db
from ..models import Document, DocumentChunk, Embedding
from .ollama_client import embed_texts
from ..vector_store import add_to_faiss


LEGAL_SIGNALS = {
    "act", "section", "rule", "article", "court", "judge", "judgment", "judgement",
    "order", "tribunal", "petition", "appeal", "ipc", "crpc", "cpc", "constitution",
    "legal", "law", "plaintiff", "defendant", "lease", "property", "land",
    "registration", "stamp duty", "revenue", "mutation",
}


def extract_pdf_text(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        extracted_text = []
        
        idx = 0
        for page in reader.pages:
            if idx >= 20:
                break
            try:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    extracted_text.append(page_text.strip())
            except Exception as e:
                print(f"Page {idx} extraction error: {e}")
            idx +=1
        
        text = ""
        if extracted_text:
            text = "\n\n".join(extracted_text)

        if text and len(text) > 100:
            return text
        return ""
    
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


def extract_docx_text(file_path: str) -> str:
    try:
        document = DocxDocument(file_path)
        lines = []
        for paragraph in document.paragraphs:
            stripped = paragraph.text.strip()
            if stripped:
                lines.append(stripped)
        return "\n".join(lines)
    except Exception as e:
        print(f"DOCX extraction error: {e}")
        return ""


def extract_document_text(document: Document) -> str:
    file_path = Path(document.storage_path)
    file_ext = file_path.suffix.lower()
    
    if file_ext == ".pdf":
        return extract_pdf_text(str(file_path))
    elif file_ext == ".docx":
        return extract_docx_text(str(file_path))
    
    return ""


def chunk_text(text: str, chunk_size: int = 1200) -> list:
    if not text:
        return []
    
    paragraphs = []
    for p in text.split('\n\n'):
        stripped = p.strip()
        if stripped:
            paragraphs.append(stripped)
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        chunk_len = len(current_chunk) + len(paragraph) + 100
        if chunk_len > chunk_size:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def is_likely_legal_document(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    return len(normalized) > 10


def index_document(document_id: int) -> dict:
    document = db.session.get(Document, document_id)
    if not document:
        return {"ok": False, "error": "Document not foun d"}

    text = extract_document_text(document)
    
    if not text:
        placeholder_text = f"[Document] {document.original_name}'s text extraction not available."
        chunks = [placeholder_text]
        vectors = embed_texts(chunks)
        
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            chunk_text=placeholder_text,
            chunk_metadata={
                "document_id": document.id,
                "filename": document.original_name,
                "source": "scanned_document",
            },
        )
        db.session.add(chunk)
        db.session.flush()

        embedding = Embedding(
            chunk_id=chunk.id,
            embedding_model="ollama",
            embedding=vectors[0],
        )
        db.session.add(embedding)

        add_to_faiss(
            [placeholder_text],
            [{"document_id": document.id}]
        )
        
        document.status = "indexed"
        db.session.commit()
        return {
            "ok": True,
            "document_id": document.id,
            "chunks": 1,
            "note": "Scanned document (placeholder)"
        }
    
    if not is_likely_legal_document(text):
        document.status = "rejected_non_legal"
        db.session.commit()
        return {
            "ok": False,
            "error": "Document does not appear to contain legal content",
        }

    chunks = chunk_text(text)
    if not chunks:
        document.status = "failed"
        db.session.commit()
        return {"ok": False, "error": "No text extracted from document"}

    vectors = embed_texts(chunks)
    if len(vectors) != len(chunks):
        document.status = "failed"
        db.session.commit()
        return {"ok": False, "error": "Embedding generation failed"}

    existing_chunks = DocumentChunk.query.filter_by(document_id=document.id).all()
    if existing_chunks:
        existing_ids = []
        for chunk in existing_chunks:
            existing_ids.append(chunk.id)
        Embedding.query.filter(Embedding.chunk_id.in_(existing_ids)).delete(synchronize_session=False)
        DocumentChunk.query.filter_by(document_id=document.id).delete(synchronize_session=False)
        db.session.flush()

    faiss_chunks = []
    faiss_metadata = []

    for chunk_index in range(len(chunks)):
        chunk_text_content = chunks[chunk_index]
        vector = vectors[chunk_index]
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=chunk_index,
            chunk_text=chunk_text_content,
            chunk_metadata={
                "document_id": document.id,
                "filename": document.original_name,
                "source": "user_upload",
            },
        )
        db.session.add(chunk)
        db.session.flush()

        embedding = Embedding(
            chunk_id=chunk.id,
            embedding_model="ollama",
            embedding=vector,
        )
        db.session.add(embedding)

        faiss_chunks.append(chunk_text_content)
        faiss_metadata.append({
            "document_id": document.id
        })

    add_to_faiss(faiss_chunks, faiss_metadata)

    document.status = "indexed"
    db.session.commit()
    
    return {
        "ok": True,
        "document_id": document.id,
        "chunks": len(chunks)
    }