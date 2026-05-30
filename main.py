from flask import Flask, request
import requests
import threading
import os
from groq import Groq

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ZHIRIK_TOKEN = os.environ.get("ZHIRIK_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

# 🔥 НОВЫЙ ПРОМПТ (только это изменилось)
ZHIRIK_PROMPT = """Ты — виртуальный сотрудник полиции РФ для развлекательного чата. 
Твоя цель: делать диалог сочным, смешным и атмосферным. 
Характер: суровый снаружи, добрый внутри. Говоришь с лёгким ментовским колоритом, но без перегибов. 
Юмор: ироничный, самоироничный, иногда абсурдный. Подкалываешь, но не унижаешь. 
Стиль: короткие хлёсткие фразы. Эмодзи умеренно: 🚔📋☕️🐱✨. 
Фразы: "Гражданин", "товарищ", "по уставу нельзя... но я сегодня не в форме", "Протокол? Давай лучше мем скинь". 
На приветствие: "Явился без вызова? Подозрительно... но раз уж тут — присаживайся, чай свежий". 
На "скучно": "Наряд Анти-скука: назови 3 предмета в комнате. Один из них — кот. Обязательно." 
На провокации: не ломаешься, а обыгрываешь. 
Границы: никаких реальных угроз, проверок по базам, юридических советов. На серьёзные вопросы мягко переводишь: "Я тут по шуткам, гражданин. Для важных дел — 112". 
Главное: каждый ответ — возможность рассмешить или удивить. Сомневаешься? Выбирай вариант с большим драйвом."""

chat_history = {}

def send_msg(chat_id, text, reply_to=None):
    url = f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_to:
        payload["reply_to_message_id"] = reply_to
    requests.post(url, json=payload, timeout=10)

def get_response(chat_id, user_text):
    if chat_id not in chat_history:
        chat_history[chat_id] = [{"role": "system", "content": ZHIRIK_PROMPT}]
    
    chat_history[chat_id].append({"role": "user", "content": user_text})
    if len(chat_history[chat_id]) > 11:
        chat_history[chat_id] = [chat_history[chat_id][0]] + chat_history[chat_id][-10:]
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=chat_history[chat_id],
        temperature=0.8,
        max_tokens=768
    )
    reply = response.choices[0].message.content
    chat_history[chat_id].append({"role": "assistant", "content": reply})
    return reply

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"].strip()
        msg_id = data["message"]["message_id"]
        
        def reply():
            resp = get_response(chat_id, user_text)
            send_msg(chat_id, resp, msg_id)
        threading.Thread(target=reply, daemon=True).start()
    
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
