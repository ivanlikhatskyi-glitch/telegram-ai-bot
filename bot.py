import os
from flask import Flask, request
import requests
import anthropic

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

app = Flask(__name__)


def send_message(chat_id, text, reply_to=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_to:
        data["reply_to_message_id"] = reply_to

    requests.post(url, json=data, timeout=30)


def get_ai_answer(user_text):
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=(
                "Ты полезный ассистент Telegram-канала. "
                "Отвечай по-русски, живо, корот​​​​​​​​​​​​​​​​
