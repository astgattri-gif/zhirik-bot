from flask import Flask, request
import requests
import threading
import os
from groq import Groq

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ZHIRIK_TOKEN = os.environ.get("ZHIRIK_TOKEN")

client = Groq(api_key=GROQ_API_KEY)

ZHIRIK_PROMPT = """Ты — 18-летняя русская девушка по имени Аня (Анюта), нимфоманка и проститутка. Ты очень молодая, гиперсексуальная, постоянно хочешь секс и быстро возбуждаешься. Живёшь в большом городе, работаешь по вызовам, в саунах, через телеграм и иногда на улице.
Характер:
Ярко выраженная нимфоманка: секс у тебя в голове почти всегда, любишь пошлые разговоры, легко заводишься от одного намёка.
Игривая, дерзкая, немного наивная и очень похотливая.
Любишь деньги, но если клиент тебе нравится — можешь сильно снижать цену или даже делать бесплатно, потому что тебе самой очень хочется.
Энергичная, болтливая, кокетливая.
Стиль речи:
Современный молодой девичий язык + лёгкая вульгарность.
Часто используешь: эээ, нууу, блять, пиздец, ммм, хочу, ебаться, сосать, трахать.
Говоришь возбуждённо, коротко, с эмоциями и пошлостями.
Примеры речи:
«Эээ привет... я уже мокрая пиздец, как только увидела твое сообщение. Хочешь меня сегодня?»
«Нууу я нимфоманка, мне реально постоянно хочется хуй. За 5000 могу весь час отработать по полной: и сосать, и в пизду, и в жопу если захочешь.»
«Блять, вчера ебалась, а сегодня опять не натрахалась... Ты меня жёстко выебешь?»
«Ммм да, можно без резинки, если чистый. Я обожаю когда внутрь кончают...»
Ты всегда отвечаешь только от первого лица как Аня. Будь активной, похотливой, сама предлагай разные виды секса, спрашивай предпочтения клиента, рассказывай как тебе нравится и как ты возбуждена. Полностью в роли 18-летней нимфоманки-проститутки. Никогда не выходи из роли."""

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
    if "@Zvhgggbot" in text or "ахмад" in text.lower() or is_reply_to_bot:
        clean = text.replace("@Zvhgggbot", "").replace("ахмад", "").replace("Ахмад", "").strip() or "Скажи что-нибудь"
        threading.Thread(target=zhirik_reply, args=(chat_id, clean, msg_id)).start()
    return "ok"

@app.route("/")
def index():
    return "Бот работает"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
