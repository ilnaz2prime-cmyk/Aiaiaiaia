import telebot
import os
import json
import urllib.request
import urllib.parse
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

TOKEN = '8897966443:AAHx6x6r00rVmFeFCmzQGrwTftU63cys828'
bot = telebot.TeleBot(TOKEN)

# Веб-сервер для удержания Render 24/7
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
        "👋 **AI Studio Bot на связи!**\n\n"
        "🎬 **/video <описание>** — генерация видеофайла MP4 (5–10 сек)\n"
        "💬 **Любое текстовое сообщение** — общение с Gemini Flash AI"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

# Генерация видео через Wan2.1 Gradio API без авторизации
@bot.message_handler(commands=['video', 'omni'])
def create_video(message):
    prompt = message.text.replace('/video', '').replace('/omni', '').strip()
    if not prompt:
        bot.reply_to(message, "⚠️ Напиши описание сцены на английском:\n`/video a neon sports car drifting in the rain at night, 4k`", parse_mode='Markdown')
        return

    status_msg = bot.reply_to(message, "🎬 Генерация видео запущена через Wan2.1... Рендер занимает около 1-2 минут.")

    temp_file = f"video_{message.chat.id}.mp4"
    try:
        # 1. Отправляем запрос на генерацию в открытый gradio-эндпоинт
        init_url = "https://wan-ai-wan2-1.hf.space/gradio_api/call/generate_video"
        payload = json.dumps({"data": [prompt, 10, "16:9"]}).encode('utf-8')
        req = urllib.request.Request(init_url, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            event_id = json.loads(resp.read().decode('utf-8')).get("event_id")

        if not event_id:
            raise Exception("Не получен event_id генератора.")

        # 2. Ожидаем результат потока данных
        result_url = f"https://wan-ai-wan2-1.hf.space/gradio_api/call/generate_video/{event_id}"
        video_url = None

        for _ in range(60):
            time.sleep(3)
            stream_req = urllib.request.Request(result_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(stream_req, timeout=30) as stream_resp:
                raw_lines = stream_resp.read().decode('utf-8').split('\n')
                for line in raw_lines:
                    if line.startswith("data:"):
                        data_payload = json.loads(line.replace("data:", "").strip())
                        if isinstance(data_payload, list) and len(data_payload) > 0:
                            v_data = data_payload[0]
                            video_url = v_data.get("video", {}).get("url") or v_data.get("url")
                            break
            if video_url:
                break

        if not video_url:
            bot.reply_to(message, "❌ Время ожидания рендера истекло. Попробуй ещё раз чуть позже.")
            return

        # 3. Скачиваем готовый видеофайл и отправляем в чат
        dl_req = urllib.request.Request(video_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(dl_req, timeout=120) as v_stream, open(temp_file, 'wb') as f:
            f.write(v_stream.read())

        with open(temp_file, 'rb') as vf:
            bot.send_video(
                message.chat.id,
                video=vf,
                caption=f"🎬 **Результат:**\n{prompt}",
                supports_streaming=True,
                parse_mode='Markdown'
            )

        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception:
            pass

    except Exception as e:
        print(f"Video Error: {e}")
        bot.reply_to(message, f"❌ Ошибка рендера: {e}")

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

# Gemini Flash текстовый чат
@bot.message_handler(func=lambda message: True)
def text_dialog(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        api_url = "https://text.pollinations.ai/openai"
        payload = {
            "model": "gemini-flash",
            "messages": [
                {"role": "system", "content": "Ты дружелюбный ассистент, отвечай точно и на русском языке."},
                {"role": "user", "content": message.text}
            ]
        }
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            reply = data['choices'][0]['message']['content']
        bot.reply_to(message, reply)
    except Exception as e:
        print(f"Chat Error: {e}")
        bot.reply_to(message, "⚠️ Сервер перегружен, попробуй позже.")

print("Бот готов к работе!")
bot.infinity_polling(timeout=20, long_polling_timeout=10)
