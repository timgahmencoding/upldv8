import os, subprocess
from telethon import TelegramClient, events
from dotenv import load_dotenv
from parallel_file_transfer import upload_file as parallel_upload_file
import cv2
from telethon.tl.types import DocumentAttributeVideo
import asyncio
import uvloop

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

semaphore = asyncio.Semaphore(3)
upload_queue = asyncio.Queue()

@telethon_client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond("Please send the .txt file with the video and PDF URLs.")

async def download_file(event, file_name, file_url, progress_message):
    async with semaphore:
        try:
            progress_update = await progress_message.edit(f"Downloading {file_name}...")
            if file_url.endswith('.pdf'):
                pdf_file_name = f"{file_name}.pdf"
                command_to_exec = ["yt-dlp", "-o", f"{pdf_download_directory}/{pdf_file_name}", file_url]
                subprocess.run(command_to_exec, check=True)
                downloaded_pdf_path = f"{pdf_download_directory}/{pdf_file_name}"
                await upload_queue.put((event, downloaded_pdf_path, pdf_file_name, None, None, progress_update.id))
            else:
                video_file_extension = '.mp4'
                downloaded_video_path = f"{video_download_directory}/{file_name}{video_file_extension}"
                command_to_exec = ["yt-dlp", "--geo-bypass-country", "US", "--retries", "25", "--fragment-retries", "25", "--force-overwrites", "--no-keep-video", "-i", "--external-downloader", "axel", "--external-downloader-args", "axel:-n 5 -a", "--add-metadata", "-o", downloaded_video_path, file_url]
                subprocess.run(command_to_exec, check=True)
                thumb_image_path = f"{thumbnail_download_directory}/{file_name}.jpg"
                thumb_cmd = f'ffmpeg -hide_banner -loglevel quiet -i {downloaded_video_path} -ss 00:00:01 -vframes 1 -update 1 {thumb_image_path}'
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
                await upload_queue.put((event, downloaded_video_path, file_name, thumb_image_path, attributes, progress_update.id))
        except Exception as e:
            await event.respond(f"Failed to download {file_name}. Error: {str(e)}")

async def upload_file():
    while True:
        event, file_path, file_name, thumb_image_path, attributes, progress_message_id = await upload_queue.get()
        try:
            file = open(file_path, 'rb')
            input_file = await parallel_upload_file(telethon_client, file, file_name)
            if thumb_image_path and attributes:
                await telethon_client.send_file(event.chat_id, file=input_file, thumb=thumb_image_path, attributes=attributes, caption=file_name)
                os.remove(thumb_image_path)
            else:
                await telethon_client.send_file(event.chat_id, file=input_file, caption=file_name)
            file.close()
            os.remove(file_path)
            await telethon_client.delete_messages(event.chat_id, [progress_message_id])
        except Exception as e:
            await event.respond(f"Failed to upload {file_name}. Error: {str(e)}")
        upload_queue.task_done()

@telethon_client.on(events.NewMessage(incoming=True, pattern=None))
async def handle_docs(event):
    if event.document:
        progress_message = await event.respond("Preparing to download...")
        file_path = await event.download_media(file=download_directory)
        with open(file_path, 'r') as file:
            lines = file.readlines()
        download_tasks = [download_file(event, line.strip().split(':', 1)[0], line.strip().split(':', 1)[1], progress_message) for line in lines]
        upload_task = asyncio.create_task(upload_file())
        await asyncio.gather(*download_tasks)
        await upload_queue.join()
        upload_task.cancel()
        os.remove(file_path)
        await telethon_client.delete_messages(event.chat_id, [progress_message.id])

print("SUCESSFULLY DEPLOYED")
telethon_client.run_until_disconnected()
    
