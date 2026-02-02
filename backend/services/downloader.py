"""Download service for YouTube videos and handle uploads"""
import subprocess
import logging
import shutil
import os
import re
from pathlib import Path
from typing import Optional, Tuple, Callable

logger = logging.getLogger(__name__)

def check_dependencies() -> Tuple[bool, list, dict]:
    """Check if required dependencies are installed and get versions"""
    missing = []
    versions = {}
    
    # Check ffmpeg
    if not shutil.which('ffmpeg'):
        missing.append('ffmpeg')
    else:
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
            match = re.search(r'ffmpeg version (\S+)', result.stdout)
            versions['ffmpeg'] = match.group(1) if match else 'unknown'
        except Exception as e:
            logger.debug(f"Could not get ffmpeg version: {e}")
            versions['ffmpeg'] = 'unknown'
    
    # Check yt-dlp
    if not shutil.which('yt-dlp'):
        missing.append('yt-dlp')
    else:
        try:
            result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=10)
            versions['yt-dlp'] = result.stdout.strip()
        except Exception as e:
            logger.debug(f"Could not get yt-dlp version: {e}")
            versions['yt-dlp'] = 'unknown'
    
    return len(missing) == 0, missing, versions

def validate_youtube_url(url: str) -> bool:
    """Validate YouTube URL format"""
    patterns = [
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://youtu\.be/[\w-]+',
        r'^https?://(www\.)?youtube\.com/shorts/[\w-]+',
        r'^https?://(www\.)?youtube\.com/live/[\w-]+',
    ]
    return any(re.match(p, url) for p in patterns)

def download_youtube(
    url: str, 
    output_path: Path,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    cookies_file: Optional[Path] = None
) -> Tuple[bool, Optional[str]]:
    """
    Download YouTube video using yt-dlp with robust fallback options
    
    Args:
        url: YouTube URL
        output_path: Output file path (should end with .mp4)
        progress_callback: Optional callback(percent, status_message)
        cookies_file: Optional path to cookies.txt for authenticated downloads
    
    Returns:
        (success, error_message)
    """
    try:
        # Validate URL
        if not validate_youtube_url(url):
            logger.error(f"Invalid YouTube URL: {url}")
            return False, "Invalid YouTube URL"
        
        # Check dependencies
        deps_ok, missing, versions = check_dependencies()
        if not deps_ok:
            logger.error(f"Missing dependencies: {', '.join(missing)}. Please install them first.")
            logger.error("Install with: pip install yt-dlp (or brew install yt-dlp)")
            return False, f"Missing dependencies: {', '.join(missing)}"
        
        logger.info(f"Dependencies OK - yt-dlp: {versions.get('yt-dlp')}, ffmpeg: {versions.get('ffmpeg')}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean output path - ensure it ends with .mp4
        if output_path.suffix != '.mp4':
            output_path = output_path.with_suffix('.mp4')
        
        # Remove existing file if any
        if output_path.exists():
            output_path.unlink()
        
        # yt-dlp output template (without extension, yt-dlp adds it)
        output_template = str(output_path.with_suffix(''))
        
        # Build command with latest recommended options for YouTube 2024+
        cmd = [
            'yt-dlp',
            '--no-warnings',
            '--no-check-certificate',
            # Format: allow any best available, merge to mp4
            '-f', 'bestvideo+bestaudio/best',
            '--merge-output-format', 'mp4',
            '--format-sort', 'res,ext:mp4:m4a',
            # Use multiple clients for better compatibility
            '--extractor-args', 'youtube:player_client=ios,web',
            # Retry settings
            '--retries', '10',
            '--fragment-retries', '10',
            '--retry-sleep', '3',
            # Skip unavailable fragments instead of failing
            '--skip-unavailable-fragments',
            # Output
            '-o', f'{output_template}.%(ext)s',
            # Progress
            '--newline',
            '--progress-template', '%(progress._percent_str)s',
        ]
        
        # Add cookies if provided
        if cookies_file and cookies_file.exists():
            cmd.extend(['--cookies', str(cookies_file)])
            logger.info("Using cookies file for authentication")
        
        # Add URL
        cmd.append(url)
        
        logger.info(f"Downloading: {url}")
        logger.debug(f"Command: {' '.join(cmd)}")
        
        if progress_callback:
            progress_callback(0, "Starting download...")
        
        # Run with live output for progress
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        last_percent = 0
        stdout_lines = []
        
        for line in process.stdout:
            line = line.strip()
            stdout_lines.append(line)
            
            # Parse progress
            if '%' in line:
                try:
                    percent_str = line.replace('%', '').strip()
                    percent = int(float(percent_str))
                    if percent != last_percent and progress_callback:
                        progress_callback(percent, f"Downloading... {percent}%")
                        last_percent = percent
                except (ValueError, TypeError):
                    # Ignore lines that don't contain valid progress percentages
                    pass
        
        stderr = process.stderr.read()
        process.wait()
        
        if process.returncode != 0:
            logger.error(f"yt-dlp failed (code {process.returncode})")
            logger.error(f"stderr: {stderr}")
            
            # Try fallback method
            return _download_fallback(url, output_path, cookies_file, progress_callback)
        
        # Verify file exists
        if output_path.exists():
            file_size = output_path.stat().st_size
            logger.info(f"Download complete: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
            if progress_callback:
                progress_callback(100, "Download complete!")
            return True, None
        
        # Check if file with different extension exists
        for ext in ['.mp4', '.mkv', '.webm']:
            alt_path = output_path.with_suffix(ext)
            if alt_path.exists():
                if ext != '.mp4':
                    # Convert to mp4
                    if _convert_to_mp4(alt_path, output_path):
                        alt_path.unlink()
                        return True, None
                else:
                    return True, None
        
        logger.error(f"Download completed but output file not found: {output_path}")
        return False, "Download completed but output file not found"
        
    except subprocess.TimeoutExpired:
        logger.error("Download timeout")
        return False, "Download timeout"
    except Exception as e:
        logger.error(f"Download error: {e}", exc_info=True)
        return False, f"Download error: {str(e)}"

def _download_fallback(
    url: str, 
    output_path: Path,
    cookies_file: Optional[Path] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Tuple[bool, Optional[str]]:
    """Fallback download method with simpler options"""
    logger.info("Trying fallback download method...")
    
    if progress_callback:
        progress_callback(0, "Retrying with fallback method...")
    
    output_template = str(output_path.with_suffix(''))
    
    # Simpler command for fallback
    cmd = [
        'yt-dlp',
        '-f', 'best',
        '--no-warnings',
        '--no-check-certificate',
        '--extractor-args', 'youtube:player_client=android',
        '-o', f'{output_template}.%(ext)s',
        '--retries', '5',
    ]
    
    if cookies_file and cookies_file.exists():
        cmd.extend(['--cookies', str(cookies_file)])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0 and output_path.exists():
            logger.info("Fallback download successful")
            if progress_callback:
                progress_callback(100, "Download complete (fallback)")
            return True, None
        
        # Check for file with different extension
        for ext in ['.mp4', '.mkv', '.webm']:
            alt_path = output_path.with_suffix(ext)
            if alt_path.exists():
                if ext != '.mp4':
                    if _convert_to_mp4(alt_path, output_path):
                        alt_path.unlink()
                        return True, None
                else:
                    return True, None
        
        logger.error(f"Fallback also failed: {result.stderr}")
        return False, f"Fallback download failed: {result.stderr.strip()}"
        
    except Exception as e:
        logger.error(f"Fallback error: {e}")
        return False, f"Fallback error: {str(e)}"

def _convert_to_mp4(input_path: Path, output_path: Path) -> bool:
    """Convert video to mp4 using ffmpeg"""
    try:
        logger.info(f"Converting {input_path.suffix} to mp4...")
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',
            str(output_path)
        ]
        # 30 minute timeout for large video files (HD/4K content)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        
        if result.returncode == 0 and output_path.exists():
            logger.info(f"Conversion successful: {output_path}")
            return True
        
        logger.error(f"Conversion failed: {result.stderr}")
        return False
        
    except Exception as e:
        logger.error(f"Convert error: {e}")
        return False

def get_video_info(url: str) -> Optional[dict]:
    """Get video info without downloading"""
    try:
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--no-download',
            '--no-warnings',
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
        return None
        
    except Exception as e:
        logger.error(f"Get video info error: {e}")
        return None

def save_upload(file_data: bytes, output_path: Path) -> bool:
    """Save uploaded file"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(file_data)
        
        file_size = output_path.stat().st_size
        logger.info(f"Saved upload: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
        return True
        
    except Exception as e:
        logger.error(f"Save upload error: {e}")
        return False
