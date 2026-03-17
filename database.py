from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]

users = db["users"]
tokens = db["tokens"]
admins = db["admins"]
chats = db["chats"]