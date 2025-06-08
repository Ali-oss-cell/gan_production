import threading
import time
import queue
import logging
import os
import platform
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor, TimeoutError

logger = logging.getLogger(__name__)

# Configure the maximum number of concurrent video processing tasks
MAX_CONCURRENT_TASKS = getattr(settings, 'MAX_VIDEO_PROCESSING_TASKS', 2)
PROCESSING_TIMEOUT = getattr(settings, 'VIDEO_PROCESSING_TIMEOUT', 600)  # Default 10 minutes

# Queue for video processing tasks
processing_queue = queue.Queue()

# Track active processing tasks
active_tasks = 0
queue_lock = threading.Lock()

class VideoProcessingTask:
    """Represents a video processing task in the queue"""
    
    def __init__(self, video_id, callback=None):
        self.video_id = video_id
        self.callback = callback
        self.status = 'queued'
        self.error = None
        self.result = None
        
    def mark_complete(self, result=None):
        """Mark the task as complete with optional result"""
        self.status = 'completed'
        self.result = result
        if self.callback:
            try:
                self.callback(self)
            except Exception as e:
                logger.error(f"Error in callback for video {self.video_id}: {str(e)}")
                
    def mark_failed(self, error):
        """Mark the task as failed with error information"""
        self.status = 'failed'
        self.error = str(error)
        if self.callback:
            try:
                self.callback(self)
            except Exception as e:
                logger.error(f"Error in callback for video {self.video_id}: {str(e)}")


def process_queue_worker():
    """Worker thread that processes the video queue"""
    global active_tasks
    
    while True:
        try:
            # Get the next task from the queue
            task = processing_queue.get(block=True, timeout=5)
            
            with queue_lock:
                active_tasks += 1
                
            try:
                # Process the video using MediaProcessor
                logger.info(f"Processing video {task.video_id}")
                
                # Get the TalentMedia instance
                from profiles.models import TalentMedia
                video = TalentMedia.objects.get(id=task.video_id)
                
                # Process the video - handle both local and S3 storage
                from profiles.utils.media_processor import MediaProcessor
                import tempfile
                from django.core.files.storage import default_storage
                
                # Create a temporary file to store the video
                temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                temp_file.close()
                
                # Download the file from storage (works with both local and S3)
                with default_storage.open(video.media_file.name) as source_file:
                    with open(temp_file.name, 'wb') as dest_file:
                        dest_file.write(source_file.read())
                
                # Process the video with timeout protection using ThreadPoolExecutor
                # This is a cross-platform solution that works on both Windows and Unix
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(MediaProcessor.process_video, temp_file.name)
                    try:
                        # Wait for the result with a timeout
                        processed_path = future.result(timeout=PROCESSING_TIMEOUT)
                    except TimeoutError:
                        # Cancel the future if possible
                        future.cancel()
                        error_msg = f"Video processing timed out after {PROCESSING_TIMEOUT} seconds"
                        logger.error(f"Timeout processing video {task.video_id}: {error_msg}")
                        task.mark_failed(error_msg)
                        # Clean up and return early
                        if os.path.exists(temp_file.name):
                            os.unlink(temp_file.name)
                        continue
                
                # Clean up the temporary file
                import os
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                
                # Mark task as complete with the processed file path
                task.mark_complete(processed_path)
                
            except Exception as e:
                logger.error(f"Error processing video {task.video_id}: {str(e)}")
                task.mark_failed(e)
                
            finally:
                with queue_lock:
                    active_tasks -= 1
                processing_queue.task_done()
                
        except queue.Empty:
            # No tasks in queue, continue waiting
            continue
        except Exception as e:
            logger.error(f"Unexpected error in queue worker: {str(e)}")
            time.sleep(5)  # Prevent tight loop in case of recurring errors


def enqueue_video_processing(video_id, callback=None):
    """Add a video to the processing queue
    
    Args:
        video_id: ID of the video to process
        callback: Optional function to call when processing completes
        
    Returns:
        VideoProcessingTask: The queued task object
    """
    task = VideoProcessingTask(video_id, callback)
    processing_queue.put(task)
    logger.info(f"Video {video_id} added to processing queue. Current queue size: {processing_queue.qsize()}")
    return task


def get_queue_status():
    """Get the current status of the processing queue
    
    Returns:
        dict: Queue status information
    """
    with queue_lock:
        return {
            'queue_size': processing_queue.qsize(),
            'active_tasks': active_tasks,
            'max_concurrent': MAX_CONCURRENT_TASKS
        }


# Start worker threads when module is imported
def start_workers():
    """Start the worker threads for video processing"""
    for i in range(MAX_CONCURRENT_TASKS):
        worker = threading.Thread(
            target=process_queue_worker,
            name=f"VideoProcessingWorker-{i}",
            daemon=True
        )
        worker.start()
        logger.info(f"Started video processing worker {i}")


# Initialize workers when Django starts
start_workers()