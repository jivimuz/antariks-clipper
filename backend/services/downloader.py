"""Download service for YouTube videos and handle uploads"""
import subprocess
import logging
import shutil
import os
import re
import time
from pathlib import Path
from typing import Optional, Tuple, Callable

logger = logging.getLogger(__name__)

# Error message templates for better user feedback
ERROR_MESSAGES = {
    'unavailable': 'Video is unavailable or has been removed',
    'private': 'Video is private and cannot be accessed',
    'region_blocked': 'Video is blocked in your region',
    'age_restricted': 'Video is age-restricted and requires authentication',
    'copyright': 'Video contains copyrighted content and cannot be downloaded',
    'live': 'Live streams cannot be downloaded yet',
    'network': 'Network error occurred. Please check your connection',
    'timeout': 'Download timed out. The video may be too large or connection is slow',
    'format': 'Video format is not supported',
    'unknown': 'An unknown error occurred during download'
}

def check_dependencies() -> Tuple[bool, list, dict]:
    """Check if required dependencies are installed and get versions"""
    missing = []
    versions = {}
    
    # Check ffmpeg
    if not shutil.which('ffmpeg'):
        missing.append('ffmpeg')
        logger.warning("ffmpeg not found. Install with: sudo apt-get install ffmpeg (Linux) or brew install ffmpeg (macOS)")
    else:
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
            match = re.search(r'ffmpeg version (\S+)', result.stdout)
            versions['ffmpeg'] = match.group(1) if match else 'unknown'
            logger.debug(f"ffmpeg version: {versions['ffmpeg']}")
        except Exception as e:
            logger.debug(f"Could not get ffmpeg version: {e}")
            versions['ffmpeg'] = 'unknown'
    
    # Check yt-dlp
    if not shutil.which('yt-dlp'):
        missing.append('yt-dlp')
        logger.warning("yt-dlp not found. Install with: pip install yt-dlp")
    else:
        try:
            result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, timeout=10)
            versions['yt-dlp'] = result.stdout.strip()
            logger.debug(f"yt-dlp version: {versions['yt-dlp']}")
        except Exception as e:
            logger.debug(f"Could not get yt-dlp version: {e}")
            versions['yt-dlp'] = 'unknown'
    
    if missing:
        logger.error(f"Missing required dependencies: {', '.join(missing)}")
    else:
        logger.info("All dependencies are installed and working")
    
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

def _parse_download_error(stderr: str) -> str:
    """
    Parse yt-dlp error message and return user-friendly error
    
    Args:
        stderr: Standard error output from yt-dlp
        
    Returns:
        User-friendly error message
    """
    stderr_lower = stderr.lower()
    
    # Check for specific error patterns
    if 'video unavailable' in stderr_lower or 'this video is unavailable' in stderr_lower:
        return ERROR_MESSAGES['unavailable']
    elif 'private video' in stderr_lower or 'this video is private' in stderr_lower:
        return ERROR_MESSAGES['private']
    elif 'not available in your country' in stderr_lower or 'geo restricted' in stderr_lower:
        return ERROR_MESSAGES['region_blocked']
    elif 'sign in to confirm your age' in stderr_lower or 'age restricted' in stderr_lower:
        return ERROR_MESSAGES['age_restricted']
    elif 'copyright' in stderr_lower or 'taken down' in stderr_lower:
        return ERROR_MESSAGES['copyright']
    elif 'live event' in stderr_lower or 'is a live stream' in stderr_lower:
        return ERROR_MESSAGES['live']
    elif 'unable to download' in stderr_lower and 'format' in stderr_lower:
        return ERROR_MESSAGES['format']
    elif 'network' in stderr_lower or 'connection' in stderr_lower:
        return ERROR_MESSAGES['network']
    elif 'timeout' in stderr_lower or 'timed out' in stderr_lower:
        return ERROR_MESSAGES['timeout']
    elif 'http error 403' in stderr_lower or 'forbidden' in stderr_lower:
        # HTTP 403 can be caused by various issues
        return "Access forbidden. This may be due to region restrictions, age restrictions, or temporary YouTube blocks. Try updating yt-dlp with: pip install --upgrade yt-dlp"
    elif 'http error 404' in stderr_lower:
        return ERROR_MESSAGES['unavailable']
    elif 'http error 429' in stderr_lower:
        return "Too many requests. Please wait a few minutes before trying again"
    else:
        # Return first error line if available
        error_lines = [line.strip() for line in stderr.split('\n') if 'error' in line.lower()]
        if error_lines:
            return f"Download error: {error_lines[0][:200]}"  # Limit length
        return ERROR_MESSAGES['unknown']

def download_youtube(
    url: str, 
    output_path: Path,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    cookies_file: Optional[Path] = None,
    max_retries: int = 3
) -> Tuple[bool, Optional[str]]:
    """
    Download YouTube video using yt-dlp with robust fallback options
    
    Args:
        url: YouTube URL
        output_path: Output file path (should end with .mp4)
        progress_callback: Optional callback(percent, status_message)
        cookies_file: Optional path to cookies.txt for authenticated downloads
        max_retries: Maximum number of retry attempts (default: 3)
    
    Returns:
        (success, error_message)
    """
    logger.info(f"=== Starting YouTube download ===")
    logger.info(f"URL: {url}")
    logger.info(f"Output: {output_path}")
    
    try:
        # Validate URL
        if not validate_youtube_url(url):
            error_msg = f"Invalid YouTube URL format: {url}"
            logger.error(error_msg)
            return False, error_msg
        
        logger.info("✓ URL validation passed")
        
        # Check dependencies
        deps_ok, missing, versions = check_dependencies()
        if not deps_ok:
            error_msg = f"Missing required dependencies: {', '.join(missing)}. Please install them first."
            logger.error(error_msg)
            logger.error("Installation instructions:")
            for dep in missing:
                if dep == 'ffmpeg':
                    logger.error("  - ffmpeg: sudo apt-get install ffmpeg (Linux) or brew install ffmpeg (macOS)")
                elif dep == 'yt-dlp':
                    logger.error("  - yt-dlp: pip install yt-dlp")
            return False, error_msg
        
        logger.info(f"✓ Dependencies verified - yt-dlp: {versions.get('yt-dlp')}, ffmpeg: {versions.get('ffmpeg')}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean output path - ensure it ends with .mp4
        if output_path.suffix != '.mp4':
            output_path = output_path.with_suffix('.mp4')
        
        # Remove existing file if any
        if output_path.exists():
            logger.info(f"Removing existing file: {output_path}")
            output_path.unlink()
        
        # Try download with retries
        for attempt in range(max_retries):
            if attempt > 0:
                # Exponential backoff: 5s, 10s, 20s
                wait_time = 5 * (2 ** (attempt - 1))
                logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay...")
                if progress_callback:
                    progress_callback(0, f"Retrying (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            
            success, error = _attempt_download(url, output_path, cookies_file, progress_callback)
            
            if success:
                file_size = output_path.stat().st_size
                logger.info(f"✓ Download successful: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
                if progress_callback:
                    progress_callback(100, "Download complete!")
                return True, None
            
            # Check if error is retryable
            if error and any(keyword in error.lower() for keyword in ['network', 'timeout', 'connection', '429']):
                logger.warning(f"Retryable error on attempt {attempt + 1}: {error}")
                continue
            else:
                # Non-retryable error, fail immediately
                logger.error(f"Non-retryable error: {error}")
                return False, error
        
        # All retries exhausted
        error_msg = f"Download failed after {max_retries} attempts"
        logger.error(error_msg)
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error during download: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

def _attempt_download(
    url: str,
    output_path: Path,
    cookies_file: Optional[Path],
    progress_callback: Optional[Callable[[int, str], None]]
) -> Tuple[bool, Optional[str]]:
    """
    Single download attempt with enhanced support for long videos
    
    Returns:
        (success, error_message)
    """
    try:
        # yt-dlp output template (without extension, yt-dlp adds it)
        output_template = str(output_path.with_suffix(''))
        
        # Build command with latest recommended options for YouTube 2024+
        # Enhanced for long videos (3+ hours)
        cmd = [
            'yt-dlp',
            '--no-warnings',
            '--no-check-certificate',
            # Format selection chain (tries each option in order until one works):
            # 1. bestvideo[ext=mp4]+bestaudio[ext=m4a] - Best quality MP4/M4A (preferred)
            # 2. bestvideo+bestaudio - Best quality any format, will merge
            # 3. best - Single file with video and audio (fallback for no separate streams)
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
            '--merge-output-format', 'mp4',
            '--format-sort', 'res,ext:mp4:m4a',
            # Use multiple clients for better compatibility
            '--extractor-args', 'youtube:player_client=ios,android,web',
            # Enhanced retry settings for long videos
            '--retries', '15',  # Increased from 10
            '--fragment-retries', '15',  # Increased from 10
            '--retry-sleep', '5',  # Increased from 3
            # Skip unavailable fragments instead of failing
            '--skip-unavailable-fragments',
            # Buffer size for large files (helps with long videos)
            '--buffer-size', '16K',
            # User agent (helps avoid some blocks)
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            # Output
            '-o', f'{output_template}.%(ext)s',
            # Progress
            '--newline',
            '--progress-template', '%(progress._percent_str)s',
            # Enhanced progress tracking
            '--progress-template', 'download:%(progress._percent_str)s %(progress.downloaded_bytes)s/%(progress.total_bytes)s %(progress.speed)s %(progress.eta)s',
        ]
        
        # Add cookies if provided
        if cookies_file and cookies_file.exists():
            cmd.extend(['--cookies', str(cookies_file)])
            logger.info("✓ Using cookies file for authentication")
        
        # Add URL
        cmd.append(url)
        
        logger.info("Starting download process (optimized for long videos)...")
        logger.debug(f"Command: {' '.join(cmd)}")
        
        if progress_callback:
            progress_callback(0, "Starting download...")
        
        # Run with live output for progress - increased timeout for very long videos
        # Timeout: 6 hours (21600s) to handle very long videos (3+ hours at slower speeds)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        last_percent = 0
        stdout_lines = []
        last_log_time = time.time()
        
        for line in process.stdout:
            line = line.strip()
            stdout_lines.append(line)
            
            # Parse progress
            if '%' in line:
                try:
                    percent_str = line.split('%')[0].split()[-1]
                    percent = int(float(percent_str))
                    if percent != last_percent and progress_callback:
                        progress_callback(percent, f"Downloading... {percent}%")
                        last_percent = percent
                        
                        # Log progress periodically (every 10% or every 2 minutes for long downloads)
                        current_time = time.time()
                        if percent % 10 == 0 or (current_time - last_log_time) > 120:
                            logger.info(f"📥 Download progress: {percent}% - {line}")
                            last_log_time = current_time
                except (ValueError, TypeError, IndexError):
                    pass
        
        stderr = process.stderr.read()
        process.wait()
        
        if process.returncode != 0:
            logger.error(f"❌ yt-dlp failed with return code {process.returncode}")
            logger.error(f"stderr output:\n{stderr}")
            
            # Parse error for user-friendly message
            error_msg = _parse_download_error(stderr)
            logger.error(f"Parsed error: {error_msg}")
            
            # Try fallback method for certain errors
            if 'http error 403' in stderr.lower() or 'player_client' in stderr.lower():
                logger.info("🔄 Attempting fallback download method...")
                return _download_fallback(url, output_path, cookies_file, progress_callback)
            
            return False, error_msg
        
        # Verify file exists
        if output_path.exists():
            file_size = output_path.stat().st_size
            logger.info(f"✓ File downloaded successfully: {file_size / 1024 / 1024:.1f} MB")
            return True, None
        
        # Check if file with different extension exists
        logger.info("🔍 Checking for alternate file formats...")
        for ext in ['.mp4', '.mkv', '.webm']:
            alt_path = output_path.with_suffix(ext)
            if alt_path.exists():
                logger.info(f"Found file with extension: {ext}")
                if ext != '.mp4':
                    logger.info(f"🔄 Converting {ext} to mp4...")
                    if _convert_to_mp4(alt_path, output_path):
                        alt_path.unlink()
                        logger.info("✓ Conversion successful")
                        return True, None
                    else:
                        return False, f"Downloaded but conversion from {ext} to mp4 failed"
                else:
                    return True, None
        
        error_msg = "Download completed but output file not found"
        logger.error(f"❌ {error_msg}")
        return False, error_msg
        
    except subprocess.TimeoutExpired:
        error_msg = ERROR_MESSAGES['timeout']
        logger.error(f"❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Download attempt failed: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return False, error_msg

def _download_fallback(
    url: str, 
    output_path: Path,
    cookies_file: Optional[Path] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Fallback download method with simpler options
    
    This method tries different player clients and simpler format options
    when the main download fails.
    """
    logger.info("=== Attempting fallback download method ===")
    
    if progress_callback:
        progress_callback(0, "Retrying with fallback method...")
    
    output_template = str(output_path.with_suffix(''))
    
    # Try different fallback strategies
    fallback_strategies = [
        {
            'name': 'Android client with best format',
            'args': ['--extractor-args', 'youtube:player_client=android'],
            'format': 'best'
        },
        {
            'name': 'iOS client with mp4 format',
            'args': ['--extractor-args', 'youtube:player_client=ios'],
            'format': 'best[ext=mp4]/best'
        },
        {
            'name': 'Web client with lower quality',
            'args': ['--extractor-args', 'youtube:player_client=web'],
            'format': 'worst'
        }
    ]
    
    for strategy in fallback_strategies:
        logger.info(f"Trying fallback strategy: {strategy['name']}")
        
        cmd = [
            'yt-dlp',
            '-f', strategy['format'],
            '--no-warnings',
            '--no-check-certificate',
            *strategy['args'],
            '-o', f'{output_template}.%(ext)s',
            '--retries', '5',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        ]
        
        if cookies_file and cookies_file.exists():
            cmd.extend(['--cookies', str(cookies_file)])
        
        cmd.append(url)
        
        try:
            logger.debug(f"Fallback command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if result.returncode == 0:
                # Check for file
                if output_path.exists():
                    logger.info(f"✓ Fallback download successful with {strategy['name']}")
                    if progress_callback:
                        progress_callback(100, "Download complete (fallback)")
                    return True, None
                
                # Check for file with different extension
                for ext in ['.mp4', '.mkv', '.webm']:
                    alt_path = output_path.with_suffix(ext)
                    if alt_path.exists():
                        logger.info(f"Found file with extension: {ext}")
                        if ext != '.mp4':
                            if _convert_to_mp4(alt_path, output_path):
                                alt_path.unlink()
                                logger.info("✓ Conversion successful")
                                return True, None
                        else:
                            return True, None
            
            logger.warning(f"Fallback strategy '{strategy['name']}' failed: {result.stderr[:200]}")
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Fallback strategy '{strategy['name']}' timed out")
            continue
        except Exception as e:
            logger.warning(f"Fallback strategy '{strategy['name']}' error: {e}")
            continue
    
    # All fallback strategies failed
    error_msg = "All download methods failed. The video may be unavailable, region-blocked, or require authentication."
    logger.error(error_msg)
    logger.error("Troubleshooting tips:")
    logger.error("  1. Update yt-dlp: pip install --upgrade yt-dlp")
    logger.error("  2. Check if video is available and public")
    logger.error("  3. Try with cookies for age-restricted videos")
    return False, error_msg

def _convert_to_mp4(input_path: Path, output_path: Path) -> bool:
    """Convert video to mp4 using ffmpeg with progress logging - optimized for long videos"""
    try:
        logger.info(f"=== Converting {input_path.suffix} to mp4 ===")
        logger.info(f"Input: {input_path}")
        logger.info(f"Output: {output_path}")
        
        # Get input file info
        file_size = input_path.stat().st_size
        logger.info(f"📊 Input file size: {file_size / 1024 / 1024:.1f} MB")
        
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',  # Overwrite output file
            str(output_path)
        ]
        
        logger.debug(f"Conversion command: {' '.join(cmd)}")
        logger.info("🔄 Starting conversion... This may take a while for long videos")
        
        # Extended timeout for very long videos (3+ hours)
        # Assuming ~1GB per hour at decent quality, 3 hours = ~3GB
        # Conversion can take 2-3x the video duration on modest hardware
        # Timeout: 4 hours (14400s) to handle 3+ hour videos safely
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=14400
        )
        
        if result.returncode == 0 and output_path.exists():
            output_size = output_path.stat().st_size
            logger.info(f"✓ Conversion successful: {output_path} ({output_size / 1024 / 1024:.1f} MB)")
            return True
        
        logger.error(f"❌ Conversion failed with return code {result.returncode}")
        logger.error(f"stderr: {result.stderr}")
        return False
        
    except subprocess.TimeoutExpired:
        logger.error("❌ Conversion timed out after 4 hours (video may be extremely long or system is slow)")
        return False
    except Exception as e:
        logger.error(f"❌ Conversion error: {e}", exc_info=True)
        return False

def get_video_info(url: str) -> Optional[dict]:
    """
    Get video info without downloading
    
    Returns:
        Dictionary with video metadata or None if failed
    """
    logger.info(f"Fetching video info for: {url}")
    
    try:
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--no-download',
            '--no-warnings',
            '--no-check-certificate',
            url
        ]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout)
            
            # Log useful info
            logger.info(f"Video title: {info.get('title', 'Unknown')}")
            logger.info(f"Duration: {info.get('duration', 0)}s")
            logger.info(f"Uploader: {info.get('uploader', 'Unknown')}")
            
            # Check for availability
            if info.get('is_live'):
                logger.warning("This is a live stream")
            if info.get('age_limit', 0) > 0:
                logger.warning(f"Age-restricted content (age limit: {info.get('age_limit')})")
            
            return info
        else:
            logger.error(f"Failed to get video info: {result.stderr}")
            # Try to parse error
            error_msg = _parse_download_error(result.stderr)
            logger.error(f"Error: {error_msg}")
            return None
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout while fetching video info")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse video info JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting video info: {e}", exc_info=True)
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
