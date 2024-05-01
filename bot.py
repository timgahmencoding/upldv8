import os
import subprocess
from moviepy.editor import VideoFileClip
from telethon import TelegramClient, events, sync
from telethon.tl.types import DocumentAttributeVideo
from dotenv import load_dotenv
import pyfiglet
from ethon.telefunc import fast_upload

load_dotenv()

download_directory = "./downloads"
if not os.path.exists(download_directory):
    os.makedirs(download_directory)

telethon_client = TelegramClient('BULK-UPLOAD-BOT', int(os.getenv("API_ID")), os.getenv("API_HASH"))
telethon_client.start(bot_token=os.getenv("BOT_TOKEN"))

@telethon_client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Please send the .txt file with the video and PDF URLs.")

@telethon_client.on(events.NewMessage(incoming=True, pattern=None))
async def handle_docs(event):
    if event.document:
        progress_message = await event.respond("Preparing to download...")
        file_path = await event.download_media(file=download_directory)
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                file_name, file_url = line.strip().split(':', 1)
                try:
                    await progress_message.edit(f"Downloading {file_name}...")
                    if file_url.endswith('.pdf'):
                        command_to_exec = [
                            "yt-dlp",
                            "-o", f"{download_directory}/{file_name}",
                            file_url
                        ]
                        subprocess.run(command_to_exec, check=True)
                        downloaded_file_path = f"{download_directory}/{file_name}"
                        await progress_message.edit(f"Uploading {file_name}...")
                        uploader = await fast_upload(telethon_client, downloaded_file_path, event.chat_id)
                        await telethon_client.send_file(event.chat_id, uploader, caption=file_name)
                    else:
                        command_to_exec = [
                            "yt-dlp",
                            "--geo-bypass-country", "US",
                            "--socket-timeout", "15",
                            "--retries",
                            "25",
                            "--fragment-retries",
                            "25",
                            "--force-overwrites",
                            "--no-keep-video",
                            "-i",
                            "--external-downloader", "axel",
                            "--external-downloader-args", "-n 10 -a -k 1M",
                            "--add-metadata",
                            "-o", f"{download_directory}/{file_name}.%(ext)s",
                            file_url
                        ]
                        subprocess.run(command_to_exec, check=True)
                        downloaded_file_path = f"{download_directory}/{file_name}"
                     #   await progress_message.edit(f"Uploading {file_name}...")
                        thumbnail_path = f"{download_directory}/{file_name}.jpg"
                        clip = VideoFileClip(downloaded_file_path + '.mp4')
                        clip.save_frame(thumbnail_path, t=1)
                        width, height = clip.size
                        duration = int(clip.duration)
                        clip.close()
                        uploader = await fast_upload(telethon_client, downloaded_file_path, event.chat_id, bot=telethon_client, event=event, msg="Uploading {file_name}...")
                        await telethon_client.send_file(event.chat_id, uploader, caption=file_name, thumb=thumbnail_path, attributes=[
                            DocumentAttributeVideo(
                                duration=duration,
                                w=width,
                                h=height,
                                supports_streaming=True
                            )
                        ])
                except subprocess.CalledProcessError as e:
                    await event.respond(f"Failed to download {file_name}. Skipping to the next file.")
        os.remove(file_path)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        if os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)

custom_fig = pyfiglet.Figlet(font='small')
print(custom_fig.renderText('Bot deployed'))

telethon_client.run_until_disconnected()
        
