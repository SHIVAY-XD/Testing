import requests
from bs4 import BeautifulSoup
import os
import hashlib
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Replace with your actual Telegram bot token
TELEGRAM_TOKEN = '6996568724:AAFrjf88-0uUXJumDiuV6CbVuXCJvT-4KbY'
MAX_SIZE_MB = 100  # Set your maximum size limit in MB

def get_video_link(dirpy_url):
    response = requests.get(dirpy_url)
    
    print(f"Fetching video link from: {dirpy_url}")
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        video_tag = soup.find('video')
        if video_tag and video_tag.source:
            print(f"Video URL found: {video_tag.source['src']}")
            return video_tag.source['src']
        
        for link in soup.find_all('a', href=True):
            if 'video' in link['href']:
                print(f"Fallback video URL found: {link['href']}")
                return link['href']
    
    print("No video URL found.")
    return None

def download_video(video_link):
    try:
        response = requests.get(video_link, stream=True)
        
        print(f"Attempting to download video from: {video_link}")
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            filename_hash = hashlib.md5(video_link.encode()).hexdigest()
            filename = f"{filename_hash}.mp4"

            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Check if the file was created
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                print(f"Downloaded video saved as: {filename}")
                return filename
            else:
                print("Error: Video file was not created.")
        else:
            print(f"Failed to download video: {response.text}")
    except Exception as e:
        print(f"An error occurred during the download: {e}")
    
    return None

def compress_video(input_path):
    output_path = f"compressed_{os.path.basename(input_path)}"
    command = [
        'ffmpeg', '-i', input_path, '-vcodec', 'libx264', '-crf', '28', 
        '-preset', 'fast', output_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_path

def get_file_size(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)  # Convert bytes to MB

async def upload_to_telegram(bot, chat_id, video_path):
    try:
        print(f"Uploading video: {video_path}")
        with open(video_path, 'rb') as video_file:
            message = await bot.send_video(chat_id=chat_id, video=video_file)

            buttons = [
                [
                    InlineKeyboardButton("Download Video", callback_data='download'),
                    InlineKeyboardButton("Visit Channel", url='https://t.me/YourChannel')  # Replace with your channel link
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message.message_id, reply_markup=reply_markup)

        os.remove(video_path)  # Delete video from server after sending
        print("Video uploaded and deleted from server.")
    except Exception as e:
        print(f"Error during video upload: {e}")
        await bot.send_message(chat_id=chat_id, text="Failed to upload the video.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a video link from Instagram or other platforms!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    user_url = update.message.text

    dirpy_url = f"https://dirpy.com/studio?url={user_url}"
    processing_message = await update.message.reply_text("Processing...")

    video_link = get_video_link(dirpy_url)
    if video_link:
        video_path = download_video(video_link)
        if video_path:
            if get_file_size(video_path) > MAX_SIZE_MB:
                video_path = compress_video(video_path)  # Compress the video if it's too large
            await upload_to_telegram(context.bot, user_id, video_path)
            await processing_message.delete()
            await update.message.reply_text("Video uploaded successfully!")
        else:
            await processing_message.delete()
            await update.message.reply_text("Failed to download the video.")
    else:
        await processing_message.delete()
        await update.message.reply_text("Failed to retrieve video link.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
