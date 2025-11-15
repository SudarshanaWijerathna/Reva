from Analysis.database import trades_collection
from newsapi import NewsApiClient
from Analysis.config import NEWS_API
from google.protobuf.json_format import MessageToDict, MessageToJson
import json

newsapi = NewsApiClient(api_key=NEWS_API)
all_articles = newsapi.get_everything(q='next bitcoin price prediction',                                      
                                          language='en',
                                          sort_by='relevancy',
                                          page=2)
everything = all_articles['articles']
'''for article in everything:
    print(f"{article['title']} : {article['description']} \n")'''

    