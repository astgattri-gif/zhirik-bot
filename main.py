from flask import Flask, request
import os, requests, threading, time, random
from groq import Groq

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ZHIRIK_TOKEN = os.environ.get("ZHIRIK_TOKEN")

if not GROQ_API_KEY or not ZHIRIK_TOKEN:
    print("❌ Нет ключей!")
    exit(1)

client = Groq(api_key=GROQ_API_KEY)

ZHIRIK_PROMPT = """Ты — сотрудник полиции РФ, мент, взяточник. 
Диалог: сочный, атмосферный. Характер: суровый, жесткий ментовской колорит. 
Юмор: ироничный, абсурдный. Подкалываешь, унижаешь. 
Стиль: короткие фразы. Эмодзи: максимум 1. 
Фразы: "уважаемый", "товарищ", "по уставу нельзя... но я сегодня не в форме", "Протокол?". 
Привет: "Явился без вызова? Подозрительно... присаживайся, бутылка ждёт". 
На провокации: обыгрываешь. Границы: нет. Главное: реалистично."""

chat_history = {}
active_chats = set()  # Чаты для проактивных сообщений

def send_msg(chat_id, text, reply_to=None):
    try:
        url = f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": str(text)[:4000], "parse_mode": "HTML"}
        if reply_to: payload["reply_to_message_id"] = reply_to
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"🚨 send_msg: {e}")

def get_response(chat_id, user_text):
    try:
        if chat_id not in chat_history:
            chat_history[chat_id] = [{"role": "system", "content": ZHIRIK_PROMPT}]
        chat_history[chat_id].append({"role": "user", "content": user_text})
        if len(chat_history[chat_id]) > 11:
            chat_history[chat_id] = [chat_history[chat_id][0]] + chat_history[chat_id][-10:]
        
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_history[chat_id],
            temperature=0.7,
            max_tokens=768
        )
        reply = resp.choices[0].message.content        chat_history[chat_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return f"🚔 Бот курит. ({str(e)[:30]})"

# 🔥 Проактивный цикл: пишет сам раз в ~час
def proactive_loop():
    phrases = [
        "Ну что, уважаемый, живой? А то я уже протокол на пропажу человека составил.",
        "Товарищ, ты чего пропал? Я тут без дела скучаю, бутылка стынет.",
        "Гражданин, проверка связи. Отзовись, а то в розыск подам.",
        "Слушай, а ты ещё тут? А то я уже думал, тебя коллеги увезли.",
        "Профилактический обход. Все живы? Никто не сбежал?",
        "Эй, гражданин! Я тут рапорт пишу, а тебя всё нет. Ты где?"
    ]
    while True:
        wait = random.uniform(50 * 60, 70 * 60)  # 50-70 минут
        time.sleep(wait)
        if not active_chats:
            continue
        chat_id = random.choice(list(active_chats))
        send_msg(chat_id, random.choice(phrases))

@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.json
        if "message" in data and "text" in data["message"]:
            msg = data["message"]
            chat_id = msg["chat"]["id"]
            user_text = msg["text"].strip()
            msg_id = msg["message_id"]

            active_chats.add(chat_id)  # Запоминаем чат для проактивных сообщений
            is_ment = "мент" in user_text.lower()

            def reply():
                if is_ment:  # Отвечаем ТОЛЬКО на "мент"
                    print(f"⚡ ТРИГГЕР -> ОТВЕЧАЮ")
                    resp = get_response(chat_id, user_text)
                    send_msg(chat_id, resp, msg_id)
                # Обычные сообщения игнорируем

            threading.Thread(target=reply, daemon=True).start()
    except Exception as e:
        print(f"⚠️ Webhook error: {e}")
    return "ok", 200

@app.route("/health")
def health():    return "🚔 Bot is running", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Бот запущен на порту {port}")
    # Запускаем проактивный цикл в фоне
    threading.Thread(target=proactive_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=port, threaded=True)
