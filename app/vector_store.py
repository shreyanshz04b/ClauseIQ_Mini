import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
dimension = 384
index = faiss.IndexFlatIP(dimension)

texts = []
metadatas = []


def add_to_faiss(chunks, metadata_list):
    global texts, metadatas

    if not chunks:
        return

    embeddings = model.encode(chunks)
    embeddings = np.array(embeddings).astype('float32')
    faiss.normalize_L2(embeddings)

    index.add(embeddings)
    texts.extend(chunks)
    metadatas.extend(metadata_list)


def search_faiss(query, k=5):
    if len(texts) == 0:
        return []

    query_vec = model.encode([query])
    query_vec = np.array(query_vec).astype('float32')
    faiss.normalize_L2(query_vec)

    distances, indices = index.search(query_vec, k)

    results = []
    for idx in indices[0]:
        if idx < len(texts):
            results.append((texts[idx], metadatas[idx]))

    return results