import telebot
import urllib.parse
import random
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

TOKEN = '8897966443:AAHx6x6r00rVmFeFCmzQGrwTftU63cys828'
bot = telebot.TeleBot(TOKEN)

# Мини-сервер, чтобы хостинг видел живой порт
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
        "Привет! Я работаю 24/7 в облаке:\n\n"
        "🎨 **Картинка**: просто напиши описание на английском\n"
        "🎬 **Видео**: напиши `/video описание на английском`"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['video'])
def create_video(message):
    prompt = message.text.replace('/video', '').strip()
    if not prompt:
        bot.reply_to(message, "Напиши текст: `/video car drifting`", parse_mode='Markdown')
        return

    bot.reply_to(message, "🎬 Видео генерируется (около 1 мин)...")
    seed = random.randint(1, 9999999)
    encoded = urllib.parse.quote(prompt)
    video_url = f"https://image.pollinations.ai/prompt/{encoded}?model=video&seed={seed}"

    try:
        bot.send_video(message.chat.id, video=video_url, caption=f"🎬 {prompt}")
    except Exception:
        bot.reply_to(message, "Ошибка создания видео.")

@bot.message_handler(func=lambda message: True)
def draw(message):
    prompt = message.text
    bot.reply_to(message, "🎨 Рисую через Flux...")
    seed = random.randint(1, 9999999)
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?model=flux&width=1024&height=1024&seed={seed}&nologo=true"

    try:
        bot.send_photo(message.chat.id, photo=url, caption=f"Запрос: {prompt}")
    except Exception:
        bot.reply_to(message, "Ошибка генерации.")

print("Бот запущен 24/7!")
bot.infinity_polling()
