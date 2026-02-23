"""
Unified script to run both semantic and sentiment pipelines
"""

# Import the semantic pipeline function
from Sentiment.Analysis.semantic_filter.semantic_pipeline import SemanticPipeline

# Import the SentimentPipeline class
from Sentiment.Analysis.ochestration.pipe import SentimentPipeline
from Sentiment.Analysis.storage.store import SentimentStorage

# Import other necessary dependencies

from Sentiment.Analysis.data_collector.news_api import APIData
from Sentiment.Analysis.data_collector.news_scrap import news_scraper
from Sentiment.Analysis.data_collector.web import web_scraper
from Sentiment.Analysis.ochestration.cleaner import TextCleaner
from Sentiment.Analysis.ochestration.bert import SentimentModel

def main():
    """
    Main function to run both pipelines sequentially
    """
    
    
    # Initialize components for sentiment pipeline
    # Adjust these initializations based on your actual code structure
    api_data = APIData()  # or however you initialize this
    cleaner = TextCleaner()  # or however you initialize this
    sentiment_model = SentimentModel()  # or however you initialize this
    storage = SentimentStorage()
    semantic_pipeline = SemanticPipeline(storage)

    # Create and run the sentiment pipeline
    print("=" * 50)
    print("Starting Sentiment Pipeline...")
    print("=" * 50)

    pipeline = SentimentPipeline(api_data, cleaner, sentiment_model, news_scraper, web_scraper)
    pipeline_results=pipeline.run_pipeline()  # Adjust method name if different

    print("Sentiment Pipeline completed.✅✅✅")
    print("Starting Semantic Pipeline...")
    print("=" * 50)
    
    semantic_results=semantic_pipeline.run_semantic_pipeline(pipeline_results)

    print("=" * 50)
    print("\nSemantic Pipeline completed!")

    print("=" * 50)
    print("Storing results in database...")
    print("=" * 50)
  
    storage.store_sentiment_results(semantic_results)  
    print("Sentiment results stored in database.✅✅✅")
    



if __name__ == "__main__":
    results = main()
    print("\nBoth pipelines completed successfully!")