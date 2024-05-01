import os
import subprocess
from moviepy.editor import VideoFileClip
from telethon import TelegramClient, events, sync
from telethon.tl.types import DocumentAttributeVideo
from dotenv import load_dotenv
import pyfiglet
from ethon.telefunc import fast_upload

load_dotenv()

download_directory = "./downloads"
if not os.path.exists(download_directory):
    os.makedirs(download_directory)

# Initialize the Telethon client
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
        # Read the file and extract URLs
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                file_name, file_url = line.strip().split(':', 1)
                try:
                    # Update the progress message with the file name
                    await progress_message.edit(f"Downloading {file_name}...")

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
                            "--external-downloader", "wget",
                          #  "--external-downloader-args", "aria2c:-x 4 -s 8 -k 1M",
                            "--add-metadata",
                            "-o", f"{download_directory}/{file_name}.%(ext)s",
                            file_url
                        ]
                    subprocess.run(command_to_exec, check=True)
                    downloaded_file_path = f"{download_directory}/{file_name}"

                    # Update the progress message with the file name for uploading
                    await progress_message.edit(f"Uploading {file_name}...")

                    # Use fast_upload to upload the file
                    if downloaded_file_path.endswith('.pdf'):
                        # Send the PDF with fast_upload
                        await fast_upload(telethon_client, downloaded_file_path, event.chat_id, file_name=file_name)
                    else:
                        # Generate thumbnail and get video information using moviepy
                        thumbnail_path = f"{download_directory}/{file_name}.jpg"
                        clip = VideoFileClip(downloaded_file_path + '.mp4')
                        clip.save_frame(thumbnail_path, t=1)  # t is the time in seconds
                        width, height = clip.size
                        duration = int(clip.duration)
                        clip.close()
                        
                        uploader = await fast_upload(telethon_client, downloaded_file_path, event.chat_id)
                        await Client.send_file(event.chat_id, uploader, caption=file_name, thumb=thumbnail_path, attributes=[
                            DocumentAttributeVideo(
                                duration=duration,
                                w=width,
                                h=height,
                                supports_streaming=True
                            )
                        ])
    
                except subprocess.CalledProcessError as e:
                    # If a download fails, skip the file and continue with the next one
                    await event.respond(f"Failed to download {file_name}. Skipping to the next file.")

        # Delete the temporary files
        os.remove(file_path)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        if os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)

# Print a custom figlet text
custom_fig = pyfiglet.Figlet(font='small')
print(custom_fig.renderText('Bot deployed'))

telethon_client.run_until_disconnected()
