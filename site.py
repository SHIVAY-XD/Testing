import requests
from bs4 import BeautifulSoup

url = 'https://fetchfile.me/en/download-xhamster/?url=https://xhamster.com/videos/stepmom-make-video-for-instagram-and-her-stepson-helps-her-xhey0CY'  # Replace with the actual page URL
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Adjust the selector to find the download link
download_link = soup.find('a', text='Download')  # Modify based on actual text or attributes

if download_link:
    video_url = download_link['href']
    print("Download link:", video_url)
else:
    print("Download link not found.")
