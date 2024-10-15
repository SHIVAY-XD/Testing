import requests
from bs4 import BeautifulSoup

# The URL of the page containing the video
url = 'https://dirpy.com/studio?url=https://xhamster.com/videos/stepmom-make-video-for-instagram-and-her-stepson-helps-her-xhey0CY&affid=tubeoffline&utm_source=tubeoffline&utm_medium=download'

# Send a request to fetch the page content
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Find the video link
# You may need to adjust this based on the actual HTML structure
video_tag = soup.find('source')  # Example: looking for a <source> tag in <video>

if video_tag and 'src' in video_tag.attrs:
    video_url = video_tag['src']
    print("Video URL:", video_url)
else:
    print("Video link not found.")
