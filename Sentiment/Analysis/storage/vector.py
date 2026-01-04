# For simplicity, using Chroma
from chromadb import Client
from sentence_transformers import SentenceTransformer

class VectorRepo:
    def __init__(self, collection_name="reference_vectors"):
        self.client = Client()
        try:
            self.collection = self.client.get_collection(collection_name)
        except Exception:
            self.collection = self.client.create_collection(collection_name)

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def add_reference(self, doc_id, text):
        embedding = self.model.encode(text).tolist()
        self.collection.add(
            ids=[str(doc_id)],
            embeddings=[embedding],
            documents=[text]
        )

    def get_all_embeddings(self):
        return self.collection.get(include=["embeddings"])["embeddings"]
