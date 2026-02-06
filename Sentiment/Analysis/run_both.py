"""
Unified script to run both semantic and sentiment pipelines
"""

# Import the semantic pipeline function
from Sentiment.Analysis.semantic_filter.semantic_pipeline import SemanticPipeline

# Import the SentimentPipeline class
from Sentiment.Analysis.ochestration.pipe import SentimentPipeline
from Sentiment.Analysis.storage.store import SentimentStorage
from Sentiment.Analysis.semantic_filter.filter_service import FilterService

# Import other necessary dependencies

from Sentiment.Analysis.data_collector.news_api import APIData
from Sentiment.Analysis.preprocessing.cleaner import TextCleaner
from Sentiment.Analysis.sentiment_model.bert import SentimentModel

def main():
    """
    Main function to run both pipelines sequentially
    """
    print("=" * 50)
    print("Starting Sentiment Pipeline...")
    print("=" * 50)
    
    # Initialize components for sentiment pipeline
    # Adjust these initializations based on your actual code structure
    api_data = APIData()  # or however you initialize this
    cleaner = TextCleaner()  # or however you initialize this
    sentiment_model = SentimentModel()  # or however you initialize this
    
    # Create and run the sentiment pipeline
    pipeline = SentimentPipeline(api_data, cleaner, sentiment_model)
    pipeline.run_pipeline()  # Adjust method name if different
    
    print("\nSentiment Pipeline completed!")
    print("=" * 50)
    
    print("Starting Semantic Pipeline...")
    print("=" * 50)
    
    # Run the semantic pipeline
    semantic_pipeline = SemanticPipeline(SentimentStorage(), FilterService())
    semantic_pipeline.run_semantic_pipeline()
    
    print("=" * 50)
    print("\nSemantic Pipeline completed!")
    
    



if __name__ == "__main__":
    results = main()
    print("\nBoth pipelines completed successfully!")