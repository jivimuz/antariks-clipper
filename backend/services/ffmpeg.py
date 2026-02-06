
from pathlib import Path
import subprocess
import sys
import logging
from typing import Optional, Tuple
import json
from utils import get_subprocess_startup_info, get_subprocess_creation_flags

def add_watermark(input_path: Path, output_path: Path, text: str) -> bool:
    """Add watermark text to video using ffmpeg drawtext"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            'ffmpeg', '-y', '-i', str(input_path),
            '-vf', f"drawtext=text='{text}':fontcolor=white:fontsize=36:x=w-tw-20:y=h-th-20:box=1:boxcolor=black@0.5:boxborderw=5",
            '-c:a', 'copy', str(output_path)
        ]
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300,
            startupinfo=get_subprocess_startup_info(),
            creationflags=get_subprocess_creation_flags()
        )
        if result.returncode == 0:
            return True
        logger.error(f"Add watermark error: {result.stderr}")
        return False
    except Exception as e:
        logger.error(f"Add watermark exception: {e}")
        return False

logger = logging.getLogger(__name__)

def get_video_info(video_path: Path) -> Optional[dict]:
    """Get video codec and format info"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,width,height',
            '-of', 'json',
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('streams'):
                return data['streams'][0]
        return None
    except Exception as e:
        logger.error(f"Get video info error: {e}")
        return None

def get_audio_info(video_path: Path) -> Optional[dict]:
    """Get audio codec info"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=codec_name,sample_rate',
            '-of', 'json',
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get('streams'):
                return data['streams'][0]
        return None
    except Exception as e:
        logger.error(f"Get audio info error: {e}")
        return None

def normalize_video(input_path: Path, output_path: Path) -> bool:
    """Normalize video to standard format with smart detection"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get video duration for dynamic timeout
        duration = get_video_duration(input_path)
        # Timeout = 3x duration minimum 300s, max 7200s (2 hours)
        timeout = min(max(int((duration or 600) * 3), 300), 7200)
        
        # Check if video is already H264
        video_info = get_video_info(input_path)
        audio_info = get_audio_info(input_path)
        
        video_codec = video_info.get('codec_name', '') if video_info else ''
        audio_codec = audio_info.get('codec_name', '') if audio_info else ''
        
        # If already H264 + AAC, just copy (much faster)
        if video_codec == 'h264' and audio_codec == 'aac':
            logger.info(f"Video already H264/AAC, copying streams: {input_path}")
            cmd = [
                'ffmpeg', '-i', str(input_path),
                '-c', 'copy',
                '-movflags', '+faststart',
                '-y',
                str(output_path)
            ]
        else:
            # Need to re-encode
            logger.info(f"Normalizing video (re-encode): {input_path}")
            cmd = [
                'ffmpeg', '-i', str(input_path),
                '-c:v', 'libx264',
                '-preset', 'fast',  # Changed from 'medium' to 'fast'
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '44100',
                '-movflags', '+faststart',
                '-y',
                str(output_path)
            ]
        
        logger.info(f"Normalize timeout: {timeout}s for {duration if duration else 'unknown'}s video")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
        
        if result.returncode != 0:
            logger.error(f"FFmpeg normalize error: {result.stderr}")
            # Fallback: try with ultrafast preset
            logger.info("Retrying with ultrafast preset...")
            cmd_fallback = [
                'ffmpeg', '-i', str(input_path),
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '44100',
                '-movflags', '+faststart',
                '-y',
                str(output_path)
            ]
            result = subprocess.run(cmd_fallback, capture_output=True, text=True, timeout=timeout, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
            if result.returncode != 0:
                logger.error(f"FFmpeg fallback error: {result.stderr}")
                return False
            
        logger.info(f"Normalized: {output_path}")
        return output_path.exists()
        
    except subprocess.TimeoutExpired:
        logger.error(f"Normalize timeout after {timeout}s")
        return False
    except Exception as e:
        logger.error(f"Normalize error: {e}")
        return False

def get_video_duration(video_path: Path) -> Optional[float]:
    """Get video duration in seconds"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        return None
    except Exception as e:
        logger.error(f"Get duration error: {e}")
        return None

def extract_thumbnail(video_path: Path, timestamp: float, output_path: Path) -> bool:
    """Extract thumbnail at timestamp"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            'ffmpeg', '-ss', str(timestamp),
            '-i', str(video_path),
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Extract thumbnail error: {e}")
        return False

def extract_segment(input_path: Path, output_path: Path, start: float, duration: float) -> bool:
    """Extract video segment"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Use -ss before -i for faster seeking
        cmd = [
            'ffmpeg', 
            '-ss', str(start),
            '-i', str(input_path),
            '-t', str(duration),
            '-c', 'copy',
            '-avoid_negative_ts', 'make_zero',
            '-y',
            str(output_path)
        ]
        
        timeout = max(int(duration * 2), 60)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Extract segment error: {e}")
        return False

def extract_audio(video_path: Path, output_path: Path, start: float, duration: float) -> bool:
    """Extract audio segment"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            'ffmpeg', 
            '-ss', str(start),
            '-i', str(video_path),
            '-t', str(duration),
            '-vn', '-acodec', 'aac',
            '-y',
            str(output_path)
        ]
        
        timeout = max(int(duration * 2), 60)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Extract audio error: {e}")
        return False

def crop_and_scale_center(input_path: Path, output_path: Path, width: int, height: int) -> bool:
    """Crop center and scale to target resolution"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Calculate crop for 9:16 aspect ratio
        target_aspect = width / height
        
        # Get duration for timeout
        duration = get_video_duration(input_path) or 60
        timeout = max(int(duration * 3), 120)
        
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-vf', f'crop=ih*{target_aspect}:ih,scale={width}:{height}',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'copy',
            '-movflags', '+faststart',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Crop and scale error: {e}")
        return False

def mux_video_audio(video_path: Path, audio_path: Path, output_path: Path) -> bool:
    """Mux video and audio with proper sync"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        video_info = get_video_info(video_path)
        audio_info = get_audio_info(audio_path)

        video_codec = video_info.get('codec_name', '') if video_info else ''
        audio_codec = audio_info.get('codec_name', '') if audio_info else ''

        # Re-encode if codecs are not browser/social compatible
        reencode_video = video_codec != 'h264'
        reencode_audio = audio_codec != 'aac'

        if reencode_video or reencode_audio:
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-i', str(audio_path),
                '-map', '0:v:0',  # Map video from first input
                '-map', '1:a:0',  # Map audio from second input
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '44100',
                '-shortest',  # End at shortest stream
                '-async', '1',  # Audio sync method
                '-vsync', '2',  # Video sync method (CFR)
                '-movflags', '+faststart',
                '-y',
                str(output_path)
            ]
        else:
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-i', str(audio_path),
                '-c:v', 'copy',
                '-c:a', 'copy',  # Copy audio codec to avoid re-encoding delays
                '-map', '0:v:0',  # Map video from first input
                '-map', '1:a:0',  # Map audio from second input
                '-shortest',  # End at shortest stream
                '-async', '1',  # Audio sync method
                '-vsync', '2',  # Video sync method (CFR)
                '-movflags', '+faststart',
                '-y',
                str(output_path)
            ]
        
        duration = get_video_duration(video_path) or 60
        timeout = max(int(duration * 2), 120)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Mux error: {e}")
        return False

def burn_subtitles(video_path: Path, srt_path: Path, output_path: Path) -> bool:
    """Burn subtitles into video with proper A/V sync"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Escape path for subtitles filter (Windows compatibility)
        srt_escaped = str(srt_path).replace('\\', '/').replace(':', '\\:')
        
        duration = get_video_duration(video_path) or 60
        timeout = max(int(duration * 3), 120)
        
        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-vf', f"subtitles='{srt_escaped}':force_style='FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,Alignment=2'",
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'copy',
            '-vsync', '2',  # Video sync method for proper frame timing
            '-async', '1',  # Audio sync method
            '-movflags', '+faststart',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Burn subtitles error: {e}")
        return False
