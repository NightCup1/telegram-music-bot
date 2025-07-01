import asyncio
import os
from aiogram import Bot, Dispatcher, types
import yt_dlp
import logging
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Чтение токена
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    logging.error("BOT_TOKEN не найден в переменных окружения!")
    exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Регистрация бота с диспетчером
dp["bot"] = bot  # Привязка бота к контексту (альтернатива)

@dp.message_handler()
async def download_music(message: types.Message):
    query = message.text
    await message.reply("🔍 Ищу и скачиваю музыку...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': 'downloaded.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            file_name = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")

        with open(file_name, "rb") as audio:
            await message.reply_audio(audio, title=info.get('title', "Audio"))

        try:
            os.remove(file_name)
        except Exception as e:
            logging.warning(f"Не удалось удалить файл {file_name}: {e}")

    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")
        logging.error(f"Ошибка при обработке запроса: {e}")

async def main():
    logging.info("Бот запущен, начинаю polling...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())


