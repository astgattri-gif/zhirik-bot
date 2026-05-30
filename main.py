from flask import Flask, request
import requests
import threading
import os
import sys
from groq import Groq

app = Flask(__name__)

# 1. ПРОВЕРКА ТОКЕНОВ ПРИ ЗАПУСКЕ
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ZHIRIK_TOKEN = os.environ.get("ZHIRIK_TOKEN")

if not GROQ_API_KEY or not ZHIRIK_TOKEN:
    print("❌ ОШИБКА: Не заданы GROQ_API_KEY или ZHIRIK_TOKEN в переменных окружения!")
    sys.exit(1)

client = Groq(api_key=GROQ_API_KEY)

POLICE_PROMPT = """Ты — виртуальный сотрудник полиции РФ для развлекательного чата. 
Твоя цель: делать диалог сочным, смешным, атмосферным. Без воды. Только драйв.
🎭 ХАРАКТЕР: Суровый снаружи, добрый внутри. Лёгкий «ментовский» колорит.
💬 СТИЛЬ: Короткие, хлёсткие фразы. Эмодзи умеренно: 🚔📋☕️🐱✨
🚫 ГРАНИЦЫ: Никаких реальных угроз, проверок, юр. советов. На серьёзные вопросы: «Я тут по шуткам. Для важных дел — 112».
🎯 ГЛАВНОЕ: Каждый ответ — возможность рассмешить или удивить."""

chat_history = {}

def send_msg(chat_id, text, reply_to=None):
    url = f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"✅ Отправлено в {chat_id}")
    except Exception as e:
        print(f"🚨 ОШИБКА ОТПРАВКИ: {e}")

def get_police_response(chat_id, user_text):
    if chat_id not in chat_history:
        chat_history[chat_id] = [{"role": "system", "content": POLICE_PROMPT}]

    chat_history[chat_id].append({"role": "user", "content": user_text})
    if len(chat_history[chat_id]) > 11:
        chat_history[chat_id] = [chat_history[chat_id][0]] + chat_history[chat_id][-10:]

    try:
        print(f"📡 Запрос к Groq от {chat_id}...")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_history[chat_id],
            temperature=0.8,
            top_p=0.95,
            presence_penalty=0.4,
            frequency_penalty=0.3,
            max_tokens=768
        )
        reply = response.choices[0].message.content
        chat_history[chat_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        err_msg = f"Groq ошибка: {str(e)}"
        print(f"🚨 {err_msg}")
        return f"🚔 Дежурный бот на перерыве. Попробуй через минуту. (Тех. инфо: {err_msg})"

@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.json
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            user_text = data["message"]["text"].strip()
            reply_to = data["message"]["message_id"]
            
            print(f"📩 Новое сообщение от {chat_id}: {user_text[:50]}...")
            
            def async_reply():
                resp = get_police_response(chat_id, user_text)
                send_msg(chat_id, resp, reply_to)
            
            threading.Thread(target=async_reply, daemon=True).start()
    except Exception as e:
        print(f"🚨 ОШИБКА ВЕБХУКА: {e}")
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Бот запущен на порту {port}. Жду сообщений...")
    app.run(host="0.0.0.0", port=port, debug=False)
