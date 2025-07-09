 
import os
import re
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Получаем токен из переменной окружения
TOKEN = os.getenv("TOKEN")

# Функция для очистки имени файла
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

# Функция для скачивания обложки
def download_thumbnail(url, filename):
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)
    return filename

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Напиши название песни, и я найду её.")

# Обработка текстовых сообщений
async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.reply_text(f"Ищу: {query}...")

    # Настройки yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0',
        'cookies': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Поиск нескольких результатов
            result = ydl.extract_info(f"ytsearch3:{query}", download=False)
            entries = result.get('entries', [])

        if not entries:
            await update.message.reply_text("Ничего не найдено. Попробуйте другой запрос.")
            return

        # Пробуем скачать первое доступное видео
        for entry in entries:
            try:
                video_title = entry['title']
                video_id = entry['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                # Скачиваем
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(video_url, download=True)
                    clean_title = sanitize_filename(video_title)
                    file_ext = result['ext']
                    file_name = f"{clean_title}.{file_ext}"
                    thumbnail_url = result.get('thumbnail', '')

                # Скачиваем обложку
                thumbnail_file = f"{clean_title}_thumb.jpg"
                if thumbnail_url:
                    download_thumbnail(thumbnail_url, thumbnail_file)

                # Отправляем название, обложку и аудио
                await update.message.reply_text(f"Песня: {video_title}")
                if os.path.exists(thumbnail_file):
                    with open(thumbnail_file, 'rb') as thumb:
                        await update.message.reply_photo(photo=thumb)
                    os.remove(thumbnail_file)

                with open(file_name, 'rb') as audio:
                    await update.message.reply_audio(audio=audio)

                os.remove(file_name)
                return  # Успешно, выходим

            except Exception as e:
                # Пропускаем недоступное видео
                continue

        await update.message.reply_text("Все найденные видео недоступны. Попробуйте другой запрос.")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

def main():
    if not TOKEN:
        raise ValueError("Токен не задан в переменной окружения TOKEN")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_music))

    app.run_polling()

if __name__ == "__main__":
    main()