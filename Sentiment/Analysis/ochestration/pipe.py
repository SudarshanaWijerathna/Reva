from Analysis.data_collector.news_api import APIData
from Analysis.preprocessing.cleaner import TextCleaner
from Analysis.sentiment_model.bert import SentimentModel
from Analysis.storage.store import SentimentStorage
from datetime import datetime


#-------Instances
api_data = APIData() #return multiple dictionaries (list of dictionaries)
cleaner = TextCleaner() #cleaning one dict at a time. Run with a for loop. already in the cleaner.py
sentiment_model = SentimentModel() #can handle both single and multiple texts
storage = SentimentStorage()

class SentimentPipeline:
    def __init__(self, api_data, cleaner,model):
        self.api_data = api_data
        self.cleaner = cleaner
        self.model = model

    def run_pipeline(self):
        
        # get data from API
        raw_articles = self.api_data.get_everything(query="stock market headlines", language='en', sort_by='relevancy', page=1)

        list_of_cleaned_texts = []
        results = []
        for article in raw_articles:
            cleaned_text = self.cleaner.clean_text(article)
            list_of_cleaned_texts.append(cleaned_text)
            
            predictions = self.model.predict(cleaned_text)

            results.append({
                'raw_article': article,
                'title': article.get('title'),
                'description': article.get('description'),
                'content': article.get('content'),
                'cleaned_text': cleaned_text,
                'predictions': predictions,
                'timestamp': datetime.utcnow()
            })
        print(f"Pipeline Results: {results[0]}\n")
        return results

pipeline = SentimentPipeline(api_data, cleaner, sentiment_model)
pipeline_results = pipeline.run_pipeline()
storage.store_sentiment_results(pipeline_results)

