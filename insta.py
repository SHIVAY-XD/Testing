import requests
from bs4 import BeautifulSoup
import os
import hashlib
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Replace with your actual Telegram bot token and channel username
TELEGRAM_TOKEN = '7744770326:AAE9OtBsE0QyzPURjV4bt6gU4H6CBn9mvFc'
CHANNEL_USERNAME = '@itsteachteam'  # Replace with your channel username
MAX_SIZE_MB = 100  # Set your maximum size limit in MB

ALLOWED_PLATFORMS = [
    'instagram.com',
    'facebook.com',
    'youtube.com',
    'twitter.com'
]

user_ids = set()  # Set to store user IDs for broadcasting
total_downloads = 0  # Counter for total video downloads

async def is_user_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

def is_supported_platform(url):
    return any(platform in url for platform in ALLOWED_PLATFORMS)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    user_ids.add(update.message.chat.id)  # Add user ID to the set
    greeting_message = (
        f"Hello {user_name}👋!\n\n"
        "I am a simple bot to download videos, reels, and photos from Instagram links.\n"
        "This bot is the fastest bot you have ever seen in Telegram.\n\n"
        "‣ Just send me your link🔗.\n\n"
        "Developer: @xdshivay ❤"
    )
    
    # Create inline buttons
    keyboard = [
        [
            InlineKeyboardButton("Channel", url=f'https://t.me/itsteachteam'),
            InlineKeyboardButton("Group", url=f'https://t.me/itsteachteamsupport')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(greeting_message, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_downloads  # Use global variable to track downloads
    user_id = update.message.chat.id
    user_url = update.message.text

    if not await is_user_member(update, context):
        await update.message.reply_text(
            f"Please join our channel {CHANNEL_USERNAME} to use this bot."
        )
        return

    if not is_supported_platform(user_url):
        await update.message.reply_text("Unsupported platform. Please provide a link from Instagram, Facebook, YouTube, or Twitter.")
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
            total_downloads += 1  # Increment download count
            await processing_message.delete()
            await update.message.reply_text("Video uploaded successfully!")
        else:
            await processing_message.delete()
            await update.message.reply_text("Failed to download the video.")
    else:
        await processing_message.delete()
        await update.message.reply_text("Failed to retrieve video link.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == YOUR_ADMIN_USER_ID:  # Replace with your admin user ID
        successful_count = 0
        failed_count = 0

        if update.reply_to_message:
            message_id = update.reply_to_message.message_id
            for user_id in user_ids:
                try:
                    await context.bot.forward_message(chat_id=user_id, from_chat_id=update.message.chat.id, message_id=message_id)
                    successful_count += 1
                except Exception as e:
                    print(f"Failed to forward message to {user_id}: {e}")
                    failed_count += 1
            await update.message.reply_text(f"Broadcast forwarded!\nSuccessful: {successful_count}\nFailed: {failed_count}\nTotal Users: {len(user_ids)}")
        else:
            message = ' '.join(context.args)
            if not message:
                await update.message.reply_text("Please provide a message to broadcast or reply to a message.")
                return
            for user_id in user_ids:
                try:
                    await context.bot.send_message(chat_id=user_id, text=message)
                    successful_count += 1
                except Exception as e:
                    print(f"Failed to send message to {user_id}: {e}")
                    failed_count += 1
            await update.message.reply_text(f"Broadcast message sent!\nSuccessful: {successful_count}\nFailed: {failed_count}\nTotal Users: {len(user_ids)}")
    else:
        await update.message.reply_text("You do not have permission to use this command.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = len(user_ids)
    await update.message.reply_text(f"Total Users: {total_users}\nTotal Downloads: {total_downloads}")

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

def download_video(video_link):
    try:
        response = requests.get(video_link, stream=True)
        if response.status_code == 200:
            filename_hash = hashlib.md5(video_link.encode()).hexdigest()
            filename = f"{filename_hash}.mp4"
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return filename
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
        with open(video_path, 'rb') as video_file:
            message = await bot.send_video(chat_id=chat_id, video=video_file)
            await bot.send_message(chat_id=chat_id, text="Your video has been uploaded successfully!")
        os.remove(video_path)  # Delete video from server after sending
    except Exception as e:
        print(f"Error during video upload: {e}")
        await bot.send_message(chat_id=chat_id, text="Failed to upload the video.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))  # Command to check stats
    app.add_handler(CommandHandler("broadcast", broadcast))  # Combined broadcast command
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
