import requests
from bs4 import BeautifulSoup
import os
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Replace with your own values
TELEGRAM_TOKEN = '6996568724:AAFrjf88-0uUXJumDiuV6CbVuXCJvT-4KbY'

def get_video_link(dirpy_url):
    response = requests.get(dirpy_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        video_tag = soup.find('video')  # Adjust this based on the actual HTML structure
        if video_tag and video_tag.source:
            return video_tag.source['src']
    return None

def download_video(video_link):
    response = requests.get(video_link, stream=True)
    if response.status_code == 200:
        filename = video_link.split("/")[-1]
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return filename
    return None

def upload_to_telegram(bot: Bot, chat_id: int, video_path: str):
    with open(video_path, 'rb') as video:
        bot.send_video(chat_id=chat_id, video=video)
    os.remove(video_path)  # Clean up after upload

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Send me a Dirpy video link!")

def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    dirpy_url = update.message.text

    update.message.reply_text("Processing...")

    video_link = get_video_link(dirpy_url)
    if video_link:
        video_path = download_video(video_link)
        if video_path:
            upload_to_telegram(context.bot, user_id, video_path)
            update.message.reply_text("Video uploaded successfully!")
        else:
            update.message.reply_text("Failed to download the video.")
    else:
        update.message.reply_text("Failed to retrieve video link.")

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
