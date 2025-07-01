import asyncio
from aiogram import Bot, Dispatcher, types
import yt_dlp
import os

API_TOKEN = "7859831857:AAErQpVltZWQ5k9dUEAeugsTm9OjDq645rQ"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

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
            await message.reply_audio(audio, title=info.get('title'))

        os.remove(file_name)

    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

async def main():
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
