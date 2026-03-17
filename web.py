from flask import Flask, request, jsonify
from payments import handle_payment
from database import users, payments

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data["event"] == "payment_link.paid":
        handle_payment(data)

    return "OK"


@app.route("/dashboard")
def dashboard():
    total_users = users.count_documents({})
    premium = users.count_documents({"premium": True})

    total = sum(p["amount"] for p in payments.find()) / 100

    return jsonify({
        "users": total_users,
        "premium": premium,
        "earnings": total
    })
