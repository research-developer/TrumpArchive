"""
Test downloading a video and its transcript using yt-dlp.
"""

import os
import json
import subprocess
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get YouTube API key
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Initialize YouTube API
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Create data directory if it doesn't exist
DATA_DIR = "data"
AUDIO_DIR = f"{DATA_DIR}/audio"
METADATA_DIR = f"{DATA_DIR}/metadata"
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

def get_video_details(video_id):
    """Get video details from YouTube API."""
    try:
        # Get video details
        response = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        ).execute()
        
        if not response["items"]:
            print(f"No video found with ID: {video_id}")
            return None
        
        video = response["items"][0]
        snippet = video["snippet"]
        content_details = video["contentDetails"]
        statistics = video["statistics"]
        
        # Extract duration (format PT#M#S)
        duration = content_details["duration"]
        duration = duration.replace("PT", "")
        minutes = 0
        seconds = 0
        
        if "M" in duration:
            minutes_part = duration.split("M")[0]
            minutes = int(minutes_part)
            duration = duration.split("M")[1]
        
        if "S" in duration:
            seconds_part = duration.split("S")[0]
            seconds = int(seconds_part)
        
        total_seconds = minutes * 60 + seconds
        
        # Extract details
        details = {
            "video_id": video_id,
            "title": snippet["title"],
            "channel_title": snippet["channelTitle"],
            "publish_date": snippet["publishedAt"],
            "description": snippet["description"],
            "views": statistics.get("viewCount", 0),
            "likes": statistics.get("likeCount", 0),
            "duration_seconds": total_seconds,
            "tags": snippet.get("tags", [])
        }
        
        return details
    except Exception as e:
        print(f"Error getting video details: {e}")
        return None

def download_audio(video_id):
    """Download audio from a YouTube video using yt-dlp."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    output_file = f"{AUDIO_DIR}/{video_id}.mp3"
    
    try:
        print(f"Downloading audio for video: {video_id}")
        
        # Use yt-dlp to download audio
        command = [
            "yt-dlp",
            "-x",                      # Extract audio
            "--audio-format", "mp3",   # Convert to mp3
            "-o", output_file,         # Output file
            url                        # URL
        ]
        
        # Run command
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            print(f"Error downloading audio: {process.stderr}")
            return None
        
        print(f"Downloaded audio to: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None

def main():
    # Try the University of Alabama speech that was successfully transcribed earlier
    video_id = "5XSUTAIuApI"  # Trump's University of Alabama speech
    
    # Get video details
    video_details = get_video_details(video_id)
    
    if video_details:
        # Print video details
        print("\nVideo Details:")
        print(f"Title: {video_details['title']}")
        print(f"Channel: {video_details['channel_title']}")
        print(f"Published: {video_details['publish_date']}")
        print(f"Views: {video_details['views']}")
        print(f"Duration: {video_details['duration_seconds']} seconds")
        print(f"Description snippet: {video_details['description'][:100]}...")
        
        # Save metadata
        metadata_file = f"{METADATA_DIR}/{video_id}.json"
        with open(metadata_file, "w") as f:
            json.dump(video_details, f, indent=2)
        
        print(f"Saved metadata to: {metadata_file}")
    
    # Download audio
    audio_file = download_audio(video_id)
    
    if audio_file and os.path.exists(audio_file):
        # Check file size
        file_size = os.path.getsize(audio_file) / (1024 * 1024)  # MB
        print(f"\nAudio file size: {file_size:.2f} MB")
    else:
        print(f"\nAudio file not found or download failed")

if __name__ == "__main__":
    main()