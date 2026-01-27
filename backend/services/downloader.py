"""Download service for YouTube videos and handle uploads"""
import subprocess
import logging
from pathlib import Path
from typing import Optional
import shutil

logger = logging.getLogger(__name__)

def download_youtube(url: str, output_path: Path) -> bool:
    """Download YouTube video using yt-dlp"""
    try:
        cmd = [
            'yt-dlp',
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '--merge-output-format', 'mp4',
            '-o', str(output_path),
            url
        ]
        
        logger.info(f"Downloading YouTube video: {url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            logger.error(f"yt-dlp error: {result.stderr}")
            return False
            
        logger.info(f"Downloaded: {output_path}")
        return output_path.exists()
        
    except subprocess.TimeoutExpired:
        logger.error("Download timeout")
        return False
    except Exception as e:
        logger.error(f"Download error: {e}")
        return False

def save_upload(file_data: bytes, output_path: Path) -> bool:
    """Save uploaded file"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(file_data)
        logger.info(f"Saved upload: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Save upload error: {e}")
        return False
