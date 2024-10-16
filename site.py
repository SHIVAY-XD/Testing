import requests
from bs4 import BeautifulSoup
import os
import hashlib
import subprocess
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = '7744770326:AAE9OtBsE0QyzPURjV4bt6gU4H6CBn9mvFc'  # Replace with your actual token
MAX_SIZE_MB = 100  # Set your maximum size limit in MB

def get_video_link(dirpy_url):
    response = requests.get(dirpy_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        video_tag = soup.find('video')
        
        if video_tag and video_tag.source:
            return video_tag.source['src']
        
        for link in soup.find_all('a', href=True):
            if 'video' in link['href']:
                return link['href']
    
    return None

async def download_video(video_link, chat_id, context):
    response = requests.get(video_link, stream=True)
    
    if response.status_code == 200:
        filename_hash = hashlib.md5(video_link.encode()).hexdigest()
        filename = f"{filename_hash}.mp4"
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded_size += len(chunk)
                percent = (downloaded_size / total_size) * 100
                await context.bot.send_message(chat_id=chat_id, text=f"Download Progress: {percent:.0f}%")

        if os.path.getsize(filename) > 0:
            return filename
    return None

async def compress_video(input_path, chat_id, context):
    output_path = f"compressed_{os.path.basename(input_path)}"
    
    command = [
        'ffmpeg', '-i', input_path, '-vcodec', 'libx264', '-crf', '30',
        '-preset', 'superfast', '-threads', '4', output_path
    ]
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    while True:
        output = process.stderr.readline()
        if output == b"" and process.poll() is not None:
            break
        if output:
            # Parse ffmpeg output for progress (this part may need to be customized)
            # Here we simulate progress reporting as a placeholder
            if b"frame=" in output:
                percent = 0  # Set your logic here to calculate percentage based on output
                await context.bot.send_message(chat_id=chat_id, text=f"Compression Progress: {percent:.0f}%")

    return output_path

async def upload_to_telegram(bot, chat_id, video_path):
    try:
        with open(video_path, 'rb') as video_file:
            message = await bot.send_video(chat_id=chat_id, video=video_file)

            buttons = [
                [
                    InlineKeyboardButton("Download Video", callback_data='download'),
                    InlineKeyboardButton("Visit Channel", url='https://t.me/YourChannel')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message.message_id, reply_markup=reply_markup)

        os.remove(video_path)  # Delete video from server after sending
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text="Failed to upload the video.")

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    user_url = update.message.text

    dirpy_url = f"https://dirpy.com/studio?url={user_url}"
    processing_message = await update.message.reply_text("Processing...")

    video_link = get_video_link(dirpy_url)
    if video_link:
        video_path = await download_video(video_link, user_id, context)
        if video_path:
            if get_file_size(video_path) > MAX_SIZE_MB:
                video_path = await compress_video(video_path, user_id, context)  # Compress the video if it's too large
            await upload_to_telegram(context.bot, user_id, video_path)
            await processing_message.delete()
            await update.message.reply_text("Video uploaded successfully!")
        else:
            await processing_message.delete()
            await update.message.reply_text("Failed to download the video.")
    else:
        await processing_message.delete()
        await update.message.reply_text("Failed to retrieve video link.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a video link from Instagram or other platforms!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    asyncio.create_task(process_video(update, context))  # Run the video processing in the background

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
