import requests
from bs4 import BeautifulSoup
import os
import hashlib
import subprocess
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging to capture only error messages
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Replace with your actual Telegram bot token and channel username
TELEGRAM_TOKEN = '6996568724:AAFrjf88-0uUXJumDiuV6CbVuXCJvT-4KbY'  # Replace with your bot token
CHANNEL_USERNAME = '@itsteachteam'  # Replace with your channel username
MAX_SIZE_MB = 100  # Set your maximum size limit in MB

ALLOWED_PLATFORMS = [
    'instagram.com',
    'facebook.com',
    'youtube.com',
    'twitter.com', 
    'x.com', 
    'youtu.be'   
]

users = []
total_downloads = 0
ADMIN_ID = 6744775967  # Replace with your actual Telegram user ID

async def is_user_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return False

def is_supported_platform(url):
    return any(platform in url for platform in ALLOWED_PLATFORMS)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    if user_id not in users:
        users.append(user_id)

    keyboard = [
        [
            InlineKeyboardButton("Channel", url=f'https://t.me/itsteachteam'),
            InlineKeyboardButton("Group", url=f'https://t.me/itsteachteamsupport')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Hello {update.message.from_user.first_name}!\n\n"
        "I am a simple bot to download videos, reels, and photos from Instagram links.\n\n"
        "Just send me your link."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_downloads
    user_id = update.message.chat.id
    user_url = update.message.text

    if not await is_user_member(update, context):
        await update.message.reply_text(
            f"Please join our channel {CHANNEL_USERNAME} to use this bot."
        )
        return

    if not is_supported_platform(user_url):
        await update.message.reply_text("Unsupported platform. Please provide a link from supported platforms.")
        return

    dirpy_url = f"https://dirpy.com/studio?url={user_url}"
    processing_message = await update.message.reply_text("Processing...")

    video_link = get_video_link(dirpy_url)
    if video_link:
        video_path = download_video(video_link)
        if video_path:
            if get_file_size(video_path) > MAX_SIZE_MB:
                video_path = compress_video(video_path)
            await upload_to_telegram(context.bot, user_id, video_path)
            total_downloads += 1
            await processing_message.delete()
        else:
            await processing_message.delete()
            await update.message.reply_text("Failed to download the video.")
    else:
        await processing_message.delete()
        await update.message.reply_text("Failed to retrieve video link.")

# Additional functions remain unchanged...

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.error("Bot started and polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
