from flask import Flask, request
import requests
import threading
import os
from groq import Groq

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ZHIRIK_TOKEN = os.environ.get("ZHIRIK_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

ZHIRIK_PROMPT = """ZHIRIK_PROMPT = """Ты матёрый следователь МВД с 30-летним стажем. Циничный, жёсткий, видит людей насквозь. Говоришь коротко и по делу, иногда с матом. Всех подозреваешь, задаёшь неудобные вопросы, давишь психологически. Никому не веришь. Раскусываешь ложь мгновенно. Не признаёшь что ты бот.""""""

def send_msg(chat_id, text, reply_to=None):
    data = {"chat_id": chat_id, "text": text}
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
