import os, subprocess
from moviepy.editor import VideoFileClip
from telethon import TelegramClient, events
from dotenv import load_dotenv
import asyncio

load_dotenv()
download_directory = "./downloads"
os.makedirs(download_directory, exist_ok=True)

bot = TelegramClient('BULK-UPLOAD-BOT', os.getenv("API_ID"), os.getenv("API_HASH"))

@bot.on(events.NewMessage(pattern='/start', incoming=True))
async def start(event):
    await event.respond("Please send the .txt file with the video and PDF URLs.")

@bot.on(events.NewMessage(incoming=True, pattern='.*\\.txt$'))
async def handle_docs(event):
    progress_message = await event.respond("Preparing to download...")
    if event.document:
        file_path = await event.download_media()
        with open(file_path, 'r') as file:
            lines = [line.strip().split(':', 1) for line in file]
        for file_name, file_url in lines:
            await progress_message.edit(f"Downloading {file_name}...")
            try:
                if file_url.endswith('.pdf'):
                    command_to_exec = f"yt-dlp -o {download_directory}/{file_name} {file_url}"
                    subprocess.run(command_to_exec, shell=True, check=True)
                    downloaded_file_path = f"{download_directory}/{file_name}"
                    await progress_message.edit(f"Uploading {file_name}...")
                    await bot.send_file(event.chat_id, downloaded_file_path, caption=file_name)
                else:
                    command_to_exec = f"yt-dlp --geo-bypass-country US --socket-timeout 15 --retries 25 --fragment-retries 25 --force-overwrites --no-keep-video -i --external-downloader axel --external-downloader-args 'axel:-n 5 -s 8 -k 1M' --add-metadata -o {download_directory}/{file_name}.%(ext)s {file_url}"
                    subprocess.run(command_to_exec, shell=True, check=True)
                    downloaded_file_path = f"{download_directory}/{file_name}.mp4"
                    await progress_message.edit(f"Uploading {file_name}...")
                    thumbnail_path = f"{download_directory}/{file_name}.jpg"
                    clip = VideoFileClip(downloaded_file_path)
                    clip.save_frame(thumbnail_path, t=1)
                    width, height = clip.size
                    duration = int(clip.duration)
                    clip.close()
                    await bot.send_file(event.chat_id, downloaded_file_path, thumb=thumbnail_path, caption=file_name, supports_streaming=True, width=width, height=height, duration=duration)
            except subprocess.CalledProcessError:
                await progress_message.edit(f"Failed to download {file_url}")

            asyncio.to_thread(os.remove, file_path)
            asyncio.to_thread(os.remove, thumbnail_path)
            asyncio.to_thread(os.remove, downloaded_file_path)
            
    else:
        await event.respond("Please send a valid .txt file.")

print('Bot successfully deployed.')

if __name__ == "__main__":
    bot.start()
    bot.run_until_disconnected()

