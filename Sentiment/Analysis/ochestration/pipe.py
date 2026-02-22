from Sentiment.Analysis.data_collector.news_api import APIData
from Sentiment.Analysis.ochestration.cleaner import TextCleaner
from Sentiment.Analysis.ochestration.bert import SentimentModel
from Sentiment.Analysis.storage.store import SentimentStorage
from datetime import datetime


#-------Instances
api_data = APIData() #return multiple dictionaries (list of dictionaries)
cleaner = TextCleaner() #cleaning one dict at a time. Run with a for loop. already in the cleaner.py
sentiment_model = SentimentModel() #can handle both single and multiple texts
storage = SentimentStorage()

class SentimentPipeline:
    def __init__(self, api_data, cleaner,model, news , web):
        self.api_data = api_data
        self.cleaner = cleaner
        self.model = model
        self.news_scraper = news
        self.web_scraper = web

    def run_pipeline(self):
        
        # get data from API. Curently only inpmlemnt for the google News Search API(not news scraper)
        raw_articles = self.api_data.get_everything(query="stock market headlines", language='en', sort_by='relevancy', page=1)
        news_results = self.news_scraper()
        web_results = self.web_scraper()

        # ============ For articles from the news API ============

        list_of_cleaned_texts = []
        results = []
        for article in raw_articles:
            cleaned_text = self.cleaner.clean_text(article)
            list_of_cleaned_texts.append(cleaned_text)
            
            predictions = self.model.predict(cleaned_text)

            results.append({
                'content': article.get('content'),
                'cleaned_text': cleaned_text,
                'predictions': predictions,
                'timestamp': datetime.utcnow(),
                'type': 'api_article'
            })
        

        # ============ For data from the news scraper ============

        headings = news_results.get('headings')
        content = news_results.get('content')
        paragraphs = news_results.get('paragraphs')

        news_data = headings + content + paragraphs

        for text in news_data:
            cleaned_text = self.cleaner.clean_text_from_scraper(text)
            predictions = self.model.predict(cleaned_text)

            results.append({
                'content': text,
                'cleaned_text': cleaned_text,
                'predictions': predictions,
                'timestamp': datetime.utcnow(),
                'type': 'news_scraper'
            })

        
        # ============ For data from the web scraper ============

        headings = web_results.get('headings')
        content = web_results.get('content')
        paragraphs = web_results.get('paragraphs')
        

        web_data = headings + content + paragraphs

        for text in web_data:
            cleaned_text = self.cleaner.clean_text_from_scraper(text)
            predictions = self.model.predict(cleaned_text)

            results.append({
                'content': text,
                'cleaned_text': cleaned_text,
                'predictions': predictions,
                'timestamp': datetime.utcnow(),
                'type': 'web_scraper'
            })
           

        print(f"Pipeline Results: {len(results)}\n")
        return results
'''
pipeline = SentimentPipeline(api_data, cleaner, sentiment_model, news_scraper, web_scraper)
pipeline_results = pipeline.run_pipeline()
print("Sentiment Pipeline Completed.✅✅✅")
storage.store_sentiment_results(pipeline_results)
'''
