# For simplicity, using Chroma
import os
import logging
from chromadb import Client
try:
    from chromadb import PersistentClient
except ImportError:
    PersistentClient = None
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class VectorRepo:
    def __init__(self, collection_name):
        try:
            self.persist_directory = "Sentiment/chroma_store"
            
            # Create directory if it doesn't exist
            try:
                os.makedirs(self.persist_directory, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create persist directory: {e}")
                raise

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
        except Exception as e:
            logger.error(f"Error initializing VectorRepo: {e}")
            raise

    def count(self):
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error counting collection: {e}")
            return 0

    def add_reference(self, doc_id, text):
        try:
            if not text or not isinstance(text, str):
                raise ValueError("Text must be a non-empty string")
            
            embedding = self.model.encode(text).tolist()
            self.collection.add(
                ids=[str(doc_id)],
                embeddings=[embedding],
                documents=[text]
            )
            # Ensure the data is flushed to disk for the next process run.
            if hasattr(self.client, "persist"):
                self.client.persist()
        except ValueError as e:
            logger.error(f"Invalid input for add_reference: {e}")
            raise
        except Exception as e:
            logger.error(f"Error adding reference with doc_id {doc_id}: {e}")
            raise

    def get_all_embeddings(self):
        try:
            embeddings = self.collection.get(include=["embeddings"])["embeddings"]
            if embeddings is None:
                logger.warning("No embeddings found in collection")
                return []
            return embeddings
        except KeyError as e:
            logger.error(f"Embeddings key not found in collection response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error retrieving embeddings: {e}")
            return []
