import telebot
import urllib.parse
import urllib.request
import json
import random
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

TOKEN = '8897966443:AAHx6x6r00rVmFeFCmzQGrwTftU63cys828'
bot = telebot.TeleBot(TOKEN)

# Сервер для поддержания активности Render 24/7
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
        "👋 **AI Studio Bot**\n\n"
        "🎬 **/video <описание>** или **/omni <описание>** — генерация видео на **10 секунд**\n"
        "🎨 **/pic <описание>** — нарисовать арт\n"
        "💬 **Любой вопрос** — общение с нейросетью"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

# Генерация 10-секундного видео
@bot.message_handler(commands=['video', 'omni'])
def create_10s_video(message):
    prompt = message.text.replace('/video', '').replace('/omni', '').strip()
    if not prompt:
        bot.reply_to(message, "⚠️ Напиши описание:\nПример: `/video neon car speeding down highway at night`", parse_mode='Markdown')
        return

    status_msg = bot.reply_to(message, "⏳ Создаю видео на 10 секунд... Рендер занимает около 2-3 минут, подожди пожалуйста.")
    
    seed = random.randint(1, 9999999)
    encoded = urllib.parse.quote(prompt)
    
    # Задаём duration=10 для 10-секундного ролика
    video_url = f"https://image.pollinations.ai/prompt/{encoded}?model=wan&duration=10&seed={seed}&nologo=true"
    temp_filename = f"video_{message.chat.id}_{seed}.mp4"

    try:
        req = urllib.request.Request(video_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=360) as response, open(temp_filename, 'wb') as out_file:
            out_file.write(response.read())

        with open(temp_filename, 'rb') as video_file:
            bot.send_video(
                message.chat.id,
                video=video_file,
                caption=f"🎬 **Видео (10 сек):** {prompt}",
                supports_streaming=True,
                parse_mode='Markdown'
            )

        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception:
            pass

    except Exception as e:
        print(f"Video Error: {e}")
        bot.reply_to(message, "❌ Сервер генерации видео перегружен или не ответил вовремя. Попробуй ещё раз чуть позже.")
    
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

# Рисование картинок
@bot.message_handler(commands=['pic'])
def create_pic(message):
    prompt = message.text.replace('/pic', '').strip()
    if not prompt:
        bot.reply_to(message, "⚠️ Напиши промпт: `/pic futuristic robot in cyberpunk city`", parse_mode='Markdown')
        return
    bot.reply_to(message, "🎨 Рисую изображение...")
    seed = random.randint(1, 9999999)
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?model=flux&width=1024&height=1024&seed={seed}&nologo=true"
    try:
        bot.send_photo(message.chat.id, photo=url, caption=f"✨ {prompt}")
    except Exception as e:
        print(f"Pic Error: {e}")
        bot.reply_to(message, "❌ Ошибка при генерации картинки.")

# Текстовый диалог по любому другому сообщению
@bot.message_handler(func=lambda message: True)
def chat_ai(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        api_url = "https://text.pollinations.ai/openai"
        payload = {
            "model": "gemini-flash",
            "messages": [
                {"role": "system", "content": "Ты полезный ассистент, отвечай кратко и точно на русском языке."},
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
        bot.reply_to(message, "⚠️ Сервер не ответил, попробуй позже.")

print("Бот запущен с генерацией на 10 сек!")
bot.infinity_polling(timeout=20, long_polling_timeout=10)
