"""Render service for creating vertical 9:16 clips"""
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any
from services.ffmpeg import (
    extract_segment, extract_audio, crop_and_scale_center,
    mux_video_audio, burn_subtitles
)
from services.reframe import reframe_video_with_tracking
from config import OUTPUT_WIDTH, OUTPUT_HEIGHT

logger = logging.getLogger(__name__)

def generate_srt(transcript_snippet: str, start_sec: float, end_sec: float, output_path: Path) -> bool:
    """Generate simple SRT file from transcript snippet"""
    try:
        duration = end_sec - start_sec
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("1\n")
            f.write(f"{format_srt_time(0)} --> {format_srt_time(duration)}\n")
            f.write(f"{transcript_snippet}\n")
        
        return True
    except Exception as e:
        logger.error(f"Generate SRT error: {e}")
        return False

def format_srt_time(seconds: float) -> str:
    """Format seconds to SRT timestamp"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def render_clip(
    video_path: Path,
    output_path: Path,
    start_sec: float,
    end_sec: float,
    face_tracking: bool = False,
    captions: bool = False,
    transcript_snippet: str = ""
) -> bool:
    """
    Render vertical 9:16 clip
    
    Args:
        video_path: Input normalized video
        output_path: Output path for rendered clip
        start_sec: Start time in seconds
        end_sec: End time in seconds
        face_tracking: Enable face tracking and reframing
        captions: Burn in captions
        transcript_snippet: Text for captions
    
    Returns:
        True if successful
    """
    try:
        duration = end_sec - start_sec
        
        logger.info(f"Rendering clip: {start_sec:.2f}s - {end_sec:.2f}s (face_tracking={face_tracking}, captions={captions})")
        
        # Create temp directory for intermediate files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            if face_tracking:
                # Extract segment first (for face tracking processing)
                segment_path = tmpdir_path / "segment.mp4"
                if not extract_segment(video_path, segment_path, start_sec, duration):
                    logger.error("Failed to extract segment")
                    return False
                
                # Reframe with face tracking
                video_no_audio = tmpdir_path / "video_no_audio.mp4"
                if not reframe_video_with_tracking(
                    segment_path,
                    video_no_audio,
                    OUTPUT_WIDTH,
                    OUTPUT_HEIGHT,
                    0,  # Already extracted segment
                    duration
                ):
                    logger.error("Failed to reframe video")
                    return False
                
                # Extract audio from original segment
                audio_path = tmpdir_path / "audio.aac"
                if not extract_audio(video_path, audio_path, start_sec, duration):
                    logger.error("Failed to extract audio")
                    return False
                
                # Mux video and audio
                if captions and transcript_snippet:
                    # Mux first, then burn captions
                    muxed_path = tmpdir_path / "muxed.mp4"
                    if not mux_video_audio(video_no_audio, audio_path, muxed_path):
                        logger.error("Failed to mux video and audio")
                        return False
                    
                    # Generate SRT
                    srt_path = tmpdir_path / "captions.srt"
                    if not generate_srt(transcript_snippet, 0, duration, srt_path):
                        logger.error("Failed to generate SRT")
                        return False
                    
                    # Burn subtitles
                    if not burn_subtitles(muxed_path, srt_path, output_path):
                        logger.error("Failed to burn subtitles")
                        return False
                else:
                    # Just mux
                    if not mux_video_audio(video_no_audio, audio_path, output_path):
                        logger.error("Failed to mux video and audio")
                        return False
            else:
                # Simple center crop and scale (faster)
                # Extract segment
                segment_path = tmpdir_path / "segment.mp4"
                if not extract_segment(video_path, segment_path, start_sec, duration):
                    logger.error("Failed to extract segment")
                    return False
                
                if captions and transcript_snippet:
                    # Crop and scale, then burn captions
                    cropped_path = tmpdir_path / "cropped.mp4"
                    if not crop_and_scale_center(segment_path, cropped_path, OUTPUT_WIDTH, OUTPUT_HEIGHT):
                        logger.error("Failed to crop and scale")
                        return False
                    
                    # Generate SRT
                    srt_path = tmpdir_path / "captions.srt"
                    if not generate_srt(transcript_snippet, 0, duration, srt_path):
                        logger.error("Failed to generate SRT")
                        return False
                    
                    # Burn subtitles
                    if not burn_subtitles(cropped_path, srt_path, output_path):
                        logger.error("Failed to burn subtitles")
                        return False
                else:
                    # Just crop and scale
                    if not crop_and_scale_center(segment_path, output_path, OUTPUT_WIDTH, OUTPUT_HEIGHT):
                        logger.error("Failed to crop and scale")
                        return False
        
        logger.info(f"Render complete: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Render error: {e}")
        return False
