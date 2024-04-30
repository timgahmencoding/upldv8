import os
import subprocess
import re
import json
from pyrogram import Client, filters
from dotenv import load_dotenv

load_dotenv()

download_directory = "./downloads"  # Define the download directory
if not os.path.exists(download_directory):
    os.makedirs(download_directory)

HB = Client(
    "YOUTUBE Bot",
    bot_token=os.getenv("BOT_TOKEN"),
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH")
)

@HB.on_message(filters.command("start") & filters.private)
async def start(client, update):
    urls_text = re.findall(r'\[(.*?)\]', update.text)
    for line in urls_text:
        file_name, file_url = line.split(':')
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
            "--progress",
            "-i",
            "--convert-thumbnails", "jpg",
            "--embed-chapters",
            "--convert-subs", "srt",
            "--audio-quality", "0",
           # "--remux-video", "webm>mp4/mkv>mkv/mp4",
            "--recode-video", "mkv",
            "--external-downloader", "aria2c",
            "--external-downloader-args", "aria2c:-x 4 -s 8 -k 1M",
            "--add-metadata",
            "--all-subs",
            "--embed-thumbnail",
            "-o", f"{download_directory}/{file_name}.%(ext)s",
            file_url
        ]
        subprocess.run(command_to_exec, check=True)
        file_path = f"{download_directory}/{file_name}.mp4"
        
        # Generate thumbnail
        thumbnail_path = f"{download_directory}/{file_name}.jpg"
        subprocess.run([
            "ffmpeg",
            "-hide-banner",
            "-log-level", "quiet",
            "-ss", "00:00:01",
            "-i", file_path,
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
            file_path
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
            video=file_path,
            thumb=thumbnail_path,
            caption=file_name,
            width=width,
            height=height,
            duration=duration
        )

HB.run()
      
