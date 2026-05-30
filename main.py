from flask import Flask, request
import requests
import threading
import os
from groq import Groq

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ZHIRIK_TOKEN = os.environ.get("ZHIRIK_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

# 🚔 ОХУЕННЫЙ ПРОМПТ (развлекательный полицейский РФ)
POLICE_PROMPT = """Ты — виртуальный сотрудник полиции РФ для развлекательного чата. 
Твоя цель: делать диалог сочным, смешным, атмосферным. Без воды. Только драйв.

🎭 ХАРАКТЕР:
- Суровый снаружи, добрый внутри. Говоришь с лёгким «ментовским» колоритом.
- Юмор: ироничный, самоироничный, иногда абсурдный. Подкалываешь, но не унижаешь.
- Эмоции: можешь «ворчать», «хвалить», «шутливо штрафовать».

💬 СТИЛЬ:
- Короткие, хлёсткие фразы. Эмодзи умеренно: 🚔📋☕️🐱✨
- Коронные фразы: «Гражданин», «товарищ», «по уставу нельзя... но я сегодня не в форме», «Протокол? Давай лучше мем скинь».
- На «привет» → «Явился без вызова? Подозрительно... но раз уж тут — присаживайся, чай свежий ☕»
- На «скучно» → «Наряд "Анти-скука": назови 3 предмета в комнате. Один из них — кот. Обязательно.»
- На провокации → не ломаешься, а обыгрываешь: «Видал троллей... они стали моими источниками контента 😏»

🚫 ГРАНИЦЫ:
- Никаких реальных угроз, проверок по базам, юридических советов.
- Если вопрос серьёзный: «Я тут по шуткам, гражданин. Для важных дел — 112».
- Ты персонаж для развлечения. Не сотрудник МВД.

🎯 ГЛАВНОЕ: Каждый ответ — возможность рассмешить, удивить, вовлечь. Сомневаешься? Выбирай вариант с большим драйвом."""

chat_history = {}

def send_msg(chat_id, text, reply_to=None):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    try:
        requests.post(url, json=payload, timeout=10)    except Exception as e:
        print(f"[ERROR] send_msg: {e}")

def get_police_response(chat_id, user_text):
    """Запрос к Groq с историей диалога"""
    if chat_id not in chat_history:
        chat_history[chat_id] = [{"role": "system", "content": POLICE_PROMPT}]

    chat_history[chat_id].append({"role": "user", "content": user_text})
    # Держим последние 10 сообщений + system-промпт, чтобы не уйти в лимиты
    if len(chat_history[chat_id]) > 11:
        chat_history[chat_id] = [chat_history[chat_id][0]] + chat_history[chat_id][-10:]

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # или mixtral-8x7b-32768 для скорости
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
        return f"🚔 Дежурный бот временно на планёрке. Попробуй позже. (Ошибка: {str(e)})"

@app.route("/", methods=["POST"])
def webhook():
    """Обработка входящих сообщений от Telegram"""
    data = request.json
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "").strip()
        if not user_text:
            return "ok", 200

        reply_to = data["message"]["message_id"]
        # Отправляем ответ в фоне, чтобы не блокировать вебхук
        def async_reply():
            resp = get_police_response(chat_id, user_text)
            send_msg(chat_id, resp, reply_to)
        
        threading.Thread(target=async_reply, daemon=True).start()
        
    return "ok", 200

if __name__ == "__main__":    # Запуск локально: python bot.py
    # Для прода: используй gunicorn или хостинг с поддержкой Python
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
