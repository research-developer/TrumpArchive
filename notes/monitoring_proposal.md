# YouTube Monitoring and Content Archiving Proposal for Trump Archive

## Executive Summary

This proposal outlines a hybrid approach for monitoring YouTube channels to collect Donald Trump's speeches, interviews, and public statements. The system will use WebSub (PubSubHubbub) as the primary notification mechanism, with scheduled API polling as a fallback. This approach balances reliability, quota efficiency, and real-time updates while maintaining compliance with YouTube's Terms of Service.

## Proposed Architecture

### 1. Primary Channel Monitoring: WebSub Notifications

WebSub (formerly PubSubHubbub) provides immediate notifications when new content is published, without consuming YouTube API quota.

#### Implementation Details:
- **Subscription Setup**: Subscribe to each channel's Atom feed using the endpoint `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`
- **Webhook Server**: Deploy a lightweight callback server (AWS Lambda or similar) to:
  - Handle verification challenges
  - Process Atom feed notifications containing video IDs and metadata
  - Queue videos for further processing through our pipeline

#### Benefits:
- Zero YouTube API quota usage for notifications
- Near real-time updates (typically within seconds of video publishing)
- Reduces polling frequency, lowering infrastructure costs

#### Challenges and Mitigations:
- **Challenge**: WebSub subscriptions expire after a certain period (typically 5 days)
  - **Mitigation**: Implement automatic renewal logic that re-subscribes every 4 days
- **Challenge**: Occasional missed notifications
  - **Mitigation**: Implement fallback polling (described below)

### 2. Fallback System: Scheduled API Polling

To ensure reliability and catch any missed WebSub notifications, we'll implement a scheduled polling mechanism.

#### Implementation Details:
- **Polling Schedule**: Check channels at different intervals based on their update frequency:
  - "real-time" channels: Every 6 hours
  - "daily" channels: Every 12 hours
  - "weekly" and "monthly" channels: Every 24 hours
- **Quota-Efficient Approach**:
  - Use `playlistItems.list` on the channel's uploads playlist (as already implemented in `test_youtube_api.py`) instead of more expensive `search` operations
  - Batch video metadata requests (up to 50 IDs per request)
  - Store last check timestamp to only process new videos

#### Benefits:
- Ensures no videos are missed due to WebSub notification failures
- Significantly reduces API quota usage compared to pure polling

### 3. Video Processing Pipeline Integration

Once videos are discovered (through either WebSub or polling), they will be processed through our existing pipeline:

1. **Filtering**: Apply the `filter_trump_videos()` logic to determine relevance
2. **Metadata Retrieval**: Fetch complete video details using batched `videos.list` calls
3. **Download**: Use yt-dlp to download the video audio (already implemented in `test_download.py`)
4. **Transcript Processing**: Generate and segment transcripts (via `test_transcript.py`)
5. **Commentary Detection**: Apply our LangChain/OpenAI detection (via `test_commentary_detection.py`)
6. **Storage**: Save processed data in structured JSON format for API access

### 4. Quota Management Strategy

Based on the YouTube best practices document, we'll implement multiple techniques to stay within the 10,000 units daily quota:

1. **Prioritize WebSub**: Use this zero-quota approach as the primary notification mechanism
2. **Efficient API Usage**:
   - Use `videos.list` with batched IDs instead of `search` when possible (1 unit vs 100 units)
   - Process up to 50 videos in a single API call when fetching metadata
   - Implement incremental processing only for new videos
3. **Intelligent Scheduling**:
   - Distribute API calls throughout the day to avoid spikes
   - Prioritize high-value channels (based on the `selectivity` score in sources.json)
4. **Quota Monitoring**:
   - Track daily quota usage with alerts at 75% and 90% thresholds
   - Implement circuit breakers to pause non-essential operations when quota is running low

### 5. Infrastructure Implementation

#### Components:
1. **WebSub Callback Server**:
   - Serverless function (AWS Lambda/Cloudflare Worker)
   - Handles subscription verification and notifications
   - Forwards new video IDs to the processing queue

2. **Scheduler Service**:
   - Manages periodic channel polling based on update frequency
   - Handles WebSub subscription renewal
   - Uses distributed locking to prevent duplicate processing

3. **Processing Queue**:
   - Message queue (SQS, RabbitMQ, etc.) to manage video processing jobs
   - Ensures reliable delivery and processing with retry logic

4. **Pipeline Worker**:
   - Consumes from the processing queue
   - Executes the full processing pipeline for each video
   - Updates database with processed content

5. **Monitoring & Alerting**:
   - Tracks quota usage, processing errors, and system health
   - Sends alerts for quota thresholds and processing failures

## Code Implementation Plan

### 1. Update Existing Code

#### Enhance `test_youtube_api.py`:
```python
def subscribe_to_channel_websub(channel_id, callback_url, verify_token=None):
    """Subscribe to WebSub notifications for a channel."""
    hub_url = "https://pubsubhubbub.appspot.com/subscribe"
    topic_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    
    data = {
        "hub.callback": callback_url,
        "hub.mode": "subscribe",
        "hub.topic": topic_url,
        "hub.lease_seconds": 432000,  # 5 days
    }
    
    if verify_token:
        data["hub.verify_token"] = verify_token
        
    response = requests.post(hub_url, data=data)
    return response.status_code == 202
```

#### Create WebSub Callback Handler:
```python
# webhook_handler.py (serverless function)
def handle_websub_callback(event, context):
    # Verification request handling
    query_params = event.get("queryStringParameters", {})
    if "hub.challenge" in query_params:
        return {
            "statusCode": 200,
            "body": query_params["hub.challenge"]
        }
    
    # Content notification handling
    try:
        body = event.get("body", "")
        feed = feedparser.parse(body)
        
        for entry in feed.entries:
            video_id = entry.yt_videoid
            channel_id = entry.yt_channelid
            
            # Queue for processing
            enqueue_video_for_processing(video_id, channel_id)
            
        return {"statusCode": 200, "body": "Success"}
    except Exception as e:
        print(f"Error processing notification: {e}")
        return {"statusCode": 500, "body": str(e)}
```

### 2. Create New Components

#### Scheduling System:
```python
# scheduler.py
import schedule
import time
from datetime import datetime
import json

def load_channels():
    with open("sources.json", "r") as f:
        return json.load(f)

def check_and_renew_subscriptions():
    """Renew WebSub subscriptions that are nearing expiration"""
    channels = load_channels()
    for channel in channels:
        channel_id = get_channel_id(channel["url"])
        # Check if subscription needs renewal (every 4 days)
        if needs_renewal(channel_id):
            callback_url = f"{WEBHOOK_BASE_URL}/youtube-notification"
            subscribe_to_channel_websub(channel_id, callback_url)
            update_subscription_timestamp(channel_id)

def poll_channel_updates(frequency):
    """Poll channels with the specified update frequency"""
    channels = load_channels()
    for channel in channels:
        if channel["update_frequency"] == frequency:
            channel_url = channel["url"]
            last_check = get_last_check_timestamp(channel_url)
            
            # Get videos since last check
            videos = get_channel_videos_since(channel_url, last_check)
            
            # Filter and process videos
            for video in filter_trump_videos(videos, channel["selectivity"]):
                video_id = video["snippet"]["resourceId"]["videoId"]
                enqueue_video_for_processing(video_id, get_channel_id(channel_url))
            
            update_last_check_timestamp(channel_url)

# Set up schedules
schedule.every(6).hours.do(poll_channel_updates, "real-time")
schedule.every(12).hours.do(poll_channel_updates, "daily")
schedule.every(24).hours.do(poll_channel_updates, "weekly")
schedule.every(24).hours.do(poll_channel_updates, "monthly")
schedule.every(4).days.at("02:00").do(check_and_renew_subscriptions)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(60)
```

#### Video Processing Queue Integration:
```python
# queue_manager.py
import boto3
import json
import os

# Initialize SQS client
sqs = boto3.client('sqs')
QUEUE_URL = os.environ.get('VIDEO_PROCESSING_QUEUE_URL')

def enqueue_video_for_processing(video_id, channel_id):
    """Add a video to the processing queue."""
    message = {
        'video_id': video_id,
        'channel_id': channel_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message)
    )
    
    return response['MessageId']

def process_queue_message(message):
    """Process a message from the queue."""
    body = json.loads(message['Body'])
    video_id = body['video_id']
    channel_id = body['channel_id']
    
    # Check if video already processed
    if is_video_processed(video_id):
        return
    
    try:
        # 1. Get video metadata
        video_metadata = get_video_metadata(video_id)
        
        # 2. Check if it meets criteria (Trump-related)
        if not is_trump_related(video_metadata):
            mark_video_not_relevant(video_id)
            return
        
        # 3. Download video audio
        audio_path = download_video_audio(video_id)
        
        # 4. Process transcript
        transcript = process_transcript(audio_path, video_id)
        
        # 5. Detect commentary
        commentary_result = detect_commentary(transcript, video_id)
        
        # 6. Store processed data
        store_processed_data(video_id, video_metadata, transcript, commentary_result)
        
        # 7. Mark as processed
        mark_video_processed(video_id)
        
    except Exception as e:
        print(f"Error processing video {video_id}: {e}")
        # Add to dead letter queue or retry queue
```

### 3. Create System Monitoring and Quota Management

```python
# quota_manager.py
import redis
import os
from datetime import datetime, timedelta
import requests
import json

# Initialize Redis client for quota tracking
redis_client = redis.Redis(host=os.environ.get('REDIS_HOST', 'localhost'))
QUOTA_KEY = 'youtube_api_quota_usage'
QUOTA_LIMIT = 10000  # Daily YouTube API quota limit

def track_api_call(operation, units=1):
    """Track YouTube API call and its quota usage."""
    today = datetime.utcnow().strftime('%Y-%m-%d')
    key = f"{QUOTA_KEY}:{today}"
    
    # Increment quota usage
    new_total = redis_client.incrby(key, units)
    
    # Set expiry (36 hours to ensure we keep today's data through tomorrow)
    redis_client.expire(key, 36 * 60 * 60)
    
    # Log operation
    redis_client.lpush(f"{key}:log", json.dumps({
        'timestamp': datetime.utcnow().isoformat(),
        'operation': operation,
        'units': units
    }))
    
    # Check thresholds and alert if needed
    check_quota_thresholds(new_total)
    
    return new_total

def check_quota_thresholds(current_usage):
    """Check if quota usage has crossed any thresholds."""
    percentage = (current_usage / QUOTA_LIMIT) * 100
    
    if percentage >= 90 and not redis_client.get(f"{QUOTA_KEY}:alert:90"):
        send_alert(f"YouTube API quota at 90%! Current usage: {current_usage}/{QUOTA_LIMIT}")
        redis_client.setex(f"{QUOTA_KEY}:alert:90", 24 * 60 * 60, 1)
    
    elif percentage >= 75 and not redis_client.get(f"{QUOTA_KEY}:alert:75"):
        send_alert(f"YouTube API quota at 75%! Current usage: {current_usage}/{QUOTA_LIMIT}")
        redis_client.setex(f"{QUOTA_KEY}:alert:75", 24 * 60 * 60, 1)
    
    return percentage

def can_make_api_call(units_required=1):
    """Check if there's enough quota to make an API call."""
    today = datetime.utcnow().strftime('%Y-%m-%d')
    key = f"{QUOTA_KEY}:{today}"
    
    current_usage = int(redis_client.get(key) or 0)
    return (current_usage + units_required) <= QUOTA_LIMIT

def send_alert(message):
    """Send alert notification."""
    # Send to Slack webhook or email
    webhook_url = os.environ.get('ALERT_WEBHOOK_URL')
    if webhook_url:
        requests.post(webhook_url, json={'text': message})
    
    print(f"ALERT: {message}")
```

## Implementation Timeline

1. **Phase 1: WebSub Integration (Week 1-2)**
   - Set up WebSub subscription system
   - Create webhook handler
   - Test end-to-end notification workflow

2. **Phase 2: Scheduler Implementation (Week 2-3)**
   - Develop and test scheduling system for channel polling
   - Implement subscription renewal logic
   - Set up environment-specific scheduling (dev/prod)

3. **Phase 3: Queue and Pipeline Integration (Week 3-4)**
   - Create processing queue infrastructure
   - Connect notification systems to the queue
   - Modify existing pipeline to work with queue-based processing

4. **Phase 4: Quota Management and Monitoring (Week 4-5)**
   - Implement quota tracking and alerting
   - Create dashboard for system monitoring
   - Test failover scenarios

5. **Phase 5: Testing and Optimization (Week 5-6)**
   - End-to-end system testing
   - Load testing with simulated video streams
   - Optimization based on real-world quota usage

## Conclusion

This hybrid WebSub-polling approach provides a robust solution for monitoring YouTube channels for Trump's speeches and statements. By leveraging WebSub for real-time updates and using efficient API polling as a fallback, we can ensure comprehensive coverage while maintaining YouTube API quota compliance.

The implementation balances several key factors:
- Near real-time updates for new content
- Minimal API quota usage
- Fault tolerance with fallback systems
- Scalability for monitoring multiple channels
- Compliance with YouTube's Terms of Service

This solution will integrate seamlessly with our existing pipeline components, allowing us to process, analyze, and serve Trump's speeches to users through our archive interface.