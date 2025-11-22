class SimpleRAG:
    """
    Simple keyword-based retrieval.
    Real version will use embeddings + vector DB.
    """

    def __init__(self):
        self.docs = []

    def index(self, doc_id: str, text: str):
        self.docs.append({"id": doc_id, "text": text})

    def search(self, query: str, k=5):
        query = query.lower()
        results = [d for d in self.docs if query in d["text"].lower()]
        return results[:k]
