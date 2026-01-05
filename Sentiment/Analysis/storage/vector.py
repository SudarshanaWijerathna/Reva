# For simplicity, using Chroma
from chromadb import Client
try:
    from chromadb import PersistentClient
except ImportError:
    PersistentClient = None
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

class VectorRepo:
    def __init__(self, collection_name):
        self.persist_directory = "./chroma_store"

        if PersistentClient:
            self.client = PersistentClient(path=self.persist_directory)
        else:
            self.client = Client(
                Settings(
                    persist_directory=self.persist_directory,
                    anonymized_telemetry=False
                )
            )

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def count(self):
        return self.collection.count()

    def add_reference(self, doc_id, text):
        embedding = self.model.encode(text).tolist()
        self.collection.add(
            ids=[str(doc_id)],
            embeddings=[embedding],
            documents=[text]
        )
        # Ensure the data is flushed to disk for the next process run.
        if hasattr(self.client, "persist"):
            self.client.persist()

    def get_all_embeddings(self):
        return self.collection.get(include=["embeddings"])["embeddings"]
