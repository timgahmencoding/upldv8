import os, asyncio
from telethon import TelegramClient, events, sync
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip

load_dotenv()
download_dir = "./downloads"
os.makedirs(download_dir, exist_ok=True)

bot = TelegramClient('bot', os.getenv("API_ID"), os.getenv("API_HASH")).start()

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Send the .txt file with URLs.")

@bot.on(events.NewMessage(pattern='.*\\.txt$'))
async def handle_docs(event):
    if event.document:
        path = await event.download_media(file=download_dir)
        with open(path, 'r') as f:
            lines = (line.strip().split(':', 1) for line in f)
        for name, url in lines:
            try:
                if url.endswith('.pdf'):
                    await download_and_send(bot, event, url, name, 'pdf')
                else:
                    await download_and_send(bot, event, url, name, 'video')
            except Exception as e:
                await event.respond(f"Error downloading {url}: {str(e)}")
            finally:
                cleanup_files(path, name, url.endswith('.pdf'))
    else:
        await event.respond("Invalid file.")

def cleanup_files(path, name, is_pdf):
    os.remove(path)
    if not is_pdf:
        os.remove(f"{download_dir}/{name}.jpg")
        os.remove(f"{download_dir}/{name}.mp4")

async def download_and_send(bot, event, url, name, file_type):
    ext = 'pdf' if file_type == 'pdf' else 'mp4'
    file_path = f"{download_dir}/{name}.{ext}"
    await bot.send_message(event.chat_id, f"Downloading {name}...")
    # Replace with your download logic
    await bot.send_message(event.chat_id, f"Uploading {name}...")
    if file_type == 'video':
        thumb_path = f"{download_dir}/{name}.jpg"
        clip = VideoFileClip(file_path)
        clip.save_frame(thumb_path, t=1)
        w, h = clip.size
        d = int(clip.duration)
        clip.close()
        await bot.send_file(event.chat_id, file_path, thumb=thumb_path, caption=name, supports_streaming=True, width=w, height=h, duration=d)
    else:
        await bot.send_file(event.chat_id, file_path, caption=name)

print('Bot deployed.')
bot.run_until_disconnected()
                                            
