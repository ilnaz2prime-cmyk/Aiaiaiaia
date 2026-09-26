import telebot
import os
import json
import urllib.request
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

TOKEN = '8897966443:AAHx6x6r00rVmFeFCmzQGrwTftU63cys828'
FAL_KEY = '056a7ecc-510c-4c73-94d9-901a65d0f8fd:6a63da9d7da7f3cff77a297a3f46bd0e'

bot = telebot.TeleBot(TOKEN)

# Сервер для работы Render 24/7
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
        "👋 **Gemini Omni Flash 1.1 Video Bot**\n\n"
        "Отправь запрос:\n"
        "`/video <описание на английском>`\n\n"
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

    status_msg = bot.reply_to(message, "🎬 Генерация через **Gemini Omni Flash 1.1** (10 сек)... Подожди около минуты.")

    # Модель Gemini Omni Flash 1.1 на fal.ai
    submit_url = "https://queue.fal.run/fal-ai/google/gemini-omni-flash/v1.1/text-to-video"
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    payload = json.dumps({
        "prompt": prompt,
        "duration": "10s",
        "aspect_ratio": "16:9"
    }).encode('utf-8')

    temp_file = f"video_{message.chat.id}.mp4"
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
                        video_obj = final_data.get("video", {})
                        video_url = video_obj.get("url") if isinstance(video_obj, dict) else final_data.get("video_url")
                    break

        if not video_url:
            bot.reply_to(message, "❌ Не удалось получить видео (таймаут). Попробуй ещё раз.")
            return

        urllib.request.urlretrieve(video_url, temp_file)

        with open(temp_file, 'rb') as vf:
            bot.send_video(
                message.chat.id,
                video=vf,
                caption=f"🎬 **Gemini Omni Flash 1.1 (10 сек):**\n{prompt}",
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
