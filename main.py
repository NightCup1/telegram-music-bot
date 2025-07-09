import os
import re
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from yt_dlp import YoutubeDL

# Получаем токен из переменной окружения
TOKEN = os.getenv("TOKEN")

# Очистка имени файла
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

# Скачивание обложки
def download_thumbnail(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)
    return filename

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши название песни, и я найду её.")

# Поиск и скачивание музыки
async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.reply_text(f"Ищу: {query}...")

    ydl_opts_search = {
        'quiet': True,
        'geo_bypass': True,
        'force_ipv4': True,
        'sleep_interval': 1,
        'retries': 3,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    }

    ydl_opts_download = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'geo_bypass': True,
        'force_ipv4': True,
        'sleep_interval': 1,
        'retries': 3,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with YoutubeDL(ydl_opts_search) as ydl:
            result = ydl.extract_info(f"ytsearch3:{query}", download=False)
            entries = result.get('entries', [])

        if not entries:
            await update.message.reply_text("Ничего не найдено. Попробуйте другой запрос.")
            return

        for entry in entries:
            try:
                video_title = entry['title']
                video_id = entry['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                with YoutubeDL(ydl_opts_download) as ydl:
                    result = ydl.extract_info(video_url, download=True)
                    clean_title = sanitize_filename(video_title)
                    file_name = f"{clean_title}.mp3"
                    thumbnail_url = result.get('thumbnail', '')

                # Отправка сообщения и файла
                await update.message.reply_text(f"Песня: {video_title}")

                if thumbnail_url:
                    thumb_file = f"{clean_title}_thumb.jpg"
                    download_thumbnail(thumbnail_url, thumb_file)
                    if os.path.exists(thumb_file):
                        with open(thumb_file, 'rb') as thumb:
                            await update.message.reply_photo(photo=thumb)
                        os.remove(thumb_file)

                if os.path.exists(file_name):
                    with open(file_name, 'rb') as audio:
                        await update.message.reply_audio(audio=audio)
                    os.remove(file_name)

                return  # Успех — выходим

            except Exception as e:
                print(f"[WARNING] Ошибка при загрузке {entry.get('title')}: {e}")
                continue

        await update.message.reply_text("Все найденные видео недоступны. Попробуйте другой запрос.")

    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {str(e)}")

def main():
    if not TOKEN:
        raise ValueError("Токен не задан в переменной окружения TOKEN")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))
    app.run_polling()

if __name__ == "__main__":
    main()