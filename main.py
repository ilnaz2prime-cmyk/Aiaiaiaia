import telebot
import os
import json
import urllib.request
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

TOKEN = os.environ.get('BOT_TOKEN')
FAL_KEY = os.environ.get('FAL_KEY')

if not TOKEN or not FAL_KEY:
    raise RuntimeError("Задай переменные окружения BOT_TOKEN и FAL_KEY")

bot = telebot.TeleBot(TOKEN)

# Сервер для поддержания активности 24/7 (Render/Railway и т.п.)
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is online 24/7!")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "👋 **Omni Flash 1.1 Video Bot**\n\n"
        "Отправь команду:\n"
        "`/video <описание сцены на английском>`\n\n"
        "Пример:\n"
        "`/video sports car drifting in rainy tokyo at night, cinematic 4k`"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['video', 'omni'])
def create_video(message):
    prompt = message.text.replace('/video', '').replace('/omni', '').strip()
    if not prompt:
        bot.reply_to(message, "⚠️ Напиши промпт:\n`/video futuristic drone flying over neon city`", parse_mode='Markdown')
        return

    status_msg = bot.reply_to(message, "🎬 Генерация видео... Подожди около минуты.")

    submit_url = "https://queue.fal.run/google/gemini-omni-flash/v1.1/text-to-video"
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "prompt": prompt,
        "duration": 10,
        "aspect_ratio": "16:9",
        "resolution": "720p"
    }).encode('utf-8')

    temp_file = f"video_{message.chat.id}_{int(time.time())}.mp4"
    try:
        req = urllib.request.Request(submit_url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            submit_res = json.loads(resp.read().decode('utf-8'))

        status_url = submit_res.get("status_url")
        response_url = submit_res.get("response_url")

        video_url = None
        for _ in range(60):
            time.sleep(3)
            check_req = urllib.request.Request(status_url, headers=headers)
            with urllib.request.urlopen(check_req, timeout=30) as check_resp:
                check_data = json.loads(check_resp.read().decode('utf-8'))
                if check_data.get("status") == "COMPLETED":
                    res_req = urllib.request.Request(response_url, headers=headers)
                    with urllib.request.urlopen(res_req, timeout=30) as r_resp:
                        final_data = json.loads(r_resp.read().decode('utf-8'))
                        video_obj = final_data.get("video")
                        if isinstance(video_obj, dict):
                            video_url = video_obj.get("url")
                        elif isinstance(video_obj, str):
                            video_url = video_obj
                    break
                elif check_data.get("status") == "FAILED":
                    bot.reply_to(message, f"❌ Генерация не удалась: {check_data.get('error', 'неизвестная ошибка')}")
                    return

        if not video_url:
            bot.reply_to(message, "❌ Не удалось получить видео (таймаут). Попробуй ещё раз.")
            return

        req_dl = urllib.request.Request(video_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_dl, timeout=120) as v_resp, open(temp_file, 'wb') as f:
            f.write(v_resp.read())

        with open(temp_file, 'rb') as vf:
            bot.send_video(
                message.chat.id,
                video=vf,
                caption=f"🎬 **Omni Flash 1.1:**\n{prompt}",
                supports_streaming=True,
                parse_mode='Markdown'
            )

        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception:
            pass

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, f"❌ Ошибка генерации: {e}")

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

print("Бот запущен!")
bot.infinity_polling(timeout=20, long_polling_timeout=10)
