"""
Simple test to fetch videos from a YouTube channel using the YouTube API.
"""

import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get YouTube API key
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not YOUTUBE_API_KEY:
    print("YouTube API key not found. Please set YOUTUBE_API_KEY in .env file.")
    exit(1)

# Initialize YouTube API
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_channel_id(channel_url):
    """Extract channel ID from URL or get it from username."""
    if "/channel/" in channel_url:
        return channel_url.split("/channel/")[1]
    
    if "/user/" in channel_url:
        username = channel_url.split("/user/")[1]
        try:
            response = youtube.channels().list(
                part="id",
                forUsername=username
            ).execute()
            
            if response["items"]:
                return response["items"][0]["id"]
            else:
                print(f"Could not find channel ID for username: {username}")
                return None
        except HttpError as e:
            print(f"Error retrieving channel ID: {e}")
            return None
    
    if "/@" in channel_url:
        handle = channel_url.split("/@")[1]
        try:
            response = youtube.search().list(
                part="snippet",
                q=handle,
                type="channel",
                maxResults=1
            ).execute()
            
            if response["items"]:
                return response["items"][0]["snippet"]["channelId"]
            else:
                print(f"Could not find channel ID for handle: {handle}")
                return None
        except HttpError as e:
            print(f"Error retrieving channel ID: {e}")
            return None
    
    return channel_url.split("/")[-1]

def get_channel_videos(channel_url, max_results=10):
    """Get videos from a YouTube channel."""
    # Get channel ID
    channel_id = get_channel_id(channel_url)
    
    if not channel_id:
        return []
    
    try:
        # Get channel uploads playlist ID
        response = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()
        
        if not response["items"]:
            print(f"No channel found with ID: {channel_id}")
            return []
        
        # Get uploads playlist ID
        uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # Get videos from uploads playlist
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            playlist_response = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_results - len(videos)),
                pageToken=next_page_token
            ).execute()
            
            videos.extend(playlist_response["items"])
            
            next_page_token = playlist_response.get("nextPageToken")
            if not next_page_token:
                break
        
        return videos
    except HttpError as e:
        print(f"Error retrieving videos: {e}")
        return []

def filter_trump_videos(videos, selectivity=0.5):
    """Filter videos to only include those featuring Trump."""
    trump_videos = []
    
    for video in videos:
        snippet = video["snippet"]
        title = snippet["title"].lower()
        description = snippet.get("description", "").lower()
        
        # Check if video is about Trump
        trump_keywords = ["trump", "donald trump", "president trump", "former president trump"]
        
        # Calculate match score based on title and description
        score = 0
        for keyword in trump_keywords:
            if keyword in title:
                score += 0.6  # Higher weight for title matches
            if keyword in description:
                score += 0.4  # Lower weight for description matches
        
        # Add video if score exceeds selectivity threshold
        if score > selectivity:
            trump_videos.append(video)
    
    return trump_videos

def main():
    # Load sources file
    with open("sources.json", "r") as f:
        sources = json.load(f)
    
    # Process first channel as a test
    channel = sources[0]
    channel_url = channel["url"]
    channel_name = channel["channel_name"]
    selectivity = channel["selectivity"]
    
    print(f"Testing channel: {channel_name} ({channel_url})")
    
    # Get videos from channel
    videos = get_channel_videos(channel_url, max_results=10)
    
    print(f"Found {len(videos)} videos")
    
    # Filter Trump videos
    trump_videos = filter_trump_videos(videos, selectivity)
    
    print(f"Found {len(trump_videos)} Trump videos")
    
    # Print video details
    for video in trump_videos:
        video_id = video["snippet"]["resourceId"]["videoId"]
        title = video["snippet"]["title"]
        published_at = video["snippet"]["publishedAt"]
        
        print(f"- {title} ({video_id}) - Published: {published_at}")

if __name__ == "__main__":
    main()