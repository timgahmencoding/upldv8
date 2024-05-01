# Bulk Upload Bot for Telegram

## Overview
The Bulk Upload Bot is an advanced Telegram bot designed to automate the process of uploading large numbers of PDFs and videos. It leverages the power of parallel file transfers to ensure super-fast uploads, making it an ideal solution for content creators, educators, and anyone in need of distributing large files efficiently.

## Features
- **Parallel File Transfers**: Utilizes a sophisticated script to upload files in parallel, significantly speeding up the process.
- **Video and PDF Support**: Seamlessly handles both video and PDF files, ensuring a wide range of content can be uploaded.
- **Automatic Thumbnail Generation**: Generates thumbnails for videos to provide a preview of the content.
- **Sanitized Filenames**: Cleans up filenames to ensure compatibility with various operating systems and Telegram's file handling.
- **Environment Variable Configuration**: Easy setup with `.env` file to manage API keys and tokens.
- **Asynchronous Operations**: Built with `asyncio` and `uvloop` for non-blocking I/O operations, ensuring the bot remains responsive.

## Setup
1. Clone the repository to your local machine.
2. Install the required dependencies using `pip install -r requirements.txt`.
3. Create a `.env` file with your Telegram `API_ID`, `API_HASH`, and `BOT_TOKEN`.
4. Run the bot using `python bot.py`.

## Usage
1. Start the bot with the `/start` command.
2. Send a `.txt` file with the URLs of the videos and PDFs you wish to upload, formatted as `filename:url`.
3. The bot will download and upload the files to the chat.

## Dependencies
- Telethon
- yt-dlp
- ffmpeg
- cv2 (OpenCV)
- dotenv

## Contributions
Contributions are welcome! Please fork the repository and submit a pull request with your proposed changes.

## License
Distributed under the MIT License. See `LICENSE` for more information.

## Contact
For support or queries, please open an issue in the GitHub repository.

---

Enjoy your experience with Bulk Upload Bot for Telegram!
