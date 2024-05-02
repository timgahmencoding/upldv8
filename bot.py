import os
import subprocess
import cv2
import asyncio
import uvloop
import time
import unicodedata
import re
import backoff
from telethon import TelegramClient, events, errors
from telethon.tl.types import DocumentAttributeVideo
from dotenv import load_dotenv
from parallel_file_transfer import fast_upload

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

load_dotenv()

download_directory = "./downloads"
pdf_download_directory = f"{download_directory}/pdfs"
video_download_directory = f"{download_directory}/video"
thumbnail_download_directory = f"{download_directory}/thumbnail"
os.makedirs(download_directory, exist_ok=True)
os.makedirs(pdf_download_directory, exist_ok=True)
os.makedirs(video_download_directory, exist_ok=True)
os.makedirs(thumbnail_download_directory, exist_ok=True)
telethon_client = TelegramClient('BULK-UPLOAD-BOT', int(os.getenv("API_ID")), os.getenv("API_HASH"))
telethon_client.start(bot_token=os.getenv("BOT_TOKEN"))

def sanitize_filename(filename):
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    filename = re.sub(r'[^\w\s-]', '', filename).strip()
    filename = re.sub(r'[-\s]+', '-', filename)
    filename = filename.strip('-')
    return filename

@backoff.on_exception(backoff.expo, Exception, max_tries=5)
async def download_file(command_to_exec):
    subprocess.run(command_to_exec, check=True)

@backoff.on_exception(backoff.expo, Exception, max_tries=5)
async def upload_file(file_path, file_name, is_pdf, event, progress_message):
    start_time = time.time() * 1000
    input_file = await fast_upload(file=file_path, name=file_name, time=start_time, bot=telethon_client, event=progress_message, msg="Uploading: " + file_name)
    try:
        if is_pdf:
            await telethon_client.send_file(event.chat_id, file=input_file, caption=file_name)
        else:
            vid = cv2.VideoCapture(file_path)
            width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
            duration = int(vid.get(cv2.CAP_PROP_FRAME_COUNT) / vid.get(cv2.CAP_PROP_FPS))
            vid.release()
            attributes = [DocumentAttributeVideo(w=int(width), h=int(height), duration=duration, supports_streaming=True)]
            thumb_image_path = f"{thumbnail_download_directory}/{file_name}.jpg"
            thum_command_to_exec = ['ffmpeg', '-hide_banner', '-loglevel', 'quiet', '-i', file_path, '-vf', 'thumbnail,scale=1280:-1', '-frames:v', '1', thumb_image_path]
            subprocess.run(thum_command_to_exec, check=True)
            await telethon_client.send_file(event.chat_id, file=input_file, thumb=thumb_image_path, attributes=attributes, caption=file_name)
    except errors.FloodWaitError as e:
        time.sleep(e.seconds)
        await upload_file(file_path, file_name, is_pdf, event, progress_message)

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
        start_index = await event.respond("Enter the starting index for downloading files: ")
        start_index = int(start_index.message.message)
        for line in lines[start_index:]:
            original_file_name, file_url = line.strip().split(':', 1)
            file_name = sanitize_filename(original_file_name)
            try:
                await progress_message.edit(f"Downloading {original_file_name}...")
                if file_url.endswith('.pdf'):
                    pdf_file_name = f"{file_name}.pdf"
                    command_to_exec = ["yt-dlp", "-o", f"{pdf_download_directory}/{pdf_file_name}", file_url]
                    await download_file(command_to_exec)
                    downloaded_pdf_path = f"{pdf_download_directory}/{pdf_file_name}"
                    await upload_file(downloaded_pdf_path, pdf_file_name, True, event, progress_message)
                else:
                    video_file_name = f"{file_name}.mp4"
                    downloaded_video_path = f"{video_download_directory}/{video_file_name}"
                    command_to_exec = ["yt-dlp", "--geo-bypass-country", "IN", "-N", "6", "--socket-timeout", "20", "--no-part", "--concurrent-fragments", "10", "--retries", "25", "--fragment-retries", "25", "--force-overwrites", "--no-keep-video", "-i", "--add-metadata", "-o", downloaded_video_path, file_url]
                    await download_file(command_to_exec)
                    await upload_file(downloaded_video_path, video_file_name, False, event, progress_message)
            except Exception as e:
                await event.respond(f"Failed to download {original_file_name}. Error: {str(e)}")
                continue
        await progress_message.edit("All files uploaded successfully.")
        os.remove(file_path)

telethon_client.run_until_disconnected()
