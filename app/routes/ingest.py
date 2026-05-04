from flask import Blueprint, jsonify

from ..extensions import db
from ..models import Document
from ..services.ingestion import index_document

ingest_bp = Blueprint("ingest", __name__)


@ingest_bp.post("/index/<int:document_id>")
def index_uploaded_document(document_id: int):
    doc = db.session.get(Document, document_id)
  
    result = index_document(document_id)
    if not result.get("ok"):
        return jsonify(result), 400
    return jsonify(result)
