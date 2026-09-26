import telebot
import urllib.parse
import urllib.request
import random
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

TOKEN = '8897966443:AAHx6x6r00rVmFeFCmzQGrwTftU63cys828'
bot = telebot.TeleBot(TOKEN)

# Мини веб-сервер для Render (24/7)
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

# Приветствие /start
@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "👋 **AI Studio Bot на связи!**\n\n"
        "🎬 **/omni <описание>** — генерация видео через **Gemini Omni Flash 1.1**\n"
        "🎥 **/video <описание>** — обычное AI видео\n"
        "🎨 **Любой текст** — генерация арта через Flux"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

# Функция скачивания и отправки видео
def generate_and_send_video(message, prompt, model_name, title):
    status_msg = bot.reply_to(message, f"⏳ {title} генерируется (около 1–2 мин)...")
    seed = random.randint(1, 9999999)
    encoded = urllib.parse.quote(prompt)
    
    video_url = f"https://image.pollinations.ai/prompt/{encoded}?model={model_name}&seed={seed}"
    temp_filename = f"vid_{message.chat.id}_{seed}.mp4"

    try:
        req = urllib.request.Request(
            video_url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=240) as response, open(temp_filename, 'wb') as out_file:
            out_file.write(response.read())

        with open(temp_filename, 'rb') as video_file:
            bot.send_video(
                message.chat.id, 
                video=video_file, 
                caption=f"✨ **{title}**\n📝 {prompt}",
                parse_mode='Markdown'
            )
        
        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception:
            pass

    except Exception as e:
        print(f"Error ({model_name}): {e}")
        bot.reply_to(message, f"❌ Ошибка генерации ({title}). Сервер перегружен, попробуй позже.")

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

# Команда для Omni Flash 1.1
@bot.message_handler(commands=['omni'])
def create_omni(message):
    prompt = message.text.replace('/omni', '').strip()
    if not prompt:
        bot.reply_to(message, "⚠️ Напиши промпт: `/omni cinematic cyberpunk chase, 4k`", parse_mode='Markdown')
        return
    generate_and_send_video(message, prompt, "gemini-omni-1.1-flash", "Gemini Omni Flash 1.1")

# Обычное видео
@bot.message_handler(commands=['video'])
def create_video(message):
    prompt = message.text.replace('/video', '').strip()
    if not prompt:
        bot.reply_to(message, "⚠️ Напиши промпт: `/video drone flight over ocean`", parse_mode='Markdown')
        return
    generate_and_send_video(message, prompt, "video", "AI Video")

# Картинка
@bot.message_handler(func=lambda message: True)
def draw(message):
    prompt = message.text
    bot.reply_to(message, "🎨 Рисую изображение...")
    seed = random.randint(1, 9999999)
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?model=flux&width=1024&height=1024&seed={seed}&nologo=true"

    try:
        bot.send_photo(message.chat.id, photo=url, caption=f"✨ Запрос: {prompt}")
    except Exception as e:
        print(f"Image Error: {e}")
        bot.reply_to(message, "❌ Ошибка при генерации картинки.")

print("Бот с поддержкой Omni Flash запущен!")
bot.infinity_polling(timeout=20, long_polling_timeout=10)
