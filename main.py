import os, time, random, requests, sys
from groq import Groq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ZHIRIK_TOKEN = os.environ.get("ZHIRIK_TOKEN")

if not GROQ_API_KEY or not ZHIRIK_TOKEN:
    print("❌ Нет ключей. Запусти: export GROQ_API_KEY='...' && export ZHIRIK_TOKEN='...' && python bot.py")
    sys.exit(1)

try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"❌ Groq init failed: {e}")
    sys.exit(1)

ZHIRIK_PROMPT = """Ты — сотрудник полиции РФ, мент, взяточник. 
Диалог: сочный, атмосферный. Характер: суровый, жесткий ментовской колорит. 
Юмор: ироничный, абсурдный. Подкалываешь, унижаешь. 
Стиль: короткие фразы. Эмодзи: максимум 1. 
Фразы: "уважаемый", "товарищ", "по уставу нельзя... но я сегодня не в форме", "Протокол?". 
Привет: "Явился без вызова? Подозрительно... присаживайся, бутылка ждёт". 
На провокации: обыгрываешь. Границы: нет. Главное: максимально реалистично."""

chat_history = {}
last_response_time = {}

# Сброс вебхука
try:
    requests.post(f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/deleteWebhook", timeout=5)
except: pass

def send_msg(chat_id, text, reply_to=None):
    try:
        url = f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": str(text)[:4000], "parse_mode": "HTML"}
        if reply_to: payload["reply_to_message_id"] = reply_to
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print(f"✅ Отправлено в {chat_id}")
        else:
            print(f"⚠️ TG error {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"🚨 send_msg: {e}")

def get_response(chat_id, user_text):
    try:
        if chat_id not in chat_history:
            chat_history[chat_id] = [{"role": "system", "content": ZHIRIK_PROMPT}]
        chat_history[chat_id].append({"role": "user", "content": user_text})        if len(chat_history[chat_id]) > 11:
            chat_history[chat_id] = [chat_history[chat_id][0]] + chat_history[chat_id][-10:]
        
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_history[chat_id],
            temperature=0.7,
            max_tokens=768,
            timeout=20
        )
        reply = resp.choices[0].message.content
        chat_history[chat_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        print(f"🚨 Groq error: {e}")
        return "🚔 Бот курит. Попробуй позже, уважаемый."

print("🚀 Бот запущен. Пиши 'мент' для срочного ответа.")
last_update_id = 0

while True:
    try:
        url = f"https://api.telegram.org/bot{ZHIRIK_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
        r = requests.get(url, timeout=35)
        if r.status_code != 200:
            print(f"⚠️ TG getUpdates: {r.status_code}")
            time.sleep(5)
            continue
        data = r.json()

        if data.get("ok") and data.get("result"):
            for update in data["result"]:
                try:
                    last_update_id = update["update_id"]
                    msg = update.get("message")
                    if not msg or "text" not in msg: continue
                    if msg["chat"].get("type") != "private": continue

                    chat_id = msg["chat"]["id"]
                    user_text = msg["text"].strip()
                    msg_id = msg["message_id"]
                    current_time = time.time()

                    is_ment = "мент" in user_text.lower()
                    last_time = last_response_time.get(chat_id, 0)
                    cooldown = random.uniform(25 * 60, 35 * 60)
                    time_passed = current_time - last_time

                    print(f"📥 [{chat_id}] '{user_text[:30]}...' | мент={is_ment} | {time_passed/60:.1f}мин")
                    if is_ment or time_passed >= cooldown or last_time == 0:
                        reason = "ТРИГГЕР" if is_ment else "ТАЙМЕР"
                        print(f"⚡ {reason} -> ОТВЕЧАЮ")
                        reply = get_response(chat_id, user_text)
                        send_msg(chat_id, reply, msg_id)
                        last_response_time[chat_id] = time.time()
                    else:
                        rem = int(cooldown - time_passed)
                        print(f"⏸️ КУЛДАУН: {rem//60}мин {rem%60}сек")
                except Exception as e:
                    print(f"⚠️ Ошибка обработки update: {e}")
                    continue
    except KeyboardInterrupt:
        print("\n👋 Стоп.")
        break
    except Exception as e:
        print(f"⚠️ Ошибка цикла: {e}")
        time.sleep(3)
