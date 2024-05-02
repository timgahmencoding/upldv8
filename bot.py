import os
import subprocess
from telethon import TelegramClient, events
from dotenv import load_dotenv
import cv2
from telethon.tl.types import DocumentAttributeVideo
import asyncio
import uvloop
import time
from parallel_file_transfer import fast_upload, progress, time_formatter

def sanitize_filename(filename):
    return filename.replace('(', '').replace(')', '').replace(' ', '_')

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

@telethon_client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Please send the .txt file with the video and PDF URLs.")

@telethon_client.on(events.NewMessage(incoming=True, pattern=None))
async def handle_docs(event):
    downloaded_pdf_path = None
    downloaded_video_path = None
    thumb_image_path = None
    if event.document:
        progress_message = await event.respond("Preparing to download...")
        file_path = await event.download_media(file=download_directory)
        with open(file_path, 'r') as file:
            lines = file.readlines()
        for line in lines:
            original_file_name, file_url = line.strip().split(':', 1)
            file_name = sanitize_filename(original_file_name)
            try:
                await progress_message.edit(f"Downloading {original_file_name}...")
                if file_url.endswith('.pdf'):
                    pdf_file_name = f"{file_name}.pdf"
                    command_to_exec = ["yt-dlp", "-o", f"{pdf_download_directory}/{pdf_file_name}", file_url]
                    subprocess.run(command_to_exec, check=True)
                    downloaded_pdf_path = f"{pdf_download_directory}/{pdf_file_name}"
                    start_time = time.time() * 1000
                    input_file = await fast_upload(file=downloaded_pdf_path, name=pdf_file_name, time=start_time, bot=telethon_client, event=progress_message, msg="Uploading PDF")
                    await telethon_client.send_file(event.chat_id, file=input_file, caption=pdf_file_name)
                else:
                    video_file_name = f"{file_name}.mp4"
                    downloaded_video_path = f"{video_download_directory}/{video_file_name}"
                    command_to_exec = ["yt-dlp", "--geo-bypass-country", "US", "--retries", "25", "--fragment-retries", "25", "--force-overwrites", "--no-keep-video", "-i", "--external-downloader", "axel", "--external-downloader-args", "axel:-n 5", "--add-metadata", "-o", downloaded_video_path, file_url]
                    subprocess.run(command_to_exec, check=True)
                    thumb_image_path = f"{thumbnail_download_directory}/{file_name}.jpg"
                    thumb_cmd = f'ffmpeg -hide_banner -loglevel quiet -i {downloaded_video_path} -ss 00:00:02 -vframes 1 -update 1 {thumb_image_path}'
                    os.system(thumb_cmd)
                    vid = cv2.VideoCapture(downloaded_video_path)
                    width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
                    height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    duration = int(vid.get(cv2.CAP_PROP_FRAME_COUNT) / vid.get(cv2.CAP_PROP_FPS))
                    vid.release()
                    attributes = [DocumentAttributeVideo(
                        w=int(width),
                        h=int(height),
                        duration=duration,
                        supports_streaming=True
                    )]
                 #   test = await progress_message.edit(f"Uploading {video_file_name}...")
                    start_time = time.time() * 1000
                    input_file = await fast_upload(file=downloaded_video_path, name=video_file_name, time=start_time, bot=telethon_client, event=progress_message, msg="Uploading: " + video_file_name)
                    await telethon_client.send_file(event.chat_id, file=input_file, thumb=thumb_image_path, attributes=attributes, caption=video_file_name)
            except Exception as e:
                await event.respond(f"Failed to download {original_file_name}. Error: {str(e)}")
                continue
        await progress_message.edit("All files uploaded successfully.")
        os.remove(file_path)
        if downloaded_pdf_path and os.path.exists(downloaded_pdf_path):
            os.remove(downloaded_pdf_path)
        if downloaded_video_path and os.path.exists(downloaded_video_path):
            os.remove(downloaded_video_path)
        if thumb_image_path and os.path.exists(thumb_image_path):
            os.remove(thumb_image_path)

print("Bot successfully deployed.")

telethon_client.run_until_disconnected()
