import os, subprocess
from telethon import TelegramClient, events
from dotenv import load_dotenv
import cv2
from telethon.tl.types import DocumentAttributeVideo

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
                    pdf_file_name = f"{file_name}.pdf"
                    command_to_exec = ["yt-dlp", "-o", f"{pdf_download_directory}/{pdf_file_name}", file_url]
                    subprocess.run(command_to_exec, check=True)
                    downloaded_pdf_path = f"{pdf_download_directory}/{pdf_file_name}"
                    await progress_message.edit(f"Uploading {pdf_file_name}...")
                    await telethon_client.send_file(event.chat_id, file=downloaded_pdf_path, caption=pdf_file_name)
                else:
                    video_file_extension = '.mp4'
                    downloaded_video_path = f"{video_download_directory}/{file_name}{video_file_extension}"
                    command_to_exec = ["yt-dlp", "--geo-bypass-country", "US", "--retries", "25", "--fragment-retries", "25", "--force-overwrites", "--no-keep-video", "-i", "--external-downloader", "axel", "--external-downloader-args", "axel:-n 5 -a", "--add-metadata", "--postprocessor-args", "-c:v libx265 -preset ultrafast -x265-params crf=22:tag=hvc1, -acodec copy, -map 0", "-o", downloaded_video_path, file_url]
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
                    await progress_message.edit(f"Uploading {file_name}...")
                    await telethon_client.send_file(event.chat_id, file=downloaded_video_path, thumb=thumb_image_path, attributes=attributes, caption=file_name)
            except Exception as e:
                await event.respond(f"Failed to download {file_name}. Error: {str(e)}")
                continue
        os.remove(file_path)
        if os.path.exists(downloaded_pdf_path):
            os.remove(downloaded_pdf_path)
        if os.path.exists(downloaded_video_path):
            os.remove(downloaded_video_path)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
            
print("Bot successfully deployed.")
            
telethon_client.run_until_disconnected()


        
