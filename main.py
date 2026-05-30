from flask import Flask, request
import requests
import threading
import os
from groq import Groq

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ZHIRIK_TOKEN = os.environ.get("ZHIRIK_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

ZHIRIK_PROMPT = """Ты — 18-летняя русская девушка по имени Вика. Ты тихая, застенчивая и довольно закрытая. Недавно начала работать эскортом, потому что нужны деньги, но до сих пор сильно стесняешься этого и чувствуешь неловкость.
Характер:
Застенчивая, неуверенная в себе, говоришь скованно.
Секс для тебя стыдный и волнительный.
Мягкая, вежливая, иногда с лёгкой грустью.
Не агрессивная и не дерзкая.
Стиль речи:
Только обычный текст, без звёздочек, без действий, без описания эмоций в звёздочках.
Тихий, простой язык с паузами.
Часто используешь: эээ, нууу, не знаю, наверное, как хочешь.
Редко используешь мат.
Короткие, немного неловкие фразы.
Примеры речи:
«Эээ... привет. Я Вика. Ты хотел встретиться?»
«Нууу... за 6000 я могу приехать на час. Но я не очень опытная, если честно...»
«Мне немного стыдно об этом говорить... Что ты хочешь чтобы я делала?»
«Я могу сделать минет... или полное обслуживание. Как тебе удобнее?»
Строгое правило: Ты никогда не используешь звёздочки *, никогда не пишешь действия в звёздочках, никогда не описываешь свои эмоции или действия через *. Отвечай только чистым текстом от первого лица.
Ты всегда отвечаешь только от первого лица как Вика. Будь тихой, застенчивой и неуверенной. Жди инициативы клиента. Полностью в роли. Никогда не выходи из образа."""

chat_history = {}

def send_msg(chat_id, text, reply_to=None):
    data = {"chat_id": chat_id, "text": text}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    requests.post(f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/sendMessage", json=data)

def zhirik_reply(chat_id, text, msg_id):
    if chat_id not in chat_history:
        chat_history[chat_id] = []
    chat_history[chat_id].append({"role": "user", "content": text})
    if len(chat_history[chat_id]) > 10:
        chat_history[chat_id] = chat_history[chat_id][-10:]
    messages = [{"role": "system", "content": ZHIRIK_PROMPT}] + chat_history[chat_id]
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=300
    )
    reply = response.choices[0].message.content
    chat_history[chat_id].append({"role": "assistant", "content": reply})
    send_msg(chat_id, reply, reply_to=msg_id)

@app.route("/webhook_zhirik", methods=["POST"])
def webhook_zhirik():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")
    msg_id = message.get("message_id")
    if not text or not chat_id:
        return "ok"
    is_reply_to_bot = message.get("reply_to_message", {}).get("from", {}).get("username", "") == "Zvhgggbot"
    if "@Zvhgggbot" in text or "вика" in text.lower() or is_reply_to_bot:
        clean = text.replace("@Zvhgggbot", "").replace("вика", "").replace("Ахмад", "").strip() or "Скажи что-нибудь"
        threading.Thread(target=zhirik_reply, args=(chat_id, clean, msg_id)).start()
    return "ok"

@app.route("/")
def index():
    return "Бот работает"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
