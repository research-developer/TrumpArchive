# Trump Archive

A comprehensive archive of Donald Trump's speeches, interviews, and public statements with a focus on raw, unedited footage without commentary. The system provides searchable transcripts linked to video timestamps.

## Project Overview

The Trump Archive project is designed to:

1. Monitor YouTube channels for Trump-related content
2. Download, process, and archive videos with transcripts
3. Detect and filter commentary vs. direct statements
4. Provide a searchable API and UI for exploring the content
5. Enable clipping, sharing, and referencing specific statements

## Components

### Data Collection

- **YouTube Monitoring**: Hybrid system using WebSub (PubSubHubbub) notifications with API polling fallback
- **Video Filtering**: Relevance scoring to identify Trump-related content
- **Content Download**: Using yt-dlp for reliable video/audio acquisition

### Processing Pipeline

- **Transcript Generation**: Convert speech to text with timestamps
- **Commentary Detection**: AI-powered system to identify and filter commentary
- **Speaker Diarization**: Identify when Trump is speaking versus others
- **Topic Identification**: Automatically categorize content by topic

### API and Frontend

- **FastAPI Backend**: Provides endpoints for accessing the archive
- **Interactive UI**: Search, browse, and interact with archived content
- **Timestamp Linking**: Direct access to specific moments in videos

## Getting Started

### Prerequisites

- Python 3.8+
- YouTube API key (set in `.env` file)
- OpenAI API key for commentary detection

### Installation

1. Clone this repository

```bash
git clone https://github.com/yourusername/trump-archive.git
cd trump-archive
```

1. Install dependencies

```bash
pip install -r requirements.txt
```

1. Create `.env` file with required API keys

```env
YOUTUBE_API_KEY=your_youtube_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

1. Configure channels to monitor in `sources.json`

### Running the System

#### Testing Individual Components

- Test YouTube API: `python test_youtube_api.py`
- Test Video Download: `python test_download.py`
- Test Transcript Processing: `python test_transcript.py`
- Test Commentary Detection: `python test_commentary_detection.py`

#### Running the Full Pipeline

```bash
python archive_pipeline.py
```

#### Starting the API Server

```bash
python -m uvicorn api:app --reload
```

## Data Format

### Metadata

```json
{
  "video_id": "5XSUTAIuApI",
  "title": "President Trump delivers commencement speech at University of Alabama",
  "channel_name": "C-SPAN",
  "channel_url": "https://www.youtube.com/user/CSPAN",
  "published_at": "2023-05-15T00:00:00Z",
  "description": "Full remarks by President Trump...",
  "commentary_evaluation": {
    "commentary_level": "no_commentary",
    "confidence": 95.5,
    "needs_review": false
  },
  "processed_at": "2023-05-16T12:34:56Z"
}
```

### Transcript

```json
{
  "video_id": "5XSUTAIuApI",
  "segments": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "start": 34.2,
      "end": 48.5,
      "speaker": "SPEAKER_1",
      "text": "Thank you, coach. Wow, what a nice looking group this is."
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "start": 48.5,
      "end": 64.1,
      "speaker": "SPEAKER_1", 
      "text": "What a beautiful group of people. And especially a very big hello to the University of Alabama."
    }
  ],
  "processed_at": "2023-05-16T12:34:56Z"
}
```

## Project Roadmap

### Phase 1: Core Implementation (Completed)

- YouTube API integration ✓
- Video downloading system ✓
- Transcript processing ✓
- Commentary detection ✓
- Basic API implementation ✓
- UI mockup ✓

### Phase 2: Continuous Monitoring (Current)

- WebSub notification system
- Scheduled polling fallback
- Processing queue integration
- Quota management system

### Phase 3: Advanced Features (Upcoming)

- User accounts for saving clips/comments
- Timeline view of statements by topic
- Advanced search capabilities
- Mobile-optimized interface

### Phase 4: Public Release

- Documentation and usage guides
- API rate limiting and security
- Account management
- Privacy controls

## Technical Architecture

The system uses a modular architecture with several key components:

1. **Monitoring Service**: Watches for new content using WebSub and scheduled polling
2. **Processing Pipeline**: Handles downloading, transcription, and analysis
3. **Storage Layer**: Manages structured data for efficient retrieval
4. **API Server**: Provides endpoints for accessing the archive
5. **Frontend**: User interface for exploring and interacting with content

## API Documentation

The API provides several endpoints for accessing the archive:

- `GET /videos`: List available videos with filtering options
- `GET /videos/{video_id}`: Get details for a specific video
- `GET /videos/{video_id}/transcript`: Get the full transcript for a video
- `GET /search`: Search across all transcripts
- `GET /topics`: Get list of available topics
- `GET /topics/{topic_id}/segments`: Get transcript segments for a specific topic

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
