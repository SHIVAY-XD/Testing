import requests
from bs4 import BeautifulSoup
import os
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
            InlineKeyboardButton("Channel", url=f'https://t.me/your_channel_username'),
            InlineKeyboardButton("Group", url=f'https://t.me/your_group_username')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Hello {update.message.from_user.first_name}!\n\n"
        "I am a simple bot to download videos, reels, and photos from supported platforms.\n\n"
        "Just send me your link."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_downloads
    user_id = update.message.chat.id
    user_url = update.message.text

    if not await is_user_member(update, context):
        await update.message.reply_text(f"Please join our channel {CHANNEL_USERNAME} to use this bot.")
        return

    if not is_supported_platform(user_url):
        await update.message.reply_text("Unsupported platform. Please provide a link from supported platforms.")
        return

    processing_message = await update.message.reply_text("Processing...")
    video_link = get_video_link(user_url)

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

def get_video_link(url):
    # Example implementation: Modify this according to the actual website you are scraping.
    # This is a placeholder for extracting the video link from the given URL.
    # Here, you would implement your scraping logic.
    return "http://example.com/video.mp4"  # Replace with actual video URL extraction logic

def download_video(video_url):
    try:
        response = requests.get(video_url, stream=True)
        filename = video_url.split("/")[-1]  # Use the last part of the URL as filename
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return filename
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        return None

def get_file_size(file_path):
    return os.path.getsize(file_path) / (1024 * 1024)  # Convert bytes to MB

def compress_video(video_path):
    # Placeholder for video compression logic
    # This should return the path of the compressed video
    return video_path  # Replace with actual compression logic

async def upload_to_telegram(bot, user_id, video_path):
    try:
        with open(video_path, 'rb') as video_file:
            await bot.send_video(chat_id=user_id, video=video_file)
    except Exception as e:
        logger.error(f"Error uploading video to Telegram: {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = len(users)
    await update.message.reply_text(f"Total Users: {total_users}\nTotal Downloads: {total_downloads}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if update.message.reply_to_message:
        message_to_forward = update.message.reply_to_message
        user_ids = users
        successful = 0
        failed = 0

        for user_id in user_ids:
            try:
                await context.bot.forward_message(chat_id=user_id, from_chat_id=message_to_forward.chat.id, message_id=message_to_forward.message_id)
                successful += 1
            except Exception as e:
                logger.error(f"Failed to forward message to {user_id}: {e}")
                failed += 1

        total_users = len(user_ids)
        await update.message.reply_text(f"Broadcast complete:\n\nSuccessfully sent: {successful}\nFailed: {failed}\nTotal users: {total_users}")
    else:
        await update.message.reply_text("Please reply to a message to broadcast it.")

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
