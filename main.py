import json
import os
import hashlib
import subprocess
import aiohttp
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Replace with your actual Telegram bot token and channel username
TELEGRAM_TOKEN = '7744770326:AAE9OtBsE0QyzPURjV4bt6gU4H6CBn9mvFc'  # Replace with your bot token
CHANNEL_USERNAME = '@itsteachteam'  # Replace with your channel username
MAX_SIZE_MB = 100  # Set your maximum size limit in MB
ADMIN_ID = 6744775967  # Replace with your actual Telegram user ID
USER_DATA_FILE = 'user_data.json'

ALLOWED_PLATFORMS = [
    'instagram.com',
    'facebook.com',
    'youtube.com',
    'twitter.com', 
    'x.com', 
    'youtu.be'
]

# Load user IDs from the JSON file
def load_user_ids():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return []

# Save user IDs to the JSON file
def save_user_ids(user_ids):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(user_ids, f)

# Initialize user list from file
users = load_user_ids()
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
    user_id = update.message.chat.id
    if user_id not in users:
        users.append(user_id)
        save_user_ids(users)  # Save updated user list

    keyboard = [
        [
            InlineKeyboardButton("Channel", url=f'https://t.me/itsteachteam'),
            InlineKeyboardButton("Group", url=f'https://t.me/itsteachteamsupport')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Hello {update.message.from_user.first_name} 👋!\n\n"
        "<b>I am a simple bot to download videos, reels, and photos from Instagram links.</b>\n\n"
        "<i>This bot is the fastest bot you have ever seen in Telegram.</i>\n\n"
        "<b>‣ Just send me your link🔗.</b>\n\n"
        "<b>Developer: @xdshivay</b> ❤", 
        reply_markup=reply_markup, parse_mode='HTML'
    )

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

    video_link = await get_video_link(dirpy_url)
    if video_link:
        video_path = await download_video(video_link)
        if video_path:
            if get_file_size(video_path) > MAX_SIZE_MB:
                video_path = compress_video(video_path)
            await upload_to_telegram(context.bot, user_id, video_path)
            total_downloads += 1  # Increment download count
            await processing_message.delete()
        else:
            await processing_message.delete()
            await update.message.reply_text("Failed to download the video.")
    else:
        await processing_message.delete()
        await update.message.reply_text("Failed to retrieve video link.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if update.message.reply_to_message:
        message_to_forward = update.message.reply_to_message
        
        successful = 0
        failed = 0
        
        for user_id in users:
            try:
                await context.bot.forward_message(chat_id=user_id, from_chat_id=message_to_forward.chat.id, message_id=message_to_forward.message_id)
                successful += 1
            except Exception as e:
                print(f"Failed to forward message to {user_id}: {e}")
                failed += 1
        
        total_users = len(users)
        await update.message.reply_text(f"Broadcast complete: \n\nSuccessfully: {successful}\nFailed: {failed}\nTotal users: {total_users}")
    else:
        await update.message.reply_text("Please reply to a message to broadcast it.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_users = len(users)
    await update.message.reply_text(f"Total Users: {total_users}\nTotal Downloads: {total_downloads}")

async def get_video_link(dirpy_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(dirpy_url) as response:
            if response.status == 200:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                video_tag = soup.find('video')
                if video_tag and video_tag.source:
                    return video_tag.source['src']
                
                for link in soup.find_all('a', href=True):
                    if 'video' in link['href']:
                        return link['href']
    return None

async def download_video(video_link):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_link) as response:
                if response.status == 200:
                    filename_hash = hashlib.md5(video_link.encode()).hexdigest()
                    filename = f"{filename_hash}.mp4"
                    with open(filename, 'wb') as f:
                        while True:
                            chunk = await response.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
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

            buttons = [
                [
                    InlineKeyboardButton("Channel", url=f'https://t.me/itsteachteam'),
                    InlineKeyboardButton("Bot", url=f'https://t.me/{bot.username}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message.message_id, reply_markup=reply_markup)

        os.remove(video_path)  # Delete video from server after sending
    except Exception as e:
        print(f"Error during video upload: {e}")
        await bot.send_message(chat_id=chat_id, text="Failed to upload the video.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
