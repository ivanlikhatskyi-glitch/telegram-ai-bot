import os
import psycopg2
from flask import Flask, request
import requests
import anthropic

TELEGRAM_TOKEN = os.environ.get("BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
SYSTEM_PROMPT = os.environ.get("SYSTEM_PROMPT", "You are a friendly assistant in a Telegram channel. Do not use any Russian resources unless asked. Reply in Russian, Ukrainian or English based on the user language.")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@vetervsem_bot")
DATABASE_URL = os.environ.get("DATABASE_URL")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
app = Flask(__name__)

MAX_HISTORY = 20


def get_db():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            chat_id BIGINT NOT NULL,
            username TEXT,
            first_name TEXT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def get_history(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT role, content FROM chat_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (user_id, MAX_HISTORY))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    rows.reverse()
    return [{"role": row[0], "content": row[1]} for row in rows]


def save_message(user_id, chat_id, username, first_name, role, content):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO chat_history (user_id, chat_id, username, first_name, role, content)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, chat_id, username, first_name, role, content))
    conn.commit()
    cur.close()
    conn.close()


def send_message(chat_id, text, reply_to=None):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    requests.post(url, json=data, timeout=30)


def get_ai_answer(user_id, chat_id, username, first_name, user_text):
    save_message(user_id, chat_id, username, first_name, "user", user_text)
    history = get_history(user_id)

    name = first_name or username or "User"
    system = SYSTEM_PROMPT + " The user's name is " + name + "."

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            messages=history,
        )
        answer = response.content[0].text.strip()
        save_message(user_id, chat_id, username, first_name, "assistant", answer)
        return answer
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
    user = message.get("from", {})
    user_id = user.get("id", chat_id)
    username = user.get("username", "")
    first_name = user.get("first_name", "")

    if not text:
        return "ok"

    if chat_type == "private":
        send_message(chat_id, get_ai_answer(user_id, chat_id, username, first_name, text), message_id)
        return "ok"

    if BOT_USERNAME.lower() not in text.lower():
        return "ok"

    question = text.replace(BOT_USERNAME, "").strip()
    if not question:
        send_message(chat_id, "Write your question after the mention", message_id)
        return "ok"

    send_message(chat_id, get_ai_answer(user_id, chat_id, username, first_name, question), message_id)
    return "ok"


@app.route("/")
def home():
    return "Bot running"


init_db()
