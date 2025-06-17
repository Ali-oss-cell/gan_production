# Video Processing System

This document explains the video processing system implemented for the Talent Platform application. The system compresses all videos to 720p resolution and stores them in DigitalOcean Spaces (S3-compatible storage).

## Features

- All videos are compressed to 720p resolution (1280x720)
- Optimized bitrate settings for web streaming (1500k)
- Asynchronous processing queue to prevent server overload
- Automatic thumbnail generation
- Storage in DigitalOcean Spaces (S3-compatible)

## Server Requirements

The current implementation is designed to work on a DigitalOcean Droplet with the following specifications:
- 2 vCPU
- 2GB RAM
- 60GB SSD

This configuration should be sufficient for moderate video processing loads, but may struggle with concurrent processing of multiple large videos. The queue system helps manage this by limiting concurrent processing tasks.

## Configuration

### Environment Variables

Add the following environment variables to your `.env` file:

```
# DigitalOcean Spaces Configuration
USE_SPACES=True
SPACES_ACCESS_KEY=your_access_key
SPACES_SECRET_KEY=your_secret_key
SPACES_BUCKET_NAME=your_bucket_name
SPACES_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com  # Change region if needed

# Video Processing Settings
MAX_VIDEO_PROCESSING_TASKS=2  # Adjust based on server capacity
VIDEO_PROCESSING_TIMEOUT=600  # Maximum time in seconds for processing a video
```

### Video Processing Queue

The video processing queue system limits the number of concurrent video processing tasks to prevent server overload. You can adjust the following settings in `settings.py`:

```python
# Video processing settings
MAX_VIDEO_PROCESSING_TASKS = 2  # Maximum concurrent video processing tasks
VIDEO_PROCESSING_TIMEOUT = 600  # Maximum time in seconds for processing a video
```

## How It Works

1. When a user uploads a video, it is saved to the database with the original file.
2. A post-save signal handler adds the video to the processing queue.
3. Worker threads process videos from the queue, limiting concurrent processing to prevent server overload.
4. Each video is compressed to 720p resolution using FFmpeg.
5. A thumbnail is generated for the video.
6. The processed video and thumbnail are saved to DigitalOcean Spaces.
7. The original video file is replaced with the processed version.

## Dependencies

- FFmpeg: Required for video processing and thumbnail generation
- boto3: Python SDK for AWS services (used for S3-compatible storage)
- django-storages: Django storage backend for S3

## Monitoring

You can monitor the video processing queue by checking the logs. The system logs information about queue status, processing start/completion, and any errors that occur.

## Troubleshooting

### Common Issues

1. **Videos not being processed**: Check that FFmpeg is installed and available in the system PATH.
2. **Storage errors**: Verify your DigitalOcean Spaces credentials and bucket configuration.
3. **Server overload**: If the server is struggling, reduce the `MAX_VIDEO_PROCESSING_TASKS` setting.

### Logs

Check the application logs for errors related to video processing. The system logs detailed information about each step of the process.