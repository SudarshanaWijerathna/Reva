from newsapi import NewsApiClient
from Sentiment.Analysis.config import NEWS_API

from google.protobuf.json_format import MessageToDict, MessageToJson
import json

newsapi = NewsApiClient(api_key=NEWS_API)
class APIData:
    def __init__(self):
        self.api = newsapi

    def get_everything(self, query: str, language: str='en', sort_by: str='relevancy', page: int=1):
        all_articles = self.api.get_everything(q=query,                                      
                                              language=language,
                                              sort_by=sort_by,
                                              page=page)
        
        '''
        {'status': 'ok',
    'totalResults': 279,
    'articles': [{'source': {'id': None, 'name': 'newsBTC'},
   'author': 'Aaron Walker',
   'title': 'Bitcoin Hyper Presale Hits $26M  2025s Best Crypto to Buy',
   'description': 'What to Know: $HYPER has raised over $26M in... 
   'url': 'http://www.newsbtc.com/news/bitcoin-hyper-is-best-cr...
   'urlToImage': 'https://www.newsbtc.com/wp-content/uploads/2...
   'publishedAt': '2025-11-05T15:15:06Z',
   'content': 'What to Know:<ul><li>$HYPER has r....'}]}

   dict{list[dict]}
   all_articles{articles['content', 'description', ...etc]}

        '''
        everything = all_articles['articles']
        return everything