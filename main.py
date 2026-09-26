import telebot
import urllib.parse
import random

TOKEN = '8897966443:AAHx6x6r00rVmFeFCmzQGrwTftU63cys828'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "Привет! Я умею генерировать медиа:\n\n"
        "🎨 **Картинка**: просто напиши описание на английском\n"
        "🎬 **Видео**: напиши `/video описание на английском`"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['video'])
def create_video(message):
    prompt = message.text.replace('/video', '').strip()
    if not prompt:
        bot.reply_to(message, "Напиши текст после команды, например:\n`/video running dog neon city`", parse_mode='Markdown')
        return

    bot.reply_to(message, "🎬 Видео генерируется (около 1 минуты), подожди...")
    seed = random.randint(1, 9999999)
    encoded = urllib.parse.quote(prompt)
    video_url = f"https://image.pollinations.ai/prompt/{encoded}?model=video&seed={seed}"

    try:
        bot.send_video(message.chat.id, video=video_url, caption=f"🎬 Видео: {prompt}")
    except Exception:
        bot.reply_to(message, "Ошибка создания видео. Попробуй запрос короче.")

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
        bot.reply_to(message, "Ошибка генерации, попробуй другой текст.")

print("Бот работает 24/7!")
bot.infinity_polling()
