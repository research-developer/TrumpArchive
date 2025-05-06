"""
Generate UI presentation data from metadata and transcripts.

This script creates sample JSON data that would be presented to users in a front-end interface.
"""

import os
import json
import glob
from datetime import datetime
from typing import List, Dict, Any
import uuid

# Data directories
DATA_DIR = "data"
METADATA_DIR = f"{DATA_DIR}/metadata"
TRANSCRIPT_DIR = f"{DATA_DIR}/transcripts"
UI_DATA_DIR = f"{DATA_DIR}/ui"

# Create output directory
os.makedirs(UI_DATA_DIR, exist_ok=True)

def load_metadata(video_id: str) -> Dict[str, Any]:
    """Load metadata for a video."""
    metadata_file = f"{METADATA_DIR}/{video_id}.json"
    
    if not os.path.exists(metadata_file):
        return {}
    
    with open(metadata_file, "r") as f:
        return json.load(f)

def load_transcript(video_id: str) -> Dict[str, Any]:
    """Load transcript for a video."""
    transcript_file = f"{TRANSCRIPT_DIR}/{video_id}.json"
    
    if not os.path.exists(transcript_file):
        return {}
    
    with open(transcript_file, "r") as f:
        return json.load(f)

def format_duration(seconds: int) -> str:
    """Format duration in seconds to HH:MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def format_date(date_str: str) -> str:
    """Format ISO date to readable format."""
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%B %d, %Y')
    except:
        return date_str

def generate_topics(transcript_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate sample topics from transcript data."""
    # This would ideally use NLP or other analysis to identify real topics
    # For demo purposes, we're creating sample topics
    
    topics = []
    
    # Sample topics related to common Trump speech themes
    potential_topics = [
        {"name": "Economy", "keywords": ["economy", "jobs", "unemployment", "tariff", "taxes", "business"]},
        {"name": "Immigration", "keywords": ["border", "wall", "immigration", "illegal", "mexico"]},
        {"name": "Foreign Policy", "keywords": ["china", "russia", "nato", "iran", "north korea", "trade"]},
        {"name": "Election", "keywords": ["election", "vote", "ballot", "fraud", "rigged"]},
        {"name": "Military", "keywords": ["military", "troops", "veterans", "defense", "army", "navy"]},
        {"name": "Healthcare", "keywords": ["healthcare", "obamacare", "medicare", "doctors", "hospital"]},
        {"name": "Media", "keywords": ["fake news", "media", "press", "cnn", "news"]},
        {"name": "Energy", "keywords": ["energy", "oil", "gas", "pipeline", "fracking", "coal"]}
    ]
    
    # Check for topic keywords in transcript
    if transcript_data and "segments" in transcript_data:
        full_text = " ".join([segment["text"].lower() for segment in transcript_data["segments"]])
        
        for topic in potential_topics:
            for keyword in topic["keywords"]:
                if keyword.lower() in full_text:
                    # Found a match - create a topic entry
                    topic_entry = {
                        "id": str(uuid.uuid4()),
                        "name": topic["name"],
                        "relevance_score": 0.8,  # Placeholder score
                        "segment_ids": []  # Would contain IDs of relevant segments
                    }
                    
                    # Find segments containing this topic
                    for segment in transcript_data["segments"]:
                        if any(keyword.lower() in segment["text"].lower() for keyword in topic["keywords"]):
                            topic_entry["segment_ids"].append(segment["id"])
                    
                    if topic_entry["segment_ids"]:
                        topics.append(topic_entry)
                    
                    # Only add each topic once
                    break
    
    return topics

def generate_key_quotes(transcript_data: Dict[str, Any], max_quotes: int = 5) -> List[Dict[str, Any]]:
    """Generate key quotes from transcript data."""
    key_quotes = []
    
    if transcript_data and "segments" in transcript_data:
        # For demo, take segments that are a reasonable length for quotes
        for segment in transcript_data["segments"]:
            text = segment["text"]
            # Simple heuristic for finding quote-worthy segments:
            # - Not too short, not too long
            # - Ideally contains strong statements
            if 50 < len(text) < 200:
                key_quotes.append({
                    "id": segment["id"],
                    "text": text,
                    "start_time": segment["start"],
                    "end_time": segment["end"],
                    "importance_score": 0.9  # Placeholder score
                })
            
            if len(key_quotes) >= max_quotes:
                break
    
    return key_quotes

def generate_ui_data(video_id: str) -> Dict[str, Any]:
    """Generate UI data for a video."""
    metadata = load_metadata(video_id)
    transcript_data = load_transcript(video_id)
    
    if not metadata:
        print(f"No metadata found for video {video_id}")
        return {}
    
    if not transcript_data:
        print(f"No transcript found for video {video_id}")
        transcript_data = {"segments": []}
    
    # Generate UI data
    ui_data = {
        "id": video_id,
        "title": metadata.get("title", "Unknown Title"),
        "description": metadata.get("description", ""),
        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
        "channel": metadata.get("channel_title", "Unknown Channel"),
        "published_date": format_date(metadata.get("publish_date", "")),
        "duration": format_duration(metadata.get("duration_seconds", 0)),
        "view_count": int(metadata.get("views", 0)),
        "like_count": int(metadata.get("likes", 0)),
        "topics": generate_topics(transcript_data),
        "key_quotes": generate_key_quotes(transcript_data),
        "transcript": {
            "segments": []
        }
    }
    
    # Add transcript segments with formatted timestamps
    if "segments" in transcript_data:
        for segment in transcript_data["segments"]:
            ui_data["transcript"]["segments"].append({
                "id": segment.get("id", str(uuid.uuid4())),
                "text": segment.get("text", ""),
                "start_time": segment.get("start", 0),
                "end_time": segment.get("end", 0),
                "formatted_start": format_duration(int(segment.get("start", 0))),
                "formatted_end": format_duration(int(segment.get("end", 0))),
                "speaker": segment.get("speaker", "SPEAKER_1"),
                "is_trump": segment.get("speaker", "SPEAKER_1") == "SPEAKER_1"  # Assuming Trump is speaker 1
            })
    
    return ui_data

def create_sample_data():
    """Create sample UI data if no real data exists."""
    # Use Alabama speech video ID
    video_id = "5XSUTAIuApI"
    
    # Check if we already have metadata and transcript
    if not os.path.exists(f"{METADATA_DIR}/{video_id}.json"):
        # Create sample metadata
        sample_metadata = {
            "video_id": video_id,
            "title": "FULL REMARKS: President Trump delivers commencement speech at University of Alabama",
            "channel_title": "LiveNOW from FOX",
            "publish_date": "2025-05-02T01:55:19Z",
            "description": "President Trump's spring commencement address to graduating seniors at The University at Alabama.",
            "views": 110646,
            "likes": 7856,
            "duration_seconds": 3371,
            "tags": ["Trump", "Alabama", "commencement", "speech", "graduation"]
        }
        
        # Save sample metadata
        os.makedirs(METADATA_DIR, exist_ok=True)
        with open(f"{METADATA_DIR}/{video_id}.json", "w") as f:
            json.dump(sample_metadata, f, indent=2)
    
    # Create sample transcript if it doesn't exist
    if not os.path.exists(f"{TRANSCRIPT_DIR}/{video_id}.json"):
        # Create sample transcript segments
        segments = []
        
        # Sample transcript text (truncated for brevity)
        speech_text = """Thank you, coach. Wow, what a nice looking group this is. What a beautiful group of people. And especially a very big hello to the University of Alabama. Congratulations to the class of 2025. Roll tide. Roll tide.

There are things that happen in life that are very important and you always remember where you were when they happened. As a student at Alabama, you'll always remember where you were when your head coach Nick Sabin retired.

The last time I was here, the Crimson Tide beat the Georgia Bulldogs 41-34. I was here. I got to watch it. That was some game. Today, it's my pleasure to return to this campus as the first president ever to deliver the keynote commencement address to this truly great American university.

It's a great school and there's nowhere I'd rather be than right here in Tuscaloosa, Alabama. Title Town, USA. That's what it's become. And I love this place. Maybe it's because I won Alabama by 45 points. Could that be the reason? 45.

You know, the way they say you like the polls have closed in Alabama. Trump has won Alabama immediately. It was very quick. It was very, very quick and nasty. That's what we like.

I want to thank President Bell for his 10 years of distinguished service. Highly respected gentleman. But 10 years of service to this great university, overseeing the education of 100,000 proud Alabama graduates.

We've created 350,000 new jobs and brought core inflation down to its lowest level in many, many years. Energy is down. Look at your cost of energy. Way down. Groceries are down. Even eggs are down.

We've had one of the greatest economies in the history of our country during the first term of Trump. And then we got hit hard with inflation during the Biden economy. It was horrible. We were hit so hard.

As you embark on this great adventure, let me share some of the biggest lessons I've learned from a lifetime spent building dreams and beating the odds. I beat a lot of odds. Lot of odds. A lot of people said, "I don't know." But it worked out okay.

First, if you're here today and think that you're too young to do something great, let me tell you that you are wrong. You're not too young. You can have great success at a very young age.

Second of all, and very importantly, you have to love what you do. I rarely see somebody that's successful that doesn't love what he or she does. That's way you really like work isn't work. It's fun.

Third thing is to think big. You know, you're going to do something, you might as well think big because it's just as tough. You can think small. I know a lot of people, they thought small. They're very smart."""
        
        # Split into paragraphs and create segments
        paragraphs = speech_text.split('\n\n')
        start_time = 0
        
        for i, paragraph in enumerate(paragraphs):
            # Each paragraph is roughly 30 seconds
            end_time = start_time + 30
            
            segments.append({
                "id": str(uuid.uuid4()),
                "start": start_time,
                "end": end_time,
                "speaker": "SPEAKER_1",  # Assuming Trump is speaker 1
                "text": paragraph.strip()
            })
            
            start_time = end_time
        
        # Save sample transcript
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
        with open(f"{TRANSCRIPT_DIR}/{video_id}.json", "w") as f:
            json.dump({
                "video_id": video_id,
                "segments": segments,
                "processed_at": datetime.now().isoformat()
            }, f, indent=2)

def main():
    # Create sample data if none exists
    create_sample_data()
    
    # Get all video IDs from metadata directory
    metadata_files = glob.glob(f"{METADATA_DIR}/*.json")
    video_ids = [os.path.basename(f).replace(".json", "") for f in metadata_files]
    
    print(f"Found {len(video_ids)} videos")
    
    # Generate UI data for each video
    for video_id in video_ids:
        print(f"Generating UI data for video {video_id}")
        ui_data = generate_ui_data(video_id)
        
        if ui_data:
            # Save UI data
            output_file = f"{UI_DATA_DIR}/{video_id}.json"
            with open(output_file, "w") as f:
                json.dump(ui_data, f, indent=2)
            
            print(f"Saved UI data to {output_file}")
    
    # Create index file with all videos
    all_videos = []
    
    for video_id in video_ids:
        ui_data_file = f"{UI_DATA_DIR}/{video_id}.json"
        
        if os.path.exists(ui_data_file):
            with open(ui_data_file, "r") as f:
                ui_data = json.load(f)
            
            # Add summary for index
            all_videos.append({
                "id": video_id,
                "title": ui_data.get("title", "Unknown Title"),
                "thumbnail_url": ui_data.get("thumbnail_url", ""),
                "channel": ui_data.get("channel", "Unknown Channel"),
                "published_date": ui_data.get("published_date", ""),
                "duration": ui_data.get("duration", "0:00"),
                "topic_count": len(ui_data.get("topics", [])),
                "segment_count": len(ui_data.get("transcript", {}).get("segments", [])),
                "view_count": ui_data.get("view_count", 0)
            })
    
    # Sort by date (newest first)
    all_videos.sort(key=lambda x: x["published_date"], reverse=True)
    
    # Save index
    index_file = f"{UI_DATA_DIR}/index.json"
    with open(index_file, "w") as f:
        json.dump({
            "videos": all_videos,
            "total": len(all_videos),
            "generated_at": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"Saved index file to {index_file}")
    
    # Generate human-readable example
    example_file = f"{UI_DATA_DIR}/example_ui.md"
    
    if video_ids:
        # Use first video for example
        with open(f"{UI_DATA_DIR}/{video_ids[0]}.json", "r") as f:
            example_data = json.load(f)
        
        with open(example_file, "w") as f:
            f.write("# Trump Archive UI Data Example\n\n")
            f.write("This document shows how the data would be presented in a user interface.\n\n")
            
            f.write("## Video Details\n\n")
            f.write(f"**Title**: {example_data.get('title', 'Unknown Title')}\n\n")
            f.write(f"**Published**: {example_data.get('published_date', 'Unknown Date')}\n\n")
            f.write(f"**Channel**: {example_data.get('channel', 'Unknown Channel')}\n\n")
            f.write(f"**Duration**: {example_data.get('duration', '0:00')}\n\n")
            f.write(f"**Views**: {example_data.get('view_count', 0):,}\n\n")
            f.write(f"**Likes**: {example_data.get('like_count', 0):,}\n\n")
            
            f.write("## Description\n\n")
            f.write(f"{example_data.get('description', 'No description available.')}\n\n")
            
            f.write("## Key Topics\n\n")
            for topic in example_data.get("topics", []):
                f.write(f"- **{topic.get('name', 'Unknown Topic')}**\n")
            
            f.write("\n## Key Quotes\n\n")
            for i, quote in enumerate(example_data.get("key_quotes", [])):
                f.write(f"### Quote {i+1} [{quote.get('formatted_start', '0:00')}]\n\n")
                f.write(f"_{quote.get('text', 'No text available.')}_\n\n")
            
            f.write("## Transcript Excerpt\n\n")
            segments = example_data.get("transcript", {}).get("segments", [])
            for i, segment in enumerate(segments[:5]):  # Show first 5 segments
                f.write(f"**[{segment.get('formatted_start', '0:00')}]** {segment.get('text', 'No text available.')}\n\n")
            
            if len(segments) > 5:
                f.write("_... and more segments ..._\n\n")
            
            f.write("## UI Presentation\n\n")
            f.write("The front-end would include:\n\n")
            f.write("1. Video player with YouTube embed\n")
            f.write("2. Interactive transcript that follows along with video\n")
            f.write("3. Topic navigation to jump to relevant sections\n")
            f.write("4. Share buttons for specific segments\n")
            f.write("5. Search functionality across all speeches\n")
        
        print(f"Generated example UI document at {example_file}")

if __name__ == "__main__":
    main()