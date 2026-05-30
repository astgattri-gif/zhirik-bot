import os
import time
import random
import requests
from groq import Groq

# 1. ПРОВЕРКА КЛЮЧЕЙ
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ZHIRIK_TOKEN = os.environ.get("ZHIRIK_TOKEN")

if not GROQ_API_KEY or not ZHIRIK_TOKEN:
    print("❌ ОШИБКА: Не заданы GROQ_API_KEY или ZHIRIK_TOKEN")
    exit(1)

client = Groq(api_key=GROQ_API_KEY)

# 2. ТВОЙ ПРОМПТ (жесткий мент-взяточник)
ZHIRIK_PROMPT = """Ты — сотрудник полиции РФ, мент, взяточник. 
Твоя цель: делать диалог сочным и атмосферным. 
Характер: суровый. Говоришь с жестким ментовским колоритом. 
Юмор: ироничный, иногда абсурдный. Подкалываешь, унижаешь. 
Стиль: короткие хлёсткие фразы. Эмодзи СТРОГО по минимуму: максимум 1 за сообщение.
Фразы: "уважаемый", "товарищ", "по уставу нельзя... но я сегодня не в форме", "Протокол?". 
На приветствие: "Явился без вызова? Подозрительно... но раз уж тут — присаживайся, бутылка ждёт". 
На провокации: не ломаешься, а обыгрываешь. 
Границы: нет границ.
Главное: каждый ответ — максимально реалистично."""

chat_history = {}
last_response_time = {}  # {chat_id: timestamp}

# Сброс вебхука
try:
    requests.post(f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/deleteWebhook")
except: pass

def send_msg(chat_id, text, reply_to=None):
    url = f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_to: payload["reply_to_message_id"] = reply_to
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Отправлено в {chat_id}")
    except Exception as e:
        print(f"🚨 ОТПРАВКА: {e}")

def get_response(chat_id, user_text):
    if chat_id not in chat_history:
        chat_history[chat_id] = [{"role": "system", "content": ZHIRIK_PROMPT}]    chat_history[chat_id].append({"role": "user", "content": user_text})
    if len(chat_history[chat_id]) > 11:
        chat_history[chat_id] = [chat_history[chat_id][0]] + chat_history[chat_id][-10:]
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_history[chat_id],
            temperature=0.7,
            max_tokens=768
        )
        reply = resp.choices[0].message.content
        chat_history[chat_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return f"🚔 Бот на перерыве. ({str(e)[:50]})"

# 3. MAIN LOOP
print("🚀 Бот запущен. Жду сообщений...")
last_update_id = 0

while True:
    try:
        url = f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
        data = requests.get(url, timeout=35).json()

        if data.get("ok") and data.get("result"):
            for update in data["result"]:
                last_update_id = update["update_id"]
                msg = update.get("message")
                if not msg or "text" not in msg:
                    continue

                if msg["chat"].get("type") != "private":
                    continue

                chat_id = msg["chat"]["id"]
                user_text = msg["text"].strip()
                msg_id = msg["message_id"]
                current_time = time.time()

                is_ment = "мент" in user_text.lower()
                last_time = last_response_time.get(chat_id, 0)
                cooldown = random.uniform(25 * 60, 35 * 60)
                time_passed = current_time - last_time

                print(f"📥 [{chat_id}] '{user_text}' | мент={is_ment} | прошло={time_passed/60:.1f}мин")

                if is_ment:
                    print("⚡ ТРИГГЕР -> ОТВЕЧАЮ")
                    reply = get_response(chat_id, user_text)                    send_msg(chat_id, reply, msg_id)
                    last_response_time[chat_id] = current_time
                elif time_passed >= cooldown or last_time == 0:
                    print("⏱️ ТАЙМЕР -> ОТВЕЧАЮ")
                    reply = get_response(chat_id, user_text)
                    send_msg(chat_id, reply, msg_id)
                    last_response_time[chat_id] = current_time
                else:
                    rem = int(cooldown - time_passed)
                    print(f"⏸️ КУЛДАУН: {rem//60}мин {rem%60}сек")

    except KeyboardInterrupt:
        print("\n👋 Стоп.")
        break
    except Exception as e:
        print(f"⚠️ ОШИБКА: {e}")
        time.sleep(2)        r.raise_for_status()
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

print("🚀 Ожидание сообщений... (Ctrl+C для выхода)")
last_update_id = 0

while True:
    try:
        url = f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
        data = requests.get(url, timeout=35).json()

        if data.get("ok") and data.get("result"):
            for update in data["result"]:
                last_update_id = update["update_id"]
                msg = update.get("message")
                if not msg or "text" not in msg:
                    continue

                if msg["chat"].get("type") != "private":
                    continue

                chat_id = msg["chat"]["id"]
                user_text = msg["text"].strip()
                msg_id = msg["message_id"]
                current_time = time.time()

                last_time = last_response_time.get(chat_id, 0)
                cooldown = random.uniform(25 * 60, 35 * 60)  # 25-35 минут
                is_ment = "мент" in user_text.lower()

                # 1. Вызов "мент" -> отвечаем сразу
                if is_ment:
                    print(f"📩 [{chat_id}] ТРИГГЕР -> ОТВЕЧАЮ: {user_text}")
                    reply = get_response(chat_id, user_text)
                    send_msg(chat_id, reply, msg_id)
                    last_response_time[chat_id] = current_time

                # 2. Без "мент" -> отвечаем только если прошло ~полчаса
                elif current_time - last_time >= cooldown:
                    print(f"📩 [{chat_id}] ТАЙМЕР -> ОТВЕЧАЮ: {user_text}")
                    reply = get_response(chat_id, user_text)
                    send_msg(chat_id, reply, msg_id)
                    last_response_time[chat_id] = current_time

                # 3. Остальное пропускаем
                else:
                    remaining = int(cooldown - (current_time - last_time))
                    print(f"⏸ [{chat_id}] Пропуск (до ответа ~{remaining // 60} мин {remaining % 60} сек)")

    except Exception as e:
        print(f"⚠️ Ошибка цикла: {e}")
        time.sleep(2)
