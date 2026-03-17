from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]

users = db["users"]
payments = db["payments"]
coupons = db["coupons"]
chats = db["chats"]
