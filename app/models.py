from datetime import datetime
from sqlalchemy import text

from .extensions import db


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.Text, nullable=False)
    mime_type = db.Column(db.String(120), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    sha256 = db.Column(db.String(64), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="uploaded")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class DocumentChunk(db.Model):
    __tablename__ = "document_chunks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    document_id = db.Column(db.BigInteger, nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    chunk_text = db.Column(db.Text, nullable=False)
    chunk_metadata = db.Column("metadata", db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Embedding(db.Model):
    __tablename__ = "embeddings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chunk_id = db.Column(db.BigInteger, nullable=False)
    embedding_model = db.Column(db.String(120), nullable=False)
    embedding = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)



def vector_search(qvec, limit=4):
    try:
        from .vector_store import search_faiss

        query = ""
        if isinstance(qvec, str):
            query = qvec
        elif isinstance(qvec, list) and len(qvec) > 0 and isinstance(qvec[0], str):
            query = qvec[0]

        results = search_faiss(query, k=limit)

        if results:
            return results

    except Exception as e:
        print(f"FAISS error, falling back: {e}")

    try:
        q = ""
        if isinstance(qvec, str):
            q = qvec
        elif isinstance(qvec, list) and len(qvec) > 0 and isinstance(qvec[0], str):
            q = qvec[0]

        all_chunks = db.session.query(DocumentChunk).all()
        if not all_chunks:
            return []

        scored = []
        q_words = set()
        for w in q.split():
            if len(w) > 2:
                q_words.add(w.lower())

        for chunk in all_chunks:
            txt = chunk.chunk_text.lower()
            chunk_words = set()
            for w in txt.split():
                if len(w) > 2:
                    chunk_words.add(w.lower())

            if q_words and chunk_words:
                intersection = len(q_words & chunk_words)
                union = len(q_words | chunk_words)
                if union > 0:
                    score = intersection / union
                else:
                    score = 0
            else:
                score = 0

            if score > 0:
                scored.append((chunk.chunk_text, chunk.chunk_metadata, score))

        idx = 0
        while idx < len(scored):
            jdx = idx + 1
            while jdx < len(scored):
                if scored[jdx][2] > scored[idx][2]:
                    temp = scored[idx]
                    scored[idx] = scored[jdx]
                    scored[jdx] = temp
                jdx += 1
            idx += 1

        res = []
        for i in range(len(scored)):
            if i >= limit:
                break
            item = scored[i]
            res.append((item[0], item[1]))

        return res

    except Exception as e:
        print(f"vector search error: {e}")
        return []