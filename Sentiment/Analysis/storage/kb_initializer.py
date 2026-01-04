from Analysis.storage.vector import VectorRepo
from Analysis.storage.knowledge_base import knowledge   # your predefined KB

def initialize_kb():
    vector_repo = VectorRepo()

    for i, sentence in enumerate(knowledge):
        vector_repo.add_reference(
            doc_id=f"kb_{i}",
            text=sentence
        )

    print("Knowledge base initialized.")

    count = vector_repo.count()
    print(f"Total reference embeddings in KB: {count}✅✅✅")

if __name__ == "__main__":
    initialize_kb()
