"""Thumbnail generation service"""
import logging
from pathlib import Path
from services.ffmpeg import extract_thumbnail

logger = logging.getLogger(__name__)

def generate_thumbnail(video_path: Path, timestamp: float, output_path: Path) -> bool:
    """Generate thumbnail at mid-point of clip"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return extract_thumbnail(video_path, timestamp, output_path)
    except Exception as e:
        logger.error(f"Thumbnail generation error: {e}")
        return False
