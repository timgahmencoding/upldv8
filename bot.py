                import os
import subprocess
import cv2
from moviepy.editor import VideoFileClip
from pyrogram import Client, filters
from dotenv import load_dotenv
import pyfiglet

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
                # Determine if the URL is for a video or a PDF
                if file_url.endswith('.pdf'):
                    # Use yt-dlp to download PDF files
                    command_to_exec = [
                        "yt-dlp",
                        "-o", f"{download_directory}/{file_name}",
                        file_url
                    ]
                else:
                    # Use yt-dlp with additional flags for videos
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
                # Execute the download command
                subprocess.run(command_to_exec, check=True)
                downloaded_file_path = f"{download_directory}/{file_name}"

                await progress_message.edit_text("Uploading...")
                # Send the file
                await client.send_document(
                    chat_id=update.chat.id,
                    document=downloaded_file_path,
                    caption=file_name
                )
                # Delete the file after uploading
                os.remove(downloaded_file_path)

        # Delete the temporary files
        await progress_message.delete()
        os.remove(file_path)
    else:
        await update.reply_text("Please send a valid .txt file.")

# Print a custom figlet text
custom_fig = pyfiglet.Figlet(font='small')
print('\033[36m' + custom_fig.renderText('Bot deployed') + '\033[0m')

bot.run()
                
