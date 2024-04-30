import os
import subprocess
import cv2
from moviepy.editor import VideoFileClip
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
    progress_message = await update.reply_text("Downloading...")
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
                    "--recode-video", "mkv",
                    "--external-downloader", "aria2c",
                    "--external-downloader-args", "aria2c:-x 4 -s 8 -k 1M",
                    "--add-metadata",
                    "-o", f"{download_directory}/{file_name}.%(ext)s",
                    file_url
                ]
                subprocess.run(command_to_exec, check=True)
                downloaded_file_path = f"{download_directory}/{file_name}.mkv"
                await progress_message.edit_text("Uploading...")
                
                # Generate thumbnail
                thumbnail_path = f"{download_directory}/{file_name}.jpg"
                try:
                    # Try extracting thumbnail with moviepy
                    clip = VideoFileClip(downloaded_file_path)
                    clip.save_frame(thumbnail_path, t=1)  # t is the time in seconds
                    width, height = clip.size
                    duration = int(clip.duration)
                    clip.close()
                except Exception as e:
                    # Fallback to cv2 if moviepy fails
                    video_capture = cv2.VideoCapture(downloaded_file_path)
                    success, image = video_capture.read()
                    if success:
                        cv2.imwrite(thumbnail_path, image)  # Save the first frame as thumbnail
                        width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        duration = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT) / video_capture.get(cv2.CAP_PROP_FPS))
                    video_capture.release()
                    
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
        # Delete the temporary files
        await progress_message.delete()
        os.remove(file_path)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        if os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)
    else:
        await update.reply_text("Please send a valid .txt file.")
        
# Print a custom figlet text
custom_fig = pyfiglet.Figlet(font='small')
print('\033[36m' + custom_fig.renderText('Bot deployed') + '\033[0m')

bot.run()
                
