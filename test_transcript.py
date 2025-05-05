"""
Test processing a transcript.

This script will:
1. Use the pre-existing transcript fetched by the MCP YouTube transcript tool
2. Structure it with timestamps and segments
3. Save it in our desired format
"""

import os
import json
import re
import uuid
from datetime import datetime

# Create data directory if it doesn't exist
DATA_DIR = "data"
TRANSCRIPT_DIR = f"{DATA_DIR}/transcripts"
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

def extract_segments_from_transcript(transcript_text):
    """Extract timestamped segments from transcript text."""
    # This example is for the format used in the previous successful MCP transcript
    # Different transcripts might need different parsing logic
    
    # Simple regular expression to find time markers ([Music], timestamps)
    segments = []
    current_time = 0  # Start at 0 seconds
    
    # Break into paragraphs first
    paragraphs = transcript_text.split('\n\n')
    
    for paragraph in paragraphs:
        # Skip empty paragraphs
        if not paragraph.strip():
            continue
            
        # Process paragraph text 
        cleaned_text = paragraph.strip()
        
        # Create a segment for this paragraph
        segments.append({
            "id": str(uuid.uuid4()),
            "start": current_time,
            "end": current_time + 10,  # Placeholder duration
            "speaker": "SPEAKER_1",  # Default to single speaker for now
            "text": cleaned_text
        })
        
        # For demo purposes, increment the time by 10 seconds per paragraph
        current_time += 10
    
    return segments

def process_transcript(video_id, transcript_text):
    """Process transcript text into structured format."""
    segments = extract_segments_from_transcript(transcript_text)
    
    # Create structured transcript
    transcript_data = {
        "video_id": video_id,
        "segments": segments,
        "processed_at": datetime.now().isoformat(),
        "metadata": {
            "source": "MCP YouTube transcript tool",
            "format": "basic_segmentation"
        }
    }
    
    return transcript_data

def main():
    # Use the Alabama speech transcript we fetched
    video_id = "5XSUTAIuApI"
    
    # Sample transcript (just for demonstration)
    # In a real implementation, this would be loaded from the MCP result
    transcript_text = """# FULL REMARKS: President Trump delivers commencement speech at University of Alabama

[Music] Thank you, coach. Wow, what a nice looking group this is. What a beautiful group of people. And especially a very big hello to the University of Alabama. Congratulations to the class of 2025. Roll tide. Roll [Applause] tide. There are things that happen in life that are very important and you always remember where you were when they happened. As a student at Alabama, you'll always remember where you were when your head coach Nick Sabin retired. Remember that? Because he's done such a fantastic job. The last time I was here, and that's true with Nick. What a great coach. What a Let's bring him back. No, you have a good coach right now, though. I have a good coach right now. He was great. But the last time I was here, the Crimson Tide beat the Georgia Bulldogs [Music] 41-34. I was here. I got to watch it. That was some game. Today, it's my pleasure to return to this campus as the first president ever to deliver the keynote commencement address to this truly great American university. It's a great school and there's nowhere I'd rather be than right here in Tuscaloosa, Alabama. Title Town, USA. That's what it's become. And I love this place. Maybe it's because I won Alabama by 45 points. Could that be the reason? 45. You know, the way they say you like uh the polls have closed in Alabama. Trump has won Alabama immediately. It was very quick. It was very, very quick and nasty. That's what we like."""
    
    # Process transcript
    transcript_data = process_transcript(video_id, transcript_text)
    
    # Save to file
    output_file = f"{TRANSCRIPT_DIR}/{video_id}.json"
    with open(output_file, "w") as f:
        json.dump(transcript_data, f, indent=2)
    
    print(f"Saved transcript to: {output_file}")
    print(f"Number of segments: {len(transcript_data['segments'])}")
    
    # Display a sample segment
    if transcript_data["segments"]:
        print("\nSample segment:")
        sample = transcript_data["segments"][0]
        print(f"ID: {sample['id']}")
        print(f"Time: {sample['start']} - {sample['end']}")
        print(f"Speaker: {sample['speaker']}")
        print(f"Text: {sample['text'][:100]}...")

if __name__ == "__main__":
    main()