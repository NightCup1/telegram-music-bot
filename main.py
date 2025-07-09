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
    await update.message.reply_text("Привет! Напиши название песни, я найду варианты, и ты выберешь, что скачать.")

# Обработка текстового запроса для поиска
async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    await update.message.reply_text(f"Ищу: {query}...")

    # Настройки yt-dlp для поиска
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0',
        'extract_flat': True,
        'default_search': 'ytsearch5',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(query, download=False)
            entries = result['entries']

        if not entries:
            await update.message.reply_text("Ничего не найдено.")
            return

        context.user_data['search_results'] = entries
        song_list = "\n".join(f"{i+1}. {entry['title']}" for i, entry in enumerate(entries))
        await update.message.reply_text(f"Выберите песню (введите номер):\n{song_list}")

    except Exception as e:
        await update.message.reply_text(f"Ошибка поиска: {str(e)}")

# Обработка выбора песни
async def download_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('search_results'):
        await update.message.reply_text("Сначала выполните поиск, отправив название песни.")
        return

    try:
        choice = int(update.message.text) - 1
        entries = context.user_data['search_results']

        if choice < 0 or choice >= len(entries):
            await update.message.reply_text("Неверный номер. Выберите номер из списка.")
            return

        selected = entries[choice]
        video_url = f"https://www.youtube.com/watch?v={selected['id']}"
        await update.message.reply_text(f"Обрабатываю: {selected['title']}...")

        # Настройки yt-dlp для скачивания
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(video_url, download=True)
            video_title = result['title']
            file_ext = result['ext']
            clean_title = sanitize_filename(video_title)
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
        context.user_data['search_results'] = None

    except ValueError:
        await update.message.reply_text("Введите число (номер песни).")
    except Exception as e:
        await update.message.reply_text(f"Ошибка скачивания: {str(e)}")

def main():
    if not TOKEN:
        raise ValueError("Токен не задан в переменной окружения TOKEN")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.Regex(r'^\d+$'), search_music))
    app.add_handler(MessageHandler(filters.Regex(r'^\d+$'), download_choice))

    app.run_polling()

if __name__ == "__main__":
    main()