import hashlib
import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import Document, DocumentChunk, Embedding
from ..services.background import index_document_async

upload_bp = Blueprint("upload", __name__)
ALLOWED_EXTENSIONS = {"pdf", "docx"}
BLOCKED_EXTENSIONS = {"exe", "txt", "sh", "bat", "cmd", "com", "scr", "jar", "py", "js"}


def is_file_allowed(filename):
    if "." not in filename:
        return False, "Invalid file: no extension found"
    
    ext = filename.rsplit(".", 1)[1].lower()
    
    if ext in BLOCKED_EXTENSIONS:
        return False, f"File type .{ext} is not accepted. Only PDF and DOCX files are allowed."
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type .{ext} is not allowed. Only PDF and DOCX files are accepted."
    
    return True, ""


@upload_bp.post("/upload")
def upload_file():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "File missing"}), 400
    
    is_allowed, error_msg = is_file_allowed(file.filename)
    if not is_allowed:
        return jsonify({"error": error_msg}), 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    max_bytes = current_app.config["MAX_UPLOAD_MB"] * 1024 * 1024
    if file_size > max_bytes:
        max_mb = current_app.config["MAX_UPLOAD_MB"]
        actual_mb = file_size / (1024 * 1024)
        error_msg = f"File size error: {actual_mb:.1f} MB exceeds the maximum allowed size of {max_mb} MB"
        return jsonify({"error": error_msg}), 400

    hasher = hashlib.sha256()
    while True:
        chunk = file.read(8192)
        if not chunk:
            break
        hasher.update(chunk)
    file_sha256 = hasher.hexdigest()
    file.seek(0)

    existing = Document.query.filter_by(sha256=file_sha256).first()
    if existing:
        return jsonify({"ok": True, "document_id": existing.id, "status": "duplicate"})

    safe_name = secure_filename(file.filename)
    storage_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"{file_sha256}_{safe_name}")
    file.save(storage_path)

    document = Document(
        user_id=1,
        original_name=file.filename,
        storage_path=storage_path,
        mime_type=file.mimetype or "application/octet-stream",
        file_size=file_size,
        sha256=file_sha256,
        status="awaiting_index",
    )
    db.session.add(document)
    db.session.commit()
    index_document_async(document.id)

    return jsonify({
        "ok": True,
        "document_id": document.id,
        "status": "awaiting_index",
        "message": "Document uploaded. Indexing in progress...",
    })


@upload_bp.get("/documents")
def list_documents():
    documents = Document.query.order_by(Document.created_at.desc()).all()
    
    doc_list = []
    for doc in documents:
        doc_list.append({
            "id": doc.id,
            "name": doc.original_name,
            "status": doc.status,
            "size": doc.file_size,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        })
    
    return jsonify({
        "ok": True,
        "documents": doc_list,
    })


@upload_bp.delete("/documents/<int:document_id>")
def delete_document(document_id):
    document = db.session.get(Document, document_id)
    if not document:
        return jsonify({"error": "Document not found"}), 404

    chunks = DocumentChunk.query.filter_by(document_id=document.id).all()
    chunk_ids = []
    for chunk in chunks:
        chunk_ids.append(chunk.id)
    
    if chunk_ids:
        Embedding.query.filter(Embedding.chunk_id.in_(chunk_ids)).delete(synchronize_session=False)
    
    DocumentChunk.query.filter_by(document_id=document.id).delete(synchronize_session=False)

    file_path = document.storage_path
    db.session.delete(document)
    db.session.commit()

    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    return jsonify({"ok": True, "deleted": document_id})


@upload_bp.get("/documents/<int:document_id>/status")
def document_status(document_id):
    doc = db.session.get(Document, document_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    
    return jsonify({
        "id": doc.id,
        "name": doc.original_name,
        "status": doc.status,
        "created_at": doc.created_at.isoformat() if doc.created_at else None
    })
