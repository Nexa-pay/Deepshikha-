import razorpay
from config import RAZORPAY_KEY, RAZORPAY_SECRET
from database import users, payments

client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))


def create_payment(user_id):
    payment = client.payment_link.create({
        "amount": 9900,
        "currency": "INR",
        "description": "Premium AI",
        "notes": {"user_id": str(user_id)}
    })

    return payment["short_url"]


def handle_payment(data):
    entity = data["payload"]["payment_link"]["entity"]

    user_id = int(entity["notes"]["user_id"])

    users.update_one(
        {"user_id": user_id},
        {"$set": {"premium": True}},
        upsert=True
    )

    payments.insert_one({
        "user_id": user_id,
        "amount": entity["amount"]
    })
