import os, subprocess, glob
from moviepy.editor import VideoFileClip
from telethon import TelegramClient, events
from dotenv import load_dotenv
import pyfiglet

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
                    command_to_exec = ["yt-dlp", "--geo-bypass-country", "US", "--retries", "25", "--fragment-retries", "25", "--force-overwrites", "--no-keep-video", "-i", "--external-downloader", "axel", "--external-downloader-args", "-n 5 -a -k 1M -s 16", "--add-metadata", "-o", f"{video_download_directory}/{file_name}", file_url]
                    subprocess.run(command_to_exec, check=True)
                    video_file_pattern = f"{video_download_directory}/{file_name}.*"
                    video_file_list = glob.glob(video_file_pattern)
                    if video_file_list:
                        downloaded_video_path = video_file_list[0]
                        thumbnail_path = f"{thumbnail_download_directory}/{file_name}.jpg"
                        clip = VideoFileClip(downloaded_video_path)
                        clip.save_frame(thumbnail_path, t=1)
                        clip.close()
                        await progress_message.edit(f"Uploading {file_name}...")
                        await telethon_client.send_file(event.chat_id, file=downloaded_video_path, caption=file_name)
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

custom_fig = pyfiglet.Figlet(font='small')
print(custom_fig.renderText('Bot deployed'))
telethon_client.run_until_disconnected()
                    
