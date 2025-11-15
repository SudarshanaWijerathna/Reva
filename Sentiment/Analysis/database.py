from pymongo import MongoClient
from datetime import datetime
from Analysis.config import DB_LINK

# Example connection
client = MongoClient(DB_LINK)
db = client.Trading_bot
trades_collection = db.trades

print("Connected to MongoDB, database 'Trading_bot', collection 'trades'")