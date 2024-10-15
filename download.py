import requests

# Video URL
video_url = 'https://video-b.xhcdn.com/key=2E4U-yaP3upBjGkcHlVMPQ,end=1729036800,limit=3/data=51.81.159.22-dvp/speed=0/024/289/611/1080p.h264.mp4'

# Send a request to download the video
response = requests.get(video_url, stream=True)

# Specify the output file name
output_file = 'downloaded_video.mp4'

# Write the content to a file
with open(output_file, 'wb') as file:
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:  # filter out keep-alive chunks
            file.write(chunk)

print(f"Video downloaded successfully: {output_file}")
