import os
from flask import Flask, request
import requests

TOKEN = os.environ.get("BOT_TOKEN")

app = Flask(__name__)


def send_message(chat_id, text, reply_to=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_to:
        data["reply_to_message_id"] = reply_to

    requests.post(url, json=data)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if "message" not in data:
        return "ok"

    message = data["message"]
    text = message.get("text", "")
    chat_id = message["chat"]["id"]
    message_id = message["message_id"]
    chat_type = message["chat"].get("type", "")

    if not text:
        return "ok"

    # Личный чат: отвечаем на любое сообщение
    if chat_type == "private":
        answer = f"Ты написал: {text}"
        send_message(chat_id, answer, message_id)
        return "ok"

    # Группа/супергруппа: отвечаем только по упоминанию
    if "@vetervsem_bot" not in text.lower():
        return "ok"

    question = text.replace("@vetervsem_bot", "").strip()

    if not question:
        send_message(chat_id, "Напиши вопрос после упоминания 🙂", message_id)
        return "ok"

    answer = f"Ты написал: {question}"
    send_message(chat_id, answer, message_id)

    return "ok"


@app.route("/")
def home():
    return "Bot running"