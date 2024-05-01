import os
import subprocess
from moviepy.editor import VideoFileClip
from telethon import TelegramClient, events, sync
from telethon.tl.types import DocumentAttributeVideo
from dotenv import load_dotenv
import pyfiglet
from FastTelethon import download_file, upload_file

load_dotenv()

download_directory = "./downloads"
pdf_download_directory = f"{download_directory}/pdfs"
video_download_directory = f"{download_directory}/video"
thumbnail_download_directory = f"{download_directory}/thumbnail"

if not os.path.exists(download_directory):
    os.makedirs(download_directory)
    os.makedirs(pdf_download_directory)
    os.makedirs(video_download_directory)
    os.makedirs(thumbnail_download_directory)

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
            uploader = await upload_file(telethon_client, file, event.chat_id)
            lines = file.readlines()
            for line in lines:
                file_name, file_url = line.strip().split(':', 1)
                try:
                    await progress_message.edit(f"Downloading {file_name}...")
                    if file_url.endswith('.pdf'):
                        command_to_exec = [
                            "yt-dlp",
                            "-o", f"{pdf_download_directory}/{file_name}",              
                            file_url
                        ]
                        subprocess.run(command_to_exec, check=True)
                        downloaded_file_path = f"{pdf_download_directory}/{file_name}"
                        await progress_message.edit(f"Uploading {file_name}...")
                        uploader = await upload_file(telethon_client, downloaded_file_path, event.chat_id)
                        await telethon_client.send_file(event.chat_id, uploader, caption=file_name)
                    else:
                        command_to_exec = [
                            "yt-dlp",
                            "--geo-bypass-country", "US",
                            "--retries",
                            "25",
                            "--fragment-retries",
                            "25",
                            "--force-overwrites",
                            "--no-keep-video",
                            "-i",
                            "--external-downloader", "axel",
                            "--external-downloader-args", "'-n 6 -a -k 1M -s 16'"
                            "--add-metadata",
                            "-o", f"{video_download_directory}/{file_name}.%(ext)s",
                            file_url
                        ]
                        subprocess.run(command_to_exec, check=True)
                        downloaded_file_path = f"{video_download_directory}/{file_name}"
                        thumbnail_path = f"{thumbnail_download_directory}/{file_name}.jpg"
                        clip = VideoFileClip(downloaded_file_path + '.mp4')
                        clip.save_frame(thumbnail_path, t=1)
                        width, height = clip.size
                        duration = int(clip.duration)
                        clip.close()
                        
                        await progress_message.edit(f"Uploading {file_name}...")
                        with open(downloaded_file_path, 'rb') as upload_file_object:
                            uploader = await upload_file(telethon_client, upload_file_object, event.chat_id)
                            await telethon_client.send_file(event.chat_id, uploader, caption=file_name)
                except Exception as e:
                    await event.respond(f"Failed to download {file_name}. Error: {str(e)}")
                    continue
        os.remove(file_path)
        if os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)
            os.remove(thumbnail_path)

custom_fig = pyfiglet.Figlet(font='small')
print(custom_fig.renderText('Bot deployed'))

telethon_client.run_until_disconnected()
