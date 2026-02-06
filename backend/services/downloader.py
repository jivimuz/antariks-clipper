"""Download service for YouTube videos and handle uploads"""
import subprocess
import logging
import shutil
import os
import sys
import re
import time
from pathlib import Path
from typing import Optional, Tuple, Callable
from utils import get_subprocess_startup_info, get_subprocess_creation_flags

logger = logging.getLogger(__name__)

# Error message templates for better user feedback
ERROR_MESSAGES = {
    'unavailable': 'Video is unavailable or has been removed',
    'private': 'Video is private and cannot be accessed',
    'region_blocked': 'Video is blocked in your region due to geographical restrictions',
    'age_restricted': 'Video is age-restricted and requires authentication',
    'copyright': 'Video contains copyrighted content and cannot be downloaded',
    'live': 'Live streams cannot be downloaded yet',
    'network': 'Network error occurred. Please check your connection',
    'timeout': 'Download timed out. The video may be too large or connection is slow',
    'format': 'Video format is not supported or no suitable format available',
    'drm': 'Video is protected by DRM (Digital Rights Management) and cannot be downloaded',
    'api_block': 'YouTube API access blocked. This may be temporary rate limiting or IP-based restriction',
    'quota_exceeded': 'YouTube API quota exceeded. Please try again later',
    'bot_detected': 'YouTube detected automated access. Try updating yt-dlp or use cookies for authentication',
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
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                capture_output=True, 
                text=True, 
                timeout=10,
                startupinfo=get_subprocess_startup_info(),
                creationflags=get_subprocess_creation_flags()
            )
            match = re.search(r'ffmpeg version (\S+)', result.stdout)
            versions['ffmpeg'] = match.group(1) if match else 'unknown'
            logger.debug(f"ffmpeg version: {versions['ffmpeg']}")
        except Exception as e:
            logger.debug(f"Could not get ffmpeg version: {e}")
            versions['ffmpeg'] = 'unknown'
    
    # Check yt-dlp - try both PATH and Python scripts directory
    ytdlp_cmd = shutil.which('yt-dlp')
    
    # Fallback: try finding in Python scripts directory
    if not ytdlp_cmd and sys.platform == 'win32':
        import site
        scripts_dir = site.USER_BASE + '\\Scripts' if hasattr(site, 'USER_BASE') else None
        if scripts_dir:
            ytdlp_exe = Path(scripts_dir) / 'yt-dlp.exe'
            if ytdlp_exe.exists():
                ytdlp_cmd = str(ytdlp_exe)
                logger.info(f"Found yt-dlp in Python scripts: {ytdlp_cmd}")
    
    if not ytdlp_cmd:
        missing.append('yt-dlp')
        logger.warning("yt-dlp not found. Install with: pip install yt-dlp")
    else:
        try:
            result = subprocess.run(
                [ytdlp_cmd, '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10,
                startupinfo=get_subprocess_startup_info(),
                creationflags=get_subprocess_creation_flags()
            )
            versions['yt-dlp'] = result.stdout.strip()
            logger.debug(f"yt-dlp version: {versions['yt-dlp']}")
            
            # Check if yt-dlp is outdated (simple version check)
            try:
                current_version = versions['yt-dlp']
                # Version format: YYYY.MM.DD
                if current_version and current_version != 'unknown':
                    # Extract year and month with error handling
                    version_parts = current_version.split('.')
                    if len(version_parts) >= 2:
                        try:
                            year = int(version_parts[0])
                            month = int(version_parts[1])
                            
                            # If version is older than 2 months, warn
                            import datetime
                            now = datetime.datetime.now()
                            version_date = datetime.datetime(year, month, 1)
                            age_months = (now.year - version_date.year) * 12 + now.month - version_date.month
                            
                            if age_months > 2:
                                logger.warning(f"⚠️ yt-dlp version {current_version} is {age_months} months old")
                                logger.warning("💡 Consider updating: pip install --upgrade yt-dlp")
                        except (ValueError, TypeError) as ve:
                            logger.debug(f"Could not parse version numbers from {current_version}: {ve}")
            except Exception as e:
                logger.debug(f"Could not check yt-dlp version age: {e}")
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

def update_ytdlp() -> Tuple[bool, str]:
    """
    Update yt-dlp to the latest version
    
    Returns:
        (success, message)
    """
    logger.info("🔄 Attempting to update yt-dlp...")
    
    try:
        # Try pip3 first, then pip
        pip_commands = ['pip3', 'pip']
        
        for pip_cmd in pip_commands:
            if shutil.which(pip_cmd):
                logger.info(f"Using {pip_cmd} to update yt-dlp...")
                result = subprocess.run(
                    [pip_cmd, 'install', '--upgrade', 'yt-dlp'],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    # Get new version
                    version_result = subprocess.run(
                        ['yt-dlp', '--version'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    new_version = version_result.stdout.strip()
                    logger.info(f"✓ yt-dlp updated successfully to version {new_version}")
                    return True, f"yt-dlp updated to version {new_version}"
                else:
                    logger.warning(f"Update with {pip_cmd} failed: {result.stderr}")
                    continue
        
        error_msg = "Could not update yt-dlp. No suitable pip command found or all attempts failed."
        logger.error(error_msg)
        return False, error_msg
        
    except subprocess.TimeoutExpired:
        error_msg = "yt-dlp update timed out"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error updating yt-dlp: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg

def _parse_download_error(stderr: str) -> str:
    """
    Parse yt-dlp error message and return user-friendly error with detailed diagnostics
    
    Args:
        stderr: Standard error output from yt-dlp
        
    Returns:
        User-friendly error message with specific cause
    """
    stderr_lower = stderr.lower()
    
    # Log full error for debugging
    logger.debug(f"Full error output: {stderr}")
    
    # Check for specific error patterns (ordered by specificity)
    
    # DRM and encryption errors
    if 'drm' in stderr_lower or 'encrypted' in stderr_lower or 'widevine' in stderr_lower:
        logger.error("🔒 DRM-protected content detected")
        return ERROR_MESSAGES['drm']
    
    # API and quota errors
    elif 'quota exceeded' in stderr_lower or 'quota has been exceeded' in stderr_lower:
        logger.error("📊 API quota exceeded")
        return ERROR_MESSAGES['quota_exceeded']
    elif 'too many requests' in stderr_lower or 'http error 429' in stderr_lower:
        logger.error("⏱️ Rate limit hit (HTTP 429)")
        return ERROR_MESSAGES['quota_exceeded']
    
    # Bot detection and access issues
    elif 'bot' in stderr_lower or 'automated' in stderr_lower or 'suspicious' in stderr_lower:
        logger.error("🤖 Bot detection triggered")
        return ERROR_MESSAGES['bot_detected']
    elif 'sign in' in stderr_lower and 'confirm' in stderr_lower:
        logger.error("🔐 Sign-in required (likely age-restricted)")
        return ERROR_MESSAGES['age_restricted']
    
    # Video availability errors
    elif 'video unavailable' in stderr_lower or 'this video is unavailable' in stderr_lower:
        logger.error("❌ Video unavailable")
        return ERROR_MESSAGES['unavailable']
    elif 'private video' in stderr_lower or 'this video is private' in stderr_lower:
        logger.error("🔒 Private video")
        return ERROR_MESSAGES['private']
    elif 'http error 404' in stderr_lower or 'not found' in stderr_lower:
        logger.error("❌ Video not found (HTTP 404)")
        return ERROR_MESSAGES['unavailable']
    
    # Region and restriction errors
    elif 'not available in your country' in stderr_lower or 'geo restricted' in stderr_lower or 'georestrict' in stderr_lower:
        logger.error("🌍 Geographic restriction detected")
        return ERROR_MESSAGES['region_blocked']
    elif 'blocked' in stderr_lower and 'country' in stderr_lower:
        logger.error("🌍 Country-based block detected")
        return ERROR_MESSAGES['region_blocked']
    
    # Copyright and legal issues
    elif 'copyright' in stderr_lower or 'taken down' in stderr_lower or 'removed' in stderr_lower:
        logger.error("⚖️ Copyright or legal issue")
        return ERROR_MESSAGES['copyright']
    
    # Live stream errors
    elif 'live event' in stderr_lower or 'is a live stream' in stderr_lower or 'live video' in stderr_lower:
        logger.error("📡 Live stream detected")
        return ERROR_MESSAGES['live']
    
    # Format and stream errors
    elif 'no video formats' in stderr_lower or 'no suitable formats' in stderr_lower:
        logger.error("📹 No suitable video formats available")
        return ERROR_MESSAGES['format']
    elif 'unable to download' in stderr_lower and 'format' in stderr_lower:
        logger.error("📹 Format download issue")
        return ERROR_MESSAGES['format']
    elif 'requested format not available' in stderr_lower:
        logger.error("📹 Requested format not available")
        return ERROR_MESSAGES['format']
    
    # Network errors
    elif 'network' in stderr_lower or 'connection' in stderr_lower or 'resolve host' in stderr_lower:
        logger.error("🌐 Network connectivity issue")
        return ERROR_MESSAGES['network']
    elif 'timeout' in stderr_lower or 'timed out' in stderr_lower:
        logger.error("⏱️ Network timeout")
        return ERROR_MESSAGES['timeout']
    
    # HTTP errors
    elif 'http error 403' in stderr_lower or 'forbidden' in stderr_lower:
        logger.error("🚫 HTTP 403 Forbidden - Access denied")
        # HTTP 403 can be caused by various issues
        return "Access forbidden (HTTP 403). Possible causes: region restrictions, age restrictions, temporary YouTube blocks, or bot detection. Try: 1) Update yt-dlp: pip install --upgrade yt-dlp, 2) Use cookies for authentication, 3) Wait and try again later"
    elif 'http error 5' in stderr_lower:
        logger.error("🔧 YouTube server error (HTTP 5xx)")
        return "YouTube server error. This is temporary. Please try again in a few minutes"
    
    # Player errors
    elif 'player' in stderr_lower and ('error' in stderr_lower or 'failed' in stderr_lower):
        logger.error("🎮 YouTube player error")
        return "YouTube player error. Try updating yt-dlp or using different player client options"
    
    # Generic errors
    else:
        # Return first error line if available
        error_lines = [line.strip() for line in stderr.split('\n') if 'error' in line.lower() and line.strip()]
        if error_lines:
            first_error = error_lines[0][:250]  # Increased from 200
            logger.error(f"❓ Unclassified error: {first_error}")
            return f"Download error: {first_error}"
        
        logger.error("❓ Unknown error with no specific error message")
        return ERROR_MESSAGES['unknown']

def download_youtube(
    url: str, 
    output_path: Path,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    cookies_file: Optional[Path] = None,
    max_retries: int = 3
) -> Tuple[bool, Optional[str]]:
    """
    Download YouTube video using yt-dlp with robust fallback options and detailed diagnostics
    
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
        
        # Pre-download diagnostics: Get video info to detect issues early
        logger.info("🔍 Pre-download diagnostics: Fetching video information...")
        if progress_callback:
            progress_callback(0, "Checking video availability...")
        
        video_info = get_video_info(url)
        if video_info:
            # Log important video details
            title = video_info.get('title', 'Unknown')
            duration = video_info.get('duration', 0)
            uploader = video_info.get('uploader', 'Unknown')
            
            logger.info(f"📺 Video Title: {title}")
            logger.info(f"⏱️ Duration: {duration}s ({duration//60}m {duration%60}s)")
            logger.info(f"👤 Uploader: {uploader}")
            
            # Check for potential issues
            if video_info.get('is_live'):
                logger.warning("⚠️ This is a live stream")
            if video_info.get('age_limit', 0) > 0:
                age_limit = video_info.get('age_limit')
                logger.warning(f"⚠️ Age-restricted content (age limit: {age_limit})")
                if not cookies_file:
                    logger.warning("💡 Tip: Age-restricted videos may require cookies. Use --cookies option")
            
            # Check for DRM
            if video_info.get('_has_drm') or video_info.get('is_drm_protected'):
                error_msg = ERROR_MESSAGES['drm']
                logger.error(f"🔒 {error_msg}")
                return False, error_msg
            
            # Check format availability
            formats = video_info.get('formats', [])
            if not formats:
                error_msg = ERROR_MESSAGES['format']
                logger.error(f"📹 {error_msg}")
                return False, error_msg
            
            logger.info(f"✓ Video info retrieved successfully, {len(formats)} formats available")
        else:
            logger.warning("⚠️ Could not fetch video info, will attempt download anyway")
            logger.warning("💡 This may indicate the video is unavailable, region-blocked, or requires authentication")
        
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
            if error and any(keyword in error.lower() for keyword in ['network', 'timeout', 'connection', '429', 'empty', 'too small']):
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
            # Enhanced progress tracking
            '--newline',
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
            bufsize=1,
            startupinfo=get_subprocess_startup_info(),
            creationflags=get_subprocess_creation_flags()
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
                    parts = line.split('%')
                    if len(parts) > 0 and parts[0].split():
                        percent_str = parts[0].split()[-1]
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
        
        # Verify file exists and is valid
        if output_path.exists():
            file_size = output_path.stat().st_size
            logger.info(f"✓ File downloaded: {file_size / 1024 / 1024:.1f} MB")
            
            # Validate the downloaded file
            logger.info("🔍 Validating downloaded video file...")
            is_valid, error_msg = _validate_video_file(output_path)
            if not is_valid:
                logger.error(f"❌ Downloaded file validation failed: {error_msg}")
                # Remove invalid file
                try:
                    output_path.unlink()
                    logger.info("Removed invalid file")
                except Exception as e:
                    logger.warning(f"Failed to remove invalid file: {e}")

                # If file is empty or too small, try fallback methods before failing
                if error_msg and any(keyword in error_msg.lower() for keyword in ['empty', 'too small', 'incomplete']):
                    logger.info("🔄 Empty/invalid file detected. Trying fallback download methods...")
                    return _download_fallback(url, output_path, cookies_file, progress_callback)

                return False, f"Download validation failed: {error_msg}"
            
            logger.info(f"✓ File validated successfully: {file_size / 1024 / 1024:.1f} MB")
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
                        # Validate converted file
                        is_valid, error_msg = _validate_video_file(output_path)
                        if is_valid:
                            return True, None
                        else:
                            return False, f"Converted file validation failed: {error_msg}"
                    else:
                        return False, f"Downloaded but conversion from {ext} to mp4 failed"
                else:
                    # Validate the mp4 file
                    is_valid, error_msg = _validate_video_file(alt_path)
                    if is_valid:
                        return True, None
                    else:
                        # Try fallback if the alternate file is empty/invalid
                        if error_msg and any(keyword in error_msg.lower() for keyword in ['empty', 'too small', 'incomplete']):
                            logger.info("🔄 Empty/invalid alternate file detected. Trying fallback download methods...")
                            try:
                                alt_path.unlink()
                            except Exception:
                                pass
                            return _download_fallback(url, output_path, cookies_file, progress_callback)
                        return False, f"Downloaded file validation failed: {error_msg}"
        
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
    Enhanced fallback download method with multiple strategies
    
    This method tries different player clients, format options, and quality levels
    when the main download fails. It implements a comprehensive fallback chain.
    """
    logger.info("=== Attempting enhanced fallback download methods ===")
    
    if progress_callback:
        progress_callback(0, "Trying alternative download methods...")
    
    output_template = str(output_path.with_suffix(''))
    
    # Enhanced fallback strategies with more options
    fallback_strategies = [
        {
            'name': 'Android client with best format',
            'args': ['--extractor-args', 'youtube:player_client=android'],
            'format': 'best[ext=mp4]/best'
        },
        {
            'name': 'iOS client with standard quality',
            'args': ['--extractor-args', 'youtube:player_client=ios'],
            'format': 'best[height<=720][ext=mp4]/best[height<=720]/best'
        },
        {
            'name': 'Web client with embedded player',
            'args': ['--extractor-args', 'youtube:player_client=web_embedded'],
            'format': 'best[ext=mp4]/best'
        },
        {
            'name': 'Android embedded client',
            'args': ['--extractor-args', 'youtube:player_client=android_embedded'],
            'format': 'best'
        },
        {
            'name': 'TV client (smart TV interface)',
            'args': ['--extractor-args', 'youtube:player_client=tv'],
            'format': 'best[ext=mp4]/best'
        },
        {
            'name': 'Mobile web with lower quality',
            'args': ['--extractor-args', 'youtube:player_client=mweb'],
            'format': 'best[height<=480]/worst'
        },
        {
            'name': 'Generic best available (no client preference)',
            'args': [],
            'format': 'b/best'
        }
    ]
    
    for idx, strategy in enumerate(fallback_strategies, 1):
        logger.info(f"🔄 Fallback strategy {idx}/{len(fallback_strategies)}: {strategy['name']}")
        if progress_callback:
            progress_callback(0, f"Fallback method {idx}/{len(fallback_strategies)}: {strategy['name']}")
        
        cmd = [
            'yt-dlp',
            '-f', strategy['format'],
            '--no-warnings',
            '--no-check-certificate',
            *strategy['args'],
            '-o', f'{output_template}.%(ext)s',
            '--retries', '5',
            '--fragment-retries', '5',
            '--skip-unavailable-fragments',
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
                    # Validate the file
                    is_valid, error_msg = _validate_video_file(output_path)
                    if is_valid:
                        logger.info(f"✓ Fallback download successful with {strategy['name']}")
                        if progress_callback:
                            progress_callback(100, "Download complete (fallback)")
                        return True, None
                    else:
                        logger.warning(f"Fallback file validation failed: {error_msg}")
                        # Try to remove invalid file and continue to next strategy
                        try:
                            output_path.unlink()
                        except Exception:
                            pass
                
                # Check for file with different extension
                for ext in ['.mp4', '.mkv', '.webm']:
                    alt_path = output_path.with_suffix(ext)
                    if alt_path.exists():
                        logger.info(f"Found file with extension: {ext}")
                        if ext != '.mp4':
                            if _convert_to_mp4(alt_path, output_path):
                                alt_path.unlink()
                                logger.info("✓ Conversion successful")
                                # Validate converted file
                                is_valid, error_msg = _validate_video_file(output_path)
                                if is_valid:
                                    return True, None
                                else:
                                    logger.warning(f"Converted file validation failed: {error_msg}")
                                    continue
                        else:
                            # Validate the file
                            is_valid, error_msg = _validate_video_file(alt_path)
                            if is_valid:
                                return True, None
                            else:
                                logger.warning(f"File validation failed: {error_msg}")
                                continue
            
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

def _validate_video_file(file_path: Path, min_size_mb: float = 0.1, expected_duration: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """
    Enhanced validation that video file is not empty and has valid content
    
    Args:
        file_path: Path to video file
        min_size_mb: Minimum file size in MB (default 0.1 MB = 100 KB)
        expected_duration: Expected video duration in seconds (optional)
    
    Returns:
        (is_valid, error_message)
    """
    try:
        if not file_path.exists():
            return False, f"File does not exist: {file_path}"
        
        # Check file size
        file_size = file_path.stat().st_size
        file_size_mb = file_size / 1024 / 1024
        
        if file_size == 0:
            logger.error("❌ File is empty (0 bytes) - Possible causes:")
            logger.error("   1. Network interruption during download")
            logger.error("   2. Region restriction or DRM protection")
            logger.error("   3. YouTube API quota exceeded")
            logger.error("   4. Invalid video format or stream unavailable")
            return False, "Downloaded file is empty (0 bytes). Possible causes: network error, region restriction, DRM, or API quota exceeded."
        
        if file_size_mb < min_size_mb:
            logger.error(f"❌ File too small ({file_size_mb:.2f} MB, minimum: {min_size_mb} MB)")
            logger.error("   This suggests incomplete download or corrupted file")
            return False, f"Downloaded file is too small ({file_size_mb:.2f} MB). Minimum expected: {min_size_mb} MB. Possible incomplete download."
        
        logger.debug(f"✓ File size check passed: {file_size_mb:.2f} MB")
        
        # Enhanced validation with ffprobe - check video stream, audio stream, and duration
        logger.debug(f"🔍 Deep validation with ffprobe: {file_path}")
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'stream=codec_type,codec_name,duration:format=duration',
            '-of', 'default=noprint_wrappers=1',  # Include keys in output (key=value format)
            str(file_path)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"❌ ffprobe validation failed: {result.stderr[:200]}")
            return False, f"File appears corrupted or not a valid video format. ffprobe error: {result.stderr[:200]}"
        
        output = result.stdout.lower()
        
        # Check if file has video stream
        if 'codec_type=video' not in output:
            logger.error("❌ No video stream found in file")
            return False, "File does not contain a video stream. May be corrupted or incomplete."
        
        logger.debug("✓ Video stream found")
        
        # Check if file has audio stream (warning only, not failure)
        if 'codec_type=audio' not in output:
            logger.warning("⚠️ No audio stream found in video file (video-only)")
        else:
            logger.debug("✓ Audio stream found")
        
        # Extract and validate duration if expected
        duration_match = re.search(r'duration=(\d+\.?\d*)', output)
        if duration_match:
            actual_duration = float(duration_match.group(1))
            logger.debug(f"✓ Video duration: {actual_duration:.1f}s ({actual_duration/60:.1f}m)")
            
            # If expected duration is provided, check if actual is reasonably close
            if expected_duration and expected_duration > 0:
                duration_diff = abs(actual_duration - expected_duration)
                duration_ratio = duration_diff / expected_duration
                
                if duration_ratio > 0.1:  # More than 10% difference
                    logger.warning(f"⚠️ Duration mismatch: expected {expected_duration}s, got {actual_duration:.1f}s")
                    logger.warning(f"   Difference: {duration_diff:.1f}s ({duration_ratio*100:.1f}%)")
                    logger.warning("   This may indicate incomplete download or corrupted file")
                    return False, f"Video duration mismatch. Expected {expected_duration}s, got {actual_duration:.1f}s. Possible incomplete download."
                else:
                    logger.debug(f"✓ Duration validation passed (diff: {duration_diff:.1f}s, {duration_ratio*100:.1f}%)")
        else:
            logger.warning("⚠️ Could not extract duration from video file")
        
        logger.debug(f"✓ Video file validation passed: {file_size_mb:.2f} MB")
        return True, None
        
    except subprocess.TimeoutExpired:
        logger.warning(f"⏱️ Video validation timed out for {file_path}")
        # Don't fail on timeout, consider file valid if it exists and has size
        if file_path.exists() and file_path.stat().st_size > min_size_mb * 1024 * 1024:
            logger.warning("   Accepting file despite timeout (has valid size)")
            return True, None
        return False, "Video validation timed out and file appears invalid"
    except Exception as e:
        logger.warning(f"❌ Error during video validation: {e}")
        # Don't fail on validation errors if file exists and has reasonable size
        if file_path.exists() and file_path.stat().st_size > min_size_mb * 1024 * 1024:
            logger.warning(f"   Accepting file despite validation error (has valid size)")
            return True, None
        return False, f"Video validation error: {str(e)}"

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
