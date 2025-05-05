"""
Trump Speech Archive Pipeline

This program:
1. Fetches videos from YouTube channels listed in sources.json
2. Evaluates videos for commentary level
3. Processes transcripts with speaker diarization
4. Stores structured data for API use

Requirements:
- pytube for YouTube video fetching
- googleapiclient.discovery for YouTube API
- pyannote.audio for diarization
- transformers/whisper for transcription
- langchain or similar for AI evaluation
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

import googleapiclient.discovery
import pytube
from googleapiclient.errors import HttpError
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from pyannote.audio import Pipeline
import whisper

# Constants
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
DATA_DIR = "data"
AUDIO_DIR = f"{DATA_DIR}/audio"
TRANSCRIPT_DIR = f"{DATA_DIR}/transcripts"
METADATA_DIR = f"{DATA_DIR}/metadata"

# Create necessary directories
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

# Initialize YouTube API
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Initialize diarization pipeline
diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1", 
    use_auth_token=HUGGINGFACE_TOKEN
)

# Initialize transcription model
whisper_model = whisper.load_model("base")

# Initialize LLM for commentary detection
llm = OpenAI(temperature=0, openai_api_key=OPENAI_API_KEY)
commentary_prompt = PromptTemplate(
    input_variables=["title", "description", "transcript_segment"],
    template="""
    You are evaluating a YouTube video to determine if it contains commentary on Donald Trump or is a direct recording.
    
    Title: {title}
    Description: {description}
    Transcript segment: {transcript_segment}
    
    On a scale of 0-100, what is the confidence level that this video:
    1. Contains NO commentary (just Trump speaking or being interviewed)
    2. Contains MINIMAL commentary (brief intro/outro only)
    3. Contains SUBSTANTIAL commentary (analysis, interpretation, reaction)
    
    Output your answer as a JSON object with these fields:
    - no_commentary_confidence: 0-100
    - minimal_commentary_confidence: 0-100
    - substantial_commentary_confidence: 0-100
    - reasoning: Brief explanation of your reasoning
    - final_classification: One of ["no_commentary", "minimal_commentary", "substantial_commentary"]
    """
)
commentary_chain = LLMChain(llm=llm, prompt=commentary_prompt)


class VideoProcessor:
    """Process YouTube videos for the Trump Archive."""
    
    def __init__(self, sources_file="sources.json"):
        """Initialize with sources file."""
        with open(sources_file, "r") as f:
            self.sources = json.load(f)
        
        # Normalize commentary levels to numerical values
        self.commentary_map = {
            "none": 0,
            "minimal_intro/outro": 1,
            "substantial": 2
        }
        
        for source in self.sources:
            if source["commentary_level"] in self.commentary_map:
                source["commentary_level_numeric"] = self.commentary_map[source["commentary_level"]]
            else:
                source["commentary_level_numeric"] = 1  # Default to minimal
    
    def get_channel_videos(self, channel_url: str, max_results: int = 50) -> List[Dict]:
        """Get videos from a YouTube channel."""
        # Extract channel ID from URL
        channel_id = channel_url.split("/")[-1]
        if "user" in channel_url:
            try:
                # Handle 'user' URLs by first getting the channel ID
                response = youtube.channels().list(
                    part="id",
                    forUsername=channel_id
                ).execute()
                
                if response["items"]:
                    channel_id = response["items"][0]["id"]
                else:
                    print(f"Could not find channel ID for username: {channel_id}")
                    return []
            except HttpError as e:
                print(f"Error retrieving channel ID: {e}")
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
    
    def filter_trump_videos(self, videos: List[Dict], selectivity: float = 0.5) -> List[Dict]:
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
    
    def evaluate_commentary(self, video: Dict) -> Dict:
        """Evaluate the level of commentary in a video."""
        video_id = video["snippet"]["resourceId"]["videoId"]
        title = video["snippet"]["title"]
        description = video["snippet"].get("description", "")
        
        # Download video for processing
        try:
            youtube_video = pytube.YouTube(f"https://www.youtube.com/watch?v={video_id}")
            audio_stream = youtube_video.streams.filter(only_audio=True).first()
            
            if not audio_stream:
                print(f"Could not find audio stream for video: {video_id}")
                return None
            
            audio_file = audio_stream.download(
                output_path=AUDIO_DIR,
                filename=f"{video_id}.mp4"
            )
            
            # Convert to proper audio format if needed
            # This is simplified; you might need proper audio conversion
            
            # Get a small sample of the transcript for initial evaluation
            # This would ideally sample from beginning, middle, and end
            transcription = whisper_model.transcribe(audio_file)
            transcript_text = transcription["text"]
            
            # Sample segments from beginning, middle, and end
            segments = []
            if len(transcript_text) > 3000:
                segments = [
                    transcript_text[:1000],  # Beginning
                    transcript_text[len(transcript_text)//2-500:len(transcript_text)//2+500],  # Middle
                    transcript_text[-1000:]  # End
                ]
            else:
                segments = [transcript_text]
            
            # Evaluate each segment
            evaluations = []
            for segment in segments:
                evaluation = commentary_chain.run({
                    "title": title,
                    "description": description,
                    "transcript_segment": segment
                })
                
                # Parse JSON result
                try:
                    evaluation_data = json.loads(evaluation)
                    evaluations.append(evaluation_data)
                except json.JSONDecodeError:
                    print(f"Error parsing evaluation: {evaluation}")
                    continue
            
            # Aggregate evaluations
            if not evaluations:
                return {
                    "video_id": video_id,
                    "commentary_level": "undetermined",
                    "confidence": 0,
                    "needs_review": True
                }
            
            # Average confidence scores
            avg_no_commentary = sum(e["no_commentary_confidence"] for e in evaluations) / len(evaluations)
            avg_minimal = sum(e["minimal_commentary_confidence"] for e in evaluations) / len(evaluations)
            avg_substantial = sum(e["substantial_commentary_confidence"] for e in evaluations) / len(evaluations)
            
            # Determine final classification
            final_classification = "undetermined"
            confidence = 0
            
            if avg_no_commentary > avg_minimal and avg_no_commentary > avg_substantial:
                final_classification = "no_commentary"
                confidence = avg_no_commentary
            elif avg_minimal > avg_no_commentary and avg_minimal > avg_substantial:
                final_classification = "minimal_commentary"
                confidence = avg_minimal
            elif avg_substantial > avg_no_commentary and avg_substantial > avg_minimal:
                final_classification = "substantial_commentary"
                confidence = avg_substantial
            
            needs_review = confidence < 70  # Set threshold for human review
            
            return {
                "video_id": video_id,
                "commentary_level": final_classification,
                "confidence": confidence,
                "needs_review": needs_review,
                "evaluations": evaluations
            }
            
        except Exception as e:
            print(f"Error processing video {video_id}: {e}")
            return {
                "video_id": video_id,
                "commentary_level": "error",
                "confidence": 0,
                "needs_review": True,
                "error": str(e)
            }
    
    def process_transcript(self, video_id: str) -> Dict:
        """Process transcript with diarization."""
        audio_file = f"{AUDIO_DIR}/{video_id}.mp4"
        
        if not os.path.exists(audio_file):
            print(f"Audio file not found: {audio_file}")
            return None
        
        # Prepare for diarization
        diarization_input = {
            'uri': video_id,
            'audio': audio_file
        }
        
        # Run diarization
        diarization = diarization_pipeline(diarization_input)
        
        # Get full transcript
        transcription = whisper_model.transcribe(audio_file)
        
        # Process diarization result with transcript
        # This is simplified; a real implementation would align timestamps
        segments = []
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            start_time = turn.start
            end_time = turn.end
            
            # Find transcript text that corresponds to this time range
            # This is simplified; you'd need proper alignment in production
            segment_text = ""
            for segment in transcription["segments"]:
                seg_start = segment["start"]
                seg_end = segment["end"]
                
                # Check if segment overlaps with diarization turn
                if (seg_start <= end_time and seg_end >= start_time):
                    segment_text += segment["text"] + " "
            
            if segment_text:
                segments.append({
                    "id": str(uuid.uuid4()),
                    "start": start_time,
                    "end": end_time,
                    "speaker": speaker,
                    "text": segment_text.strip()
                })
        
        # If diarization failed or no segments, use full transcript with single timestamp
        if not segments:
            segments.append({
                "id": str(uuid.uuid4()),
                "start": 0,
                "end": transcription["segments"][-1]["end"] if transcription["segments"] else 0,
                "speaker": "SPEAKER_0",  # Default speaker
                "text": transcription["text"]
            })
        
        return {
            "video_id": video_id,
            "segments": segments,
            "processed_at": datetime.now().isoformat()
        }
    
    def save_processed_data(self, video_id: str, metadata: Dict, transcript: Dict):
        """Save processed data."""
        # Save metadata
        metadata_file = f"{METADATA_DIR}/{video_id}.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Save transcript
        transcript_file = f"{TRANSCRIPT_DIR}/{video_id}.json"
        with open(transcript_file, "w") as f:
            json.dump(transcript, f, indent=2)
    
    def process_channel(self, channel_info: Dict, max_videos: int = 10):
        """Process videos from a channel."""
        channel_url = channel_info["url"]
        selectivity = channel_info["selectivity"]
        channel_name = channel_info["channel_name"]
        
        print(f"Processing channel: {channel_name}")
        
        # Get videos from channel
        videos = self.get_channel_videos(channel_url, max_videos)
        
        # Filter Trump videos
        trump_videos = self.filter_trump_videos(videos, selectivity)
        
        print(f"Found {len(trump_videos)} Trump videos out of {len(videos)} total videos")
        
        # Process each video
        for video in trump_videos:
            video_id = video["snippet"]["resourceId"]["videoId"]
            title = video["snippet"]["title"]
            
            print(f"Processing video: {title} ({video_id})")
            
            # Evaluate commentary
            commentary_eval = self.evaluate_commentary(video)
            
            if not commentary_eval:
                print(f"Failed to evaluate commentary for video: {video_id}")
                continue
            
            # Skip videos with substantial commentary unless they need review
            if (commentary_eval["commentary_level"] == "substantial_commentary" and 
                not commentary_eval["needs_review"]):
                print(f"Skipping video with substantial commentary: {video_id}")
                continue
            
            # Process transcript
            transcript = self.process_transcript(video_id)
            
            if not transcript:
                print(f"Failed to process transcript for video: {video_id}")
                continue
            
            # Create metadata
            metadata = {
                "video_id": video_id,
                "title": title,
                "channel_name": channel_name,
                "channel_url": channel_url,
                "published_at": video["snippet"]["publishedAt"],
                "description": video["snippet"].get("description", ""),
                "commentary_evaluation": commentary_eval,
                "processed_at": datetime.now().isoformat()
            }
            
            # Save data
            self.save_processed_data(video_id, metadata, transcript)
            
            print(f"Successfully processed video: {video_id}")
    
    def run_pipeline(self, max_videos_per_channel: int = 10):
        """Run the complete pipeline."""
        for channel_info in self.sources:
            self.process_channel(channel_info, max_videos_per_channel)


if __name__ == "__main__":
    # Check for API keys
    if not YOUTUBE_API_KEY:
        print("YouTube API key not found. Please set YOUTUBE_API_KEY environment variable.")
        exit(1)
    
    if not OPENAI_API_KEY:
        print("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        exit(1)
    
    if not HUGGINGFACE_TOKEN:
        print("Hugging Face token not found. Please set HUGGINGFACE_TOKEN environment variable.")
        exit(1)
    
    # Initialize and run processor
    processor = VideoProcessor()
    processor.run_pipeline()