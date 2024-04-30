# BULK Download and Upload Telegram Bot

## Overview
This Telegram bot is designed to download videos from provided URLs using `yt-dlp` and then upload them directly to a Telegram chat. It responds to a `/start` command followed by a list of video names and URLs.

## Features
- **Download Videos**: Uses `yt-dlp` to download videos from URLs.
- **Generate Thumbnails**: Creates a thumbnail for each video using `cv2+moviepy`.
- **Retrieve Video Info**: Gathers video information using `cv2+moviepy`.
- **Upload to Telegram**: Sends the downloaded video to Telegram with the thumbnail and video details.

## Usage
To use the bot, send `/start` to check bot is live then send text file containing urls.


## Installation
To set up the bot, you need to have `yt-dlp`, `cv2+moviepy`, and `aria2c` installed on your system. Ensure that these tools are accessible from the environment where the bot is running.

## Configuration
Make sure to set the `download_directory` in the script to the path where you want the downloaded files to be saved.

## Running the Bot
Execute the script to run the bot. It will listen for commands and process them as they come.

## Dependencies
- Python 3.6 or higher
- Pyrogram
- `yt-dlp`
- `ffmpeg`
- `ffprobe`
- `cv2+moviepy`
- `aria2c`
## License
This project is licensed under the MIT License - see the LICENSE.md file for details.


