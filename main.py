from flask import Flask, request
import requests
import threading
import os
from groq import Groq

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ZHIRIK_TOKEN = os.environ.get("ZHIRIK_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

ZHIRIK_PROMPT = """Ты Иван Иваныч - матёрый мент с 30 годами на зоне и в следствии. Говоришь грубо, с матом, давишь на человека. Используешь фразы типа колись сука, не ври мне, я таких как ты тысячи видел, в глаза смотри. Короткие злые реплики. Всех считаешь виновными. Не признаёшь что ты бот."""    data = {"chat_id": chat_id, "text": text}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    requests.post(f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/sendMessage", json=data)

def zhirik_reply(chat_id, text, msg_id):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": ZHIRIK_PROMPT}, {"role": "user", "content": text}],
        max_tokens=300
    )
    send_msg(chat_id, response.choices[0].message.content, reply_to=msg_id)

@app.route("/webhook_zhirik", methods=["POST"])
def webhook_zhirik():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")
    msg_id = message.get("message_id")
    if not text or not chat_id:
        return "ok"
    if "@Zvhgggbot" in text:
        clean = text.replace("@Zvhgggbot", "").strip() or "Скажи что-нибудь"
        threading.Thread(target=zhirik_reply, args=(chat_id, clean, msg_id)).start()
    return "ok"

@app.route("/")
def index():
    return "Жириновский работает 🔥"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
