import requests
from bs4 import BeautifulSoup
import os
import hashlib
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Replace with your actual Telegram bot token
TELEGRAM_TOKEN = '6996568724:AAFrjf88-0uUXJumDiuV6CbVuXCJvT-4KbY'

def get_video_link(dirpy_url):
    response = requests.get(dirpy_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        video_tag = soup.find('video')
        if video_tag and video_tag.source:
            return video_tag.source['src']
        
        # Fallback: Look for any <a> tags that might contain the video link
        for link in soup.find_all('a', href=True):
            if 'video' in link['href']:
                return link['href']
    
    return None

def download_video(video_link):
    response = requests.get(video_link, stream=True)
    if response.status_code == 200:
        # Create a hash of the video link for the filename
        filename_hash = hashlib.md5(video_link.encode()).hexdigest()
        filename = f"{filename_hash}.mp4"  # Use .mp4 as the file extension

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return filename
    return None

async def upload_to_telegram(bot, chat_id, video_path):
    await bot.send_video(chat_id=chat_id, video=open(video_path, 'rb'))
    os.remove(video_path)  # Clean up after upload

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a video link from Instagram or other platforms!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    user_url = update.message.text

    # Construct the Dirpy URL
    dirpy_url = f"https://dirpy.com/studio?url={user_url}"

    await update.message.reply_text("Processing...")

    video_link = get_video_link(dirpy_url)
    if video_link:
        video_path = download_video(video_link)
        if video_path:
            await upload_to_telegram(context.bot, user_id, video_path)
            await update.message.reply_text("Video uploaded successfully!")
        else:
            await update.message.reply_text("Failed to download the video.")
    else:
        await update.message.reply_text("Failed to retrieve video link.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
