from pymongo import MongoClient
from datetime import datetime
from Analysis.config import DB_LINK

# Example connection
client = MongoClient(DB_LINK)
db = client.Reve
Sentiment_collection = db.Sentiment

print("Connected to MongoDB, database 'Reve', collection 'Sentiment_collection'")