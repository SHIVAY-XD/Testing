import os
import json
import aiohttp
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

TELEGRAM_BOT_TOKEN = '6996568724:AAFrjf88-0uUXJumDiuV6CbVuXCJvT-4KbY'
API_ID = 12834603
API_HASH = '84a5daf7ac334a70b3fbd180616a76c6'
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', '@itsteachteam')
USER_DATA_FILE = "user_details.json"

# Load user details
try:
    with open(USER_DATA_FILE, "r") as file:
        user_details = json.load(file)
except FileNotFoundError:
    user_details = []

def save_user_details():
    with open(USER_DATA_FILE, "w") as file:
        json.dump(user_details, file, indent=4)

app = Client("my_bot", bot_token=TELEGRAM_BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

async def check_channel_membership(user_id):
    try:
        async for member in app.get_chat_members(CHANNEL_USERNAME):
            if member.user.id == user_id:
                if member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.CREATOR, enums.ChatMemberStatus.MEMBER]:
                    return True
        return False
    except Exception as e:
        print(f"Error checking membership for user {user_id}: {e}")
        return False

async def download_and_send_video(video_url, chat_id, user_id):
    # Check if the user is a member of the channel
    if not await check_channel_membership(user_id):
        keyboard = [
            [InlineKeyboardButton("Join Channel", url="https://t.me/Itsteachteam")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await app.send_message(chat_id, 
                               "Before sending the link, please join our channel first.\n\nAfter joining, send the link again.",
                               reply_markup=reply_markup)
        return

    # User is a member; proceed with video download
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

if __name__ == '__main__':
    app.run()
