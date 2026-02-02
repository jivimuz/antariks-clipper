#!/usr/bin/env python3
"""
Test script for YouTube download with specific video
Tests: https://www.youtube.com/watch?v=NEcbdGkJgcA
"""
import sys
import logging
from pathlib import Path
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.downloader import download_youtube, get_video_info, check_dependencies

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_download():
    """Test download with the specified video"""
    
    # Test video URL
    test_url = "https://www.youtube.com/watch?v=NEcbdGkJgcA"
    
    logger.info("="*80)
    logger.info("YouTube Download Test")
    logger.info("="*80)
    logger.info(f"Testing with video: {test_url}")
    logger.info("")
    
    # Check dependencies
    logger.info("Step 1: Checking dependencies...")
    deps_ok, missing, versions = check_dependencies()
    if not deps_ok:
        logger.error(f"Missing dependencies: {missing}")
        return False
    logger.info(f"✓ Dependencies OK: yt-dlp={versions.get('yt-dlp')}, ffmpeg={versions.get('ffmpeg')}")
    logger.info("")
    
    # Get video info first
    logger.info("Step 2: Fetching video information...")
    video_info = get_video_info(test_url)
    if video_info:
        logger.info(f"✓ Video Title: {video_info.get('title', 'Unknown')}")
        duration = video_info.get('duration', 0)
        logger.info(f"✓ Duration: {duration}s ({duration//60}m {duration%60}s)")
        logger.info(f"✓ Uploader: {video_info.get('uploader', 'Unknown')}")
        logger.info(f"✓ View count: {video_info.get('view_count', 'Unknown')}")
    else:
        logger.warning("Could not fetch video info, but will try download anyway")
    logger.info("")
    
    # Prepare output
    output_dir = Path("/tmp/antariks_test")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "test_video.mp4"
    
    # Remove existing file
    if output_path.exists():
        output_path.unlink()
        logger.info(f"Removed existing test file")
    
    # Progress callback
    last_percent = 0
    def progress_callback(percent, message):
        nonlocal last_percent
        if percent != last_percent or percent == 0 or percent == 100:
            logger.info(f"Progress: {percent}% - {message}")
            last_percent = percent
    
    # Download
    logger.info("Step 3: Starting download...")
    logger.info(f"Output path: {output_path}")
    logger.info("")
    
    start_time = time.time()
    success, error = download_youtube(
        url=test_url,
        output_path=output_path,
        progress_callback=progress_callback
    )
    elapsed = time.time() - start_time
    
    logger.info("")
    logger.info("="*80)
    logger.info("Test Results")
    logger.info("="*80)
    logger.info(f"Download time: {elapsed:.1f}s ({elapsed/60:.1f}m)")
    
    if success:
        file_size = output_path.stat().st_size
        logger.info(f"✓ SUCCESS: File downloaded and validated")
        logger.info(f"✓ File size: {file_size / 1024 / 1024:.2f} MB ({file_size:,} bytes)")
        logger.info(f"✓ File path: {output_path}")
        
        # Additional validation
        if file_size == 0:
            logger.error("❌ FAILURE: File is empty!")
            return False
        elif file_size < 100000:  # Less than 100KB
            logger.warning(f"⚠ WARNING: File seems too small ({file_size} bytes)")
        
        logger.info("")
        logger.info("✓ All tests passed!")
        return True
    else:
        logger.error(f"❌ FAILURE: Download failed")
        logger.error(f"Error: {error}")
        return False

if __name__ == "__main__":
    try:
        success = test_download()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        sys.exit(1)
