"""
Simple API for the Trump Archive Project.

This script provides a basic FastAPI implementation for:
1. Listing available speeches
2. Getting transcript details
3. Searching transcripts
4. Getting video information

To run:
uvicorn api:app --reload
"""

import os
import json
import glob
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# Data directories
DATA_DIR = "data"
METADATA_DIR = f"{DATA_DIR}/metadata"
TRANSCRIPT_DIR = f"{DATA_DIR}/transcripts"

# Models
class TranscriptSegment(BaseModel):
    id: str
    start: float
    end: float
    speaker: str
    text: str

class Transcript(BaseModel):
    video_id: str
    segments: List[TranscriptSegment]
    processed_at: str
    metadata: Optional[Dict[str, Any]] = None

class VideoMetadata(BaseModel):
    video_id: str
    title: str
    channel_title: str
    publish_date: str
    description: str
    views: int
    likes: int
    duration_seconds: int
    tags: List[str]

class SearchResult(BaseModel):
    video_id: str
    title: str
    matches: List[TranscriptSegment]
    
# Initialize FastAPI
app = FastAPI(
    title="Trump Archive API",
    description="API for accessing Donald Trump's speeches, interviews, and statements",
    version="0.1.0"
)

# Helper functions
def load_metadata(video_id: str) -> Optional[VideoMetadata]:
    """Load metadata for a video."""
    metadata_file = f"{METADATA_DIR}/{video_id}.json"
    
    if not os.path.exists(metadata_file):
        return None
    
    with open(metadata_file, "r") as f:
        data = json.load(f)
        return VideoMetadata(**data)

def load_transcript(video_id: str) -> Optional[Transcript]:
    """Load transcript for a video."""
    transcript_file = f"{TRANSCRIPT_DIR}/{video_id}.json"
    
    if not os.path.exists(transcript_file):
        return None
    
    with open(transcript_file, "r") as f:
        data = json.load(f)
        return Transcript(**data)

def list_videos() -> List[VideoMetadata]:
    """List all available videos."""
    videos = []
    metadata_files = glob.glob(f"{METADATA_DIR}/*.json")
    
    for file in metadata_files:
        video_id = os.path.basename(file).replace(".json", "")
        metadata = load_metadata(video_id)
        if metadata:
            videos.append(metadata)
    
    return videos

def search_transcripts(query: str) -> List[SearchResult]:
    """Search transcripts for matching text."""
    results = []
    transcript_files = glob.glob(f"{TRANSCRIPT_DIR}/*.json")
    
    for file in transcript_files:
        video_id = os.path.basename(file).replace(".json", "")
        transcript = load_transcript(video_id)
        metadata = load_metadata(video_id)
        
        if not transcript or not metadata:
            continue
        
        # Find matching segments
        matches = []
        for segment in transcript.segments:
            if query.lower() in segment.text.lower():
                matches.append(segment)
        
        if matches:
            results.append(SearchResult(
                video_id=video_id,
                title=metadata.title,
                matches=matches
            ))
    
    return results

# API Routes
@app.get("/")
def read_root():
    return {"message": "Welcome to the Trump Archive API"}

@app.get("/videos", response_model=List[VideoMetadata])
def get_videos():
    """Get a list of all available videos."""
    return list_videos()

@app.get("/videos/{video_id}", response_model=VideoMetadata)
def get_video(video_id: str):
    """Get metadata for a specific video."""
    metadata = load_metadata(video_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return metadata

@app.get("/videos/{video_id}/transcript", response_model=Transcript)
def get_transcript(video_id: str):
    """Get transcript for a specific video."""
    transcript = load_transcript(video_id)
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return transcript

@app.get("/search", response_model=List[SearchResult])
def search(q: str = Query(..., description="Search query")):
    """Search transcripts for matching text."""
    if not q or len(q) < 3:
        raise HTTPException(status_code=400, detail="Search query must be at least 3 characters")
    
    results = search_transcripts(q)
    return results

# YouTube video URL helper
@app.get("/videos/{video_id}/url")
def get_video_url(video_id: str):
    """Get YouTube URL for a specific video."""
    metadata = load_metadata(video_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return {
        "video_id": video_id,
        "youtube_url": f"https://www.youtube.com/watch?v={video_id}"
    }

# Add timestamp URL helper
@app.get("/videos/{video_id}/segments/{segment_id}/url")
def get_segment_url(video_id: str, segment_id: str):
    """Get YouTube URL with timestamp for a specific segment."""
    transcript = load_transcript(video_id)
    
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    # Find segment
    segment = None
    for s in transcript.segments:
        if s.id == segment_id:
            segment = s
            break
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    # Convert to seconds
    start_seconds = int(segment.start)
    
    return {
        "video_id": video_id,
        "segment_id": segment_id,
        "start_time": start_seconds,
        "youtube_url": f"https://www.youtube.com/watch?v={video_id}&t={start_seconds}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)