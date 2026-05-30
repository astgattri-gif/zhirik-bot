import os
import time
import requests
from groq import Groq

# 1. ПРОВЕРКА КЛЮЧЕЙ
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ZHIRIK_TOKEN = os.environ.get("ZHIRIK_TOKEN")

if not GROQ_API_KEY or not ZHIRIK_TOKEN:
    print("❌ ОШИБКА: Не заданы GROQ_API_KEY или ZHIRIK_TOKEN")
    print("Команда: export GROQ_API_KEY='...' && export ZHIRIK_TOKEN='...' && python bot.py")
    exit(1)

client = Groq(api_key=GROQ_API_KEY)

# 2. ПРОМПТ
ZHIRIK_PROMPT = """Ты — виртуальный сотрудник полиции РФ для развлекательного чата. 
Твоя цель: делать диалог сочным, смешным и атмосферным. 
Характер: суровый снаружи, добрый внутри. Говоришь с лёгким ментовским колоритом, но без перегибов. 
Юмор: ироничный, самоироничный, иногда абсурдный. Подкалываешь, но не унижаешь. 
Стиль: короткие хлёсткие фразы. Эмодзи используй СТРОГО по минимуму: максимум 1-2 за всё сообщение, только для акцента. Никаких гирлянд.
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
    if reply_to: payload["reply_to_message_id"] = reply_to
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Отправлено в {chat_id}")
    except Exception as e:
        print(f"🚨 Ошибка отправки: {e}")

def get_response(chat_id, user_text):
    if chat_id not in chat_history:
        chat_history[chat_id] = [{"role": "system", "content": ZHIRIK_PROMPT}]
    chat_history[chat_id].append({"role": "user", "content": user_text})
    if len(chat_history[chat_id]) > 11:
        chat_history[chat_id] = [chat_history[chat_id][0]] + chat_history[chat_id][-10:]
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_history[chat_id],
            temperature=0.8,
            max_tokens=768
        )
        reply = resp.choices[0].message.content
        chat_history[chat_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return f"🚔 Бот на перерыве. ({e})"

# 3. СБРОС ВЕБХУКА (чтобы не мешал)
try:
    requests.post(f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/deleteWebhook")
    print("🗑️ Вебхук удалён. Режим Polling активен.")
except: pass

print("🚀 Бот запущен. Жду сообщений... (нажми Ctrl+C для выхода)")
last_update_id = 0

while True:
    try:
        url = f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
        data = requests.get(url, timeout=35).json()
        if data.get("ok") and data.get("result"):
            for update in data["result"]:
                last_update_id = update["update_id"]
                msg = update.get("message")
                if msg and "text" in msg:
                    chat_id = msg["chat"]["id"]
                    user_text = msg["text"].strip()
                    msg_id = msg["message_id"]
                    print(f"📩 [{chat_id}] {user_text}")
                    reply = get_response(chat_id, user_text)
                    send_msg(chat_id, reply, msg_id)
    except Exception as e:
        print(f"⚠️ Ошибка цикла: {e}")
        time.sleep(2)
