"""Download service for YouTube videos and handle uploads"""
import subprocess
import logging
import shutil
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def check_dependencies() -> Tuple[bool, list]:
    """Check if required dependencies are installed"""
    missing = []
    
    # Check ffmpeg
    if not shutil.which('ffmpeg'):
        missing.append('ffmpeg')
    
    # Check yt-dlp
    if not shutil.which('yt-dlp'):
        missing.append('yt-dlp')
    
    return len(missing) == 0, missing

def download_youtube(url: str, output_path: Path) -> bool:
    """Download YouTube video using yt-dlp with robust fallback options"""
    try:
        # Check dependencies first
        deps_ok, missing = check_dependencies()
        if not deps_ok:
            logger.error(f"Missing dependencies: {', '.join(missing)}. Please install them first.")
            return False
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove extension if present (yt-dlp adds it)
        output_template = str(output_path.with_suffix('')) + '.%(ext)s'
        
        cmd = [
            'yt-dlp',
            # Format selection with fallbacks
            '-f', 'bv*[ext=mp4]+ba[ext=m4a]/bv*[ext=mp4]+ba/bv+ba/b',
            # Force mp4 output
            '--merge-output-format', 'mp4',
            # Use android client to bypass SABR streaming restrictions
            '--extractor-args', 'youtube:player_client=android,web',
            # Retry options
            '--retries', '5',
            '--fragment-retries', '5',
            # Don't abort on unavailable fragments
            '--skip-unavailable-fragments',
            # Output path
            '-o', output_template,
            # Quiet progress but show errors
            '--no-warnings',
            '--progress',
            # The URL
            url
        ]
        
        logger.info(f"Downloading YouTube video: {url}")
        logger.debug(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=1800  # 30 minutes timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout
            logger.error(f"yt-dlp error: {error_msg}")
            
            # Try alternative format if first attempt fails
            logger.info("Retrying with alternative format...")
            cmd_alt = [
                'yt-dlp',
                '-f', 'best[ext=mp4]/best',
                '--extractor-args', 'youtube:player_client=android',
                '--retries', '3',
                '-o', output_template,
                url
            ]
            
            result = subprocess.run(
                cmd_alt,
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            if result.returncode != 0:
                logger.error(f"yt-dlp retry failed: {result.stderr or result.stdout}")
                return False
        
        # Check if file was created (yt-dlp might use different extension)
        expected_mp4 = output_path.with_suffix('.mp4')
        if expected_mp4.exists():
            # Rename to expected path if different
            if expected_mp4 != output_path:
                expected_mp4.rename(output_path)
            logger.info(f"Downloaded: {output_path}")
            return True
        
        # Check for any video file with the base name
        for ext in ['.mp4', '.mkv', '.webm']:
            check_path = output_path.with_suffix(ext)
            if check_path.exists():
                if check_path != output_path:
                    # Convert to mp4 if needed
                    if ext != '.mp4':
                        if convert_to_mp4(check_path, output_path):
                            check_path.unlink()
                        else:
                            logger.error(f"Failed to convert {check_path} to mp4")
                            return False
                    else:
                        check_path.rename(output_path)
                logger.info(f"Downloaded: {output_path}")
                return True
        
        logger.error(f"Download completed but file not found: {output_path}")
        return False
        
    except subprocess.TimeoutExpired:
        logger.error("Download timeout (30 minutes)")
        return False
    except Exception as e:
        logger.error(f"Download error: {e}")
        return False

def convert_to_mp4(input_path: Path, output_path: Path) -> bool:
    """Convert video to mp4 using ffmpeg"""
    try:
        logger.info(f"Converting {input_path} to mp4...")
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y',
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
            logger.info(f"Successfully converted to {output_path}")
            return True
        else:
            logger.error(f"Conversion failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Convert error: {e}")
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
