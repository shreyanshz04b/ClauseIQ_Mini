import threading
from flask import current_app
from ..extensions import db
from ..models import Document
from .ingestion import index_document as _index_document_sync


def index_document_async(document_id: int):
    
    app = current_app._get_current_object()
    
    def _do_index():
        try:
            with app.app_context():
                print(f" Starting index for document {document_id}")
                result = _index_document_sync(document_id)
                
                if result.get("ok"):
                    doc = db.session.get(Document, document_id)
                    if doc:
                        doc.status = "indexed"
                        db.session.commit()
                        print(f" Document {document_id} indexed successfully")
                else:
                    doc = db.session.get(Document, document_id)
                    if doc:
                        doc.status = "index_failed"
                        db.session.commit()
                        print(f" Document {document_id} indexing failed: {result.get('error')}")
        except Exception as e:
            print(f" Error indexing document {document_id}: {e}")
            try:
                with app.app_context():
                    doc = db.session.get(Document, document_id)
                    if doc:
                        doc.status = "index_failed"
                        db.session.commit()
            except:
                pass
    
    thread = threading.Thread(target=_do_index, daemon=True)
    thread.start()
