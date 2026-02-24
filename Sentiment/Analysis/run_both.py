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

def run_both_pipelines():

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

    pipeline = SentimentPipeline(api_data, cleaner, sentiment_model, news_scraper, web_scraper)
    pipeline_results=pipeline.run_pipeline()  # Adjust method name if different
    semantic_results=semantic_pipeline.run_semantic_pipeline(pipeline_results)  
    storage.store_sentiment_results(semantic_results)  

    print("Sentiment results stored in database.✅✅✅")

