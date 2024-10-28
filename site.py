import os
import json
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Replace with your actual bot token and channel usernames
TELEGRAM_BOT_TOKEN = '6996568724:AAFrjf88-0uUXJumDiuV6CbVuXCJvT-4KbY'
API_ID = 12834603
API_HASH = '84a5daf7ac334a70b3fbd180616a76c6'
CHANNEL_USERNAME = '@itsteachteam'
USER_DETAILS_CHANNEL = '@userdatass'
ADMIN_USER_IDS = [6744775967]
USER_DATA_FILE = "user_details.json"

try:
    with open(USER_DATA_FILE, "r") as file:
        user_details = json.load(file)
except FileNotFoundError:
    user_details = []

def save_user_details():
    with open(USER_DATA_FILE, "w") as file:
        json.dump(user_details, file, indent=4)

app = Client("my_bot", bot_token=TELEGRAM_BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_name = message.from_user.username

    if not any(user['id'] == user_id for user in user_details):
        user_info = {
            "id": user_id,
            "name": user_first_name,
            "username": user_name
        }
        user_details.append(user_info)
        save_user_details()

        await client.send_message(USER_DETAILS_CHANNEL, 
                                   f"New user started the bot:\nName: {user_first_name}\nUsername: {user_name}\nUser ID: {user_id}")

    welcome_message = (
        f"Hello {user_first_name}!\n\n"
        "I am a simple bot to download videos, reels, and photos from Instagram links.\n\n"
        "This bot is the fastest bot you have ever seen in Telegram.\n\n"
        "Just send me your link.\n\n"
        "Developer: @xdshivay ❤"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Channel", url="https://t.me/Itsteachteam"),
            InlineKeyboardButton("Group", url="https://t.me/Itsteachteamsupport")
        ], 
        [
            InlineKeyboardButton("Developer", url="https://t.me/XDSHlVAY")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(welcome_message, reply_markup=reply_markup)

@app.on_message(filters.command("info"))
async def info(client, message):
    user_id = message.from_user.id
    if user_id not in ADMIN_USER_IDS:
        await message.reply_text("You are not authorized to use this command.")
        return

    total_users = len(user_details)
    await message.reply_text(f"Total users in the bot: {total_users}")

async def check_channel_membership(user_id):
    try:
        chat_member = await app.get_chat_member(CHANNEL_USERNAME, user_id)
        print(f"User ID: {user_id}, Status: {chat_member.status}")  # Debug line
        return chat_member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking membership for user {user_id}: {e}")  # Debug line
        return False

async def download_and_send_video(video_url, chat_id, user_id):
    if not await check_channel_membership(user_id):
        keyboard = [
            [InlineKeyboardButton("Join Channel", url="https://t.me/Itsteachteam")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await app.send_message(chat_id, 
                               "Before sending the link, please join our channel first.\n\nAfter joining, send the link again.",
                               reply_markup=reply_markup)
        return

    downloading_message = await app.send_message(chat_id, "Processing your request... Please wait.")

    api_url = f'https://tele-social.vercel.app/down?url={video_url}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers) as response:
                response.raise_for_status()
                content = await response.json()

        video_link = content['data'].get('video')
        title = content['data'].get('title', "Video")

        if not video_link or not video_link.startswith("http"):
            await app.send_message(chat_id, "Received an invalid video link.")
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(video_link) as response:
                response.raise_for_status()
                video_data = await response.read()

        await app.send_video(chat_id, video_data, caption=title)

    except aiohttp.ClientError as e:
        await app.send_message(chat_id, "Network error occurred. Please try again later.")
        print(f"Network error: {e}")
    except Exception as e:
        await app.send_message(chat_id, "Failed to download video. Please try again later.")
        print(f"Error: {e}")
    finally:
        await app.delete_messages(chat_id, downloading_message.message_id)

@app.on_message(filters.text & ~filters.command(['start', 'info', 'broadcast']))
async def handle_message(client, message):
    video_link = message.text
    await download_and_send_video(video_link, message.chat.id, message.from_user.id)

@app.on_message(filters.command("broadcast"))
async def broadcast(client, message):
    if message.from_user.id not in ADMIN_USER_IDS:
        await message.reply_text("You are not authorized to use this command.")
        return

    if not message.reply_to_message:
        await message.reply_text("Please reply to a message to broadcast it.")
        return

    message_to_forward = message.reply_to_message
    successful = 0
    failed = 0

    for user in user_details:
        user_id = user['id']
        try:
            await client.forward_messages(user_id, message_to_forward.chat.id, message_to_forward.message_id)
            successful += 1
        except Exception as e:
            print(f"Failed to forward message to {user_id}: {e}")
            failed += 1

    await message.reply_text(f"Broadcast complete:\n\nSuccessfully sent: {successful}\nFailed: {failed}\nTotal users: {len(user_details)}")

if __name__ == '__main__':
    app.run()
