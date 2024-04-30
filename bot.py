import os
import subprocess
import re
import json
import pyfiglet
from pyrogram import Client, filters
from dotenv import load_dotenv

load_dotenv()

download_directory = "./downloads"
if not os.path.exists(download_directory):
    os.makedirs(download_directory)

bot = Client(
    "BULK-UPLOAD-Bot",
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
                    "--no-keep-video",
                    "-i",
                    "--convert-thumbnails", "jpg",
                    "--audio-quality", "0",
                    #"--remux-video", "webm>mp4/mkv>mkv/mp4",
                    "--recode-video", "mkv",
                    "--external-downloader", "aria2c",
                    "--external-downloader-args", "aria2c:-x 4 -s 16 -k 1M",
                    "--add-metadata",
                    "--all-subs",
                    "--embed-thumbnail",
                    "-o", f"{download_directory}/{file_name}.%(ext)s",
                    file_url
                ]
                subprocess.run(command_to_exec, check=True)
                downloaded_file_path = f"{download_directory}/{file_name}"
                
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
                        "-hide-banner",
                        "-log-level", "quiet",
                        "-ss", "00:00:01",
                        "-i", downloaded_file_path,
                        "-vframes", "1",
                        "-q:v", "2",
                        "-vf", "scale=320:320:force_original_aspect_ratio=decrease",
                        thumbnail_path
                    ], check=True)
                    
                    # Get video information
                    result = subprocess.run([
                        "ffprobe",
                        "-hide-banner",
                        "-log-level", "quiet",
                        "-v", "quiet",
                        "-print_format", "json",
                        "-show_format",
                        "-show_streams",
                        downloaded_file_path
                    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    video_info = json.loads(result.stdout)
                    
                    # Extract video dimensions and duration
                    video_stream = next((stream for stream in video_info['streams'] if stream['codec_type'] == 'video'), None)
                    width = int(video_stream['width']) if video_stream else 0
                    height = int(video_stream['height']) if video_stream else 0
                    duration = float(video_stream['duration']) if video_stream else 0
                    
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
                        
