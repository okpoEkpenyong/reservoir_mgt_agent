import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(384)
        self.docs = []

    def add(self, text: str, meta: dict):
        vector = self.model.encode([text]).astype("float32")
        self.index.add(vector)
        self.docs.append({"text": text, "meta": meta})

    def search(self, query: str, k=5):
        v = self.model.encode([query]).astype("float32")
        distances, idxs = self.index.search(v, k)

        results = []
        for i in idxs[0]:
            if i < len(self.docs):
                results.append(self.docs[i])
        return results
