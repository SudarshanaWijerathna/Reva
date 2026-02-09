from Sentiment.Analysis.storage.vector import VectorRepo
from Sentiment.Analysis.storage.knowledge_base import knowledge, ShortTerm, MediumTerm, LongTerm  # your predefined KB

def initialize_kb():
    vector_repo_ref = VectorRepo(collection_name="reference_vectors")
    vector_repo_short = VectorRepo(collection_name="short_term_vectors")
    vector_repo_medium = VectorRepo(collection_name="medium_term_vectors")
    vector_repo_long = VectorRepo(collection_name="long_term_vectors")

    for i, sentence in enumerate(knowledge):
        vector_repo_ref.add_reference(
            doc_id=f"kb_{i}",
            text=sentence
        )
    print("Knowledge base initialized.")

    for i, sentence in enumerate(ShortTerm):
        vector_repo_short.add_reference(
            doc_id=f"short_{i}",
            text=sentence
        )
    print("Short-term knowledge base initialized.")

    for i, sentence in enumerate(MediumTerm):
        vector_repo_medium.add_reference(
            doc_id=f"medium_{i}",
            text=sentence
        )
    print("Medium-term knowledge base initialized.")

    for i, sentence in enumerate(LongTerm):
        vector_repo_long.add_reference(
            doc_id=f"long_{i}",
            text=sentence
        )
    print("Long-term knowledge base initialized.")

    count = vector_repo_ref.count()
    print(f"Total reference embeddings in KB: {count}✅✅✅")
    print(f"Total short-term embeddings in KB: {vector_repo_short.count()}✅✅✅")
    print(f"Total medium-term embeddings in KB: {vector_repo_medium.count()}✅✅✅")
    print(f"Total long-term embeddings in KB: {vector_repo_long.count()}✅✅✅")

if __name__ == "__main__":
    initialize_kb()
