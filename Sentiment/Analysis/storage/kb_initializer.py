from Sentiment.Analysis.storage.vector import VectorRepo
from Sentiment.Analysis.storage.knowledge_base import knowledge, ShortTerm, MediumTerm, LongTerm, RentalMarket, HouseMarket, LandMarket  # your predefined KB

def initialize_kb():
    vector_repo_ref = VectorRepo(collection_name="reference_vectors")
    vector_repo_short = VectorRepo(collection_name="short_term_vectors")
    vector_repo_medium = VectorRepo(collection_name="medium_term_vectors")
    vector_repo_long = VectorRepo(collection_name="long_term_vectors")
    vector_repo_rental = VectorRepo(collection_name="rental_market_vectors")
    vector_repo_house = VectorRepo(collection_name="house_market_vectors")
    vector_repo_land = VectorRepo(collection_name="land_market_vectors")

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

    for i, sentence in enumerate(RentalMarket):
        vector_repo_rental.add_reference(
            doc_id=f"rental_{i}",
            text=sentence
        )
    print("Rental market knowledge base initialized.")

    for i, sentence in enumerate(HouseMarket):
        vector_repo_house.add_reference(
            doc_id=f"house_{i}",
            text=sentence
        )
    print("House market knowledge base initialized.")

    for i, sentence in enumerate(LandMarket):
        vector_repo_land.add_reference(
            doc_id=f"land_{i}",
            text=sentence
        )
    print("Land market knowledge base initialized.")

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
    print(f"Total rental market embeddings in KB: {vector_repo_rental.count()}✅✅✅")
    print(f"Total house market embeddings in KB: {vector_repo_house.count()}✅✅✅")
    print(f"Total land market embeddings in KB: {vector_repo_land.count()}✅✅✅")

if __name__ == "__main__":
    initialize_kb()
