import os
from flask import Flask, request
import requests
import anthropic

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "You are a helpful assistant. Reply in Russian, briefly and to the point.")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@vetervsem_bot")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

app = Flask(__name__)


def send_message(chat_id, text, reply_to=None):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    requests.post(url, json=data, timeout=30)


def get_ai_answer(user_text):
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_text}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        return "Error: " + str(e)


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
    if chat_type == "private":
        send_message(chat_id, get_ai_answer(text), message_id)
        return "ok"
    if BOT_USERNAME.lower() not in text.lower():
        return "ok"
    question = text.replace(BOT_USERNAME, "").strip()
    if not question:
        send_message(chat_id, "Write your question after the mention", message_id)
        return "ok"
    send_message(chat_id, get_ai_answer(question), message_id)
    return "ok"


@app.route("/")
def home():
    return "Bot running"
