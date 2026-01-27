"""FFmpeg utilities for video processing"""
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple
import json

logger = logging.getLogger(__name__)

def normalize_video(input_path: Path, output_path: Path) -> bool:
    """Normalize video to standard format"""
    try:
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            '-y',
            str(output_path)
        ]
        
        logger.info(f"Normalizing video: {input_path}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg normalize error: {result.stderr}")
            return False
            
        logger.info(f"Normalized: {output_path}")
        return output_path.exists()
        
    except subprocess.TimeoutExpired:
        logger.error("Normalize timeout")
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
        
        result = subprocess.run(cmd, capture_output=True, text=True)
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
        cmd = [
            'ffmpeg', '-ss', str(timestamp),
            '-i', str(video_path),
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Extract thumbnail error: {e}")
        return False

def extract_segment(input_path: Path, output_path: Path, start: float, duration: float) -> bool:
    """Extract video segment"""
    try:
        cmd = [
            'ffmpeg', '-ss', str(start),
            '-i', str(input_path),
            '-t', str(duration),
            '-c', 'copy',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Extract segment error: {e}")
        return False

def extract_audio(video_path: Path, output_path: Path, start: float, duration: float) -> bool:
    """Extract audio segment"""
    try:
        cmd = [
            'ffmpeg', '-ss', str(start),
            '-i', str(video_path),
            '-t', str(duration),
            '-vn', '-acodec', 'aac',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Extract audio error: {e}")
        return False

def crop_and_scale_center(input_path: Path, output_path: Path, width: int, height: int) -> bool:
    """Crop center and scale to target resolution"""
    try:
        # Calculate crop for 9:16 aspect ratio
        target_aspect = width / height
        
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-vf', f'crop=ih*{target_aspect}:ih,scale={width}:{height}',
            '-c:a', 'copy',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Crop and scale error: {e}")
        return False

def mux_video_audio(video_path: Path, audio_path: Path, output_path: Path) -> bool:
    """Mux video and audio"""
    try:
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-i', str(audio_path),
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-shortest',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Mux error: {e}")
        return False

def burn_subtitles(video_path: Path, srt_path: Path, output_path: Path) -> bool:
    """Burn subtitles into video"""
    try:
        # Escape path for subtitles filter
        srt_escaped = str(srt_path).replace('\\', '/').replace(':', '\\:')
        
        cmd = [
            'ffmpeg', '-i', str(video_path),
            '-vf', f"subtitles='{srt_escaped}':force_style='FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,Alignment=2'",
            '-c:a', 'copy',
            '-y',
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0 and output_path.exists()
        
    except Exception as e:
        logger.error(f"Burn subtitles error: {e}")
        return False
