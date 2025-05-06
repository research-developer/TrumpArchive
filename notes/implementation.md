# Trump Archive Implementation

This document provides an overview of the implemented Trump Archive system components.

## Implementation Overview

The system consists of several components:

1. **YouTube Data Collection**
   - Fetches videos from specified channels in `sources.json`
   - Uses YouTube API to get metadata
   - Downloads audio for transcription using yt-dlp

2. **Commentary Detection**
   - Uses LangChain with OpenAI to evaluate commentary level
   - Provides confidence scores for different commentary types
   - Flags videos for human review if confidence is low

3. **Transcript Processing**
   - Combines diarization with transcript text
   - Structures data with unique IDs for each segment
   - Saves in a searchable format

4. **API Layer**
   - Provides endpoints for listing videos, retrieving transcripts
   - Supports searching across all transcripts
   - Generates timestamped YouTube URLs

## Components Tested

- **YouTube API** (`test_youtube_api.py`)
  - Successfully retrieved videos from channels
  - Filtered for Trump-related content
  - Got video metadata

- **Audio Download** (`test_download.py`)
  - Used yt-dlp for audio extraction
  - Encountered some API rate limiting issues

- **Transcript Processing** (`test_transcript.py`)
  - Created structured transcript data
  - Added unique IDs for each segment

- **Commentary Detection** (`test_commentary_detection.py`)
  - Tested AI evaluation of commentary levels
  - Some improvements needed for accuracy

- **API Layer** (`api.py`)
  - Created FastAPI implementation
  - Endpoints for listing, searching, and retrieving data

## Next Steps

1. **Improve Commentary Detection**
   - Fine-tune prompts for better accuracy
   - Consider using a fine-tuned model for classification

2. **Enhance Diarization**
   - Implement more accurate speaker identification
   - Better alignment with transcript text

3. **Expand Data Collection**
   - Add more sources to `sources.json`
   - Implement automatic updates for new videos

4. **Web Frontend**
   - Build interface for browsing and searching
   - Add user features (clipping, commenting, etc.)

5. **Performance Optimization**
   - Implement caching for API responses
   - Consider database instead of file storage for scale

## Usage

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp sample.env .env
# Edit .env with your API keys

# Run API server
uvicorn api:app --reload
```

### API Endpoints
- `GET /videos` - List all videos
- `GET /videos/{video_id}` - Get video metadata
- `GET /videos/{video_id}/transcript` - Get video transcript
- `GET /search?q={query}` - Search transcripts
- `GET /videos/{video_id}/url` - Get YouTube URL
- `GET /videos/{video_id}/segments/{segment_id}/url` - Get timestamped URL

## Conclusion

The current implementation provides a solid foundation for the Trump Archive project. The system can fetch videos, evaluate commentary levels, process transcripts, and serve data through an API. With some improvements to accuracy and scale, this system can become a valuable resource for researchers and the public.