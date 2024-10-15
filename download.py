import requests
from bs4 import BeautifulSoup
from telegram import Bot

# Telegram Bot Token and Chat ID
TELEGRAM_TOKEN = '6996568724:AAFrjf88-0uUXJumDiuV6CbVuXCJvT-4KbY'
CHAT_ID = '-1002447378281'

# Function to fetch the video URL
def fetch_video_url(page_url):
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    video_tag = soup.find('source')  # Adjust this selector as needed

    if video_tag and 'src' in video_tag.attrs:
        return video_tag['src']
    return None

# Function to download the video
def download_video(video_url):
    response = requests.get(video_url, stream=True)
    file_name = 'downloaded_video.mp4'

    with open(file_name, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    return file_name

# Function to upload the video to Telegram
def upload_to_telegram(file_name):
    bot = Bot(token=TELEGRAM_TOKEN)
    with open(file_name, 'rb') as video:
        bot.send_video(chat_id=CHAT_ID, video=video)

# Main function
def main():
    input_url = input("Enter the page URL: ")
    
    video_url = fetch_video_url(input_url)
    if video_url:
        print(f"Video URL found: {video_url}")
        video_file = download_video(video_url)
        print("Video downloaded successfully.")
        upload_to_telegram(video_file)
        print("Video uploaded to Telegram successfully.")
    else:
        print("No video URL found.")

if __name__ == '__main__':
    main()
