import os
import subprocess
import re
import json
from moviepy.editor import VideoFileClip
import pyfiglet
from pyrogram import Client, filters
from dotenv import load_dotenv

load_dotenv()

download_directory = "./downloads"
if not os.path.exists(download_directory):
    os.makedirs(download_directory)

bot = Client(
    "BULK-UPLOAD-BOT",
    bot_token=os.getenv("BOT_TOKEN"),
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH")
)

@bot.on_message(filters.command("start") & filters.private)
async def start(client, update):
    await update.reply_text("Please send the .txt file with the video and PDF URLs.")

@bot.on_message(filters.document & filters.private)
async def handle_docs(client, update):
    if update.document.mime_type == "text/plain":
        # Save the document
        file_path = await update.download()
        # Read the file and extract URLs
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                file_name, file_url = line.strip().split(':', 1)
                command_to_exec = [
                    "yt-dlp",
                    "--geo-bypass-country", "US",
                    "--socket-timeout", "15",
                    "--retries",
                    "25",
                    "--fragment-retries",
                    "25",
                    "--force-overwrites",
                    "-k",
                    "-i",
                    "--recode-video", "mkv",
                    "--external-downloader", "aria2c",
                    "--external-downloader-args", "aria2c:-x 4 -s 16 -k 1M",
                    "--add-metadata",
                    "-o", f"{download_directory}/{file_name}.%(ext)s",
                    file_url
                ]
                subprocess.run(command_to_exec, check=True)
               # downloaded_file_path = f"{download_directory}/{file_name}"
                downloaded_file_path = f"{download_directory}/{file_name}.mkv"
                
                # Check the file extension
                if downloaded_file_path.endswith('.pdf'):
                    # Send the PDF
                    await client.send_document(
                        chat_id=update.chat.id,
                        document=downloaded_file_path,
                        caption=file_name
                    )
                else:
                    # Assume the file is a video and process accordingly
                    # Generate thumbnail
                    thumbnail_path = f"{download_directory}/{file_name}.jpg"
                    
                    subprocess.run([
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel", "quiet",
                        "-ss", "00:00:01",
                        "-i", downloaded_file_path,
                        "-vframes", "1",
                        "-q:v", "2",
                        "-vf", "scale=320:320:force_original_aspect_ratio=decrease",
                        thumbnail_path
                    ], check=True)
                    '''
                    thumb_cmd = f'ffmpeg -hide_banner -loglevel quiet -i {downloaded_file_path} -ss 00:00:02 -vframes 1 -update 1 {thumbnail_path}'
                    os.system(thumb_cmd)
                    '''
                    clip = VideoFileClip(downloaded_file_path)
                    duration = clip.duration
                    width = clip.size[0]
                    height = clip.size[1]
                    
                    # Send the video
                    await client.send_video(
                        chat_id=update.chat.id,
                        video=downloaded_file_path,
                        thumb=thumbnail_path,
                        caption=file_name,
                        width=width,
                        height=height,
                        duration=duration
                    )
        # Delete the temporary file
        os.remove(file_path)
    else:
        await update.reply_text("Please send a valid .txt file.")
        
# Print a custom figlet text
custom_fig = pyfiglet.Figlet(font='small')
print('\033[36m' + custom_fig.renderText('Bot deployed') + '\033[0m')
    
bot.run()
                        
