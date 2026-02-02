"""Render service for creating vertical 9:16 clips"""
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any
from services.ffmpeg import (
    extract_segment, extract_audio, crop_and_scale_center,
    mux_video_audio, burn_subtitles
)
from services.reframe import reframe_video_with_tracking, reframe_video_smart
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


def _mux_and_add_captions(
    video_no_audio: Path,
    audio_path: Path,
    output_path: Path,
    captions: bool,
    transcript_snippet: str,
    duration: float,
    tmpdir_path: Path
) -> bool:
    """
    Helper function to mux video/audio and optionally add captions
    
    Args:
        video_no_audio: Path to video without audio
        audio_path: Path to audio file
        output_path: Final output path
        captions: Whether to add captions
        transcript_snippet: Caption text
        duration: Video duration in seconds
        tmpdir_path: Temporary directory path
    
    Returns:
        True if successful
    """
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
    
    return True


def render_clip(
    video_path: Path,
    output_path: Path,
    start_sec: float,
    end_sec: float,
    face_tracking: bool = False,
    smart_crop: bool = False,
    captions: bool = False,
    transcript_snippet: str = "",
    watermark_text: str = "",
    upload_to_s3: bool = True
) -> str:
    """
    Render vertical 9:16 clip
    
    Args:
        video_path: Input normalized video
        output_path: Output path for rendered clip
        start_sec: Start time in seconds
        end_sec: End time in seconds
        face_tracking: Enable face tracking and reframing
        smart_crop: Enable smart cropping (solo/duo_switch/duo_split modes)
        captions: Burn in captions
        transcript_snippet: Text for captions
    
    Returns:
        True if successful
    """
    from services.cloud import upload_file_to_s3
    try:
        duration = end_sec - start_sec
        
        logger.info(f"Rendering clip: {start_sec:.2f}s - {end_sec:.2f}s (face_tracking={face_tracking}, smart_crop={smart_crop}, captions={captions})")
        
        # Create temp directory for intermediate files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            if smart_crop:
                # Extract segment first (for smart cropping processing)
                segment_path = tmpdir_path / "segment.mp4"
                if not extract_segment(video_path, segment_path, start_sec, duration):
                    logger.error("Failed to extract segment")
                    return False
                
                # Smart reframe with automatic mode detection
                video_no_audio = tmpdir_path / "video_no_audio.mp4"
                if not reframe_video_smart(
                    segment_path,
                    video_no_audio,
                    OUTPUT_WIDTH,
                    OUTPUT_HEIGHT,
                    0,  # Already extracted segment
                    duration
                ):
                    logger.error("Failed to smart reframe video")
                    return False
                
                # Extract audio from original segment
                audio_path = tmpdir_path / "audio.aac"
                if not extract_audio(video_path, audio_path, start_sec, duration):
                    logger.error("Failed to extract audio")
                    return False
                
                # Mux and add captions if needed
                if not _mux_and_add_captions(
                    video_no_audio, audio_path, output_path,
                    captions, transcript_snippet, duration, tmpdir_path
                ):
                    return False
            
            elif face_tracking:
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
                
                # Mux and add captions if needed
                if not _mux_and_add_captions(
                    video_no_audio, audio_path, output_path,
                    captions, transcript_snippet, duration, tmpdir_path
                ):
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
        
        # Watermark
        if watermark_text:
            from services.ffmpeg import add_watermark
            watermarked_path = output_path.parent / (output_path.stem + "_wm.mp4")
            if add_watermark(output_path, watermarked_path, watermark_text):
                output_path.unlink(missing_ok=True)
                watermarked_path.rename(output_path)
        logger.info(f"Render complete: {output_path}")
        s3_url = None
        if upload_to_s3:
            try:
                s3_key = f"renders/{output_path.name}"
                s3_url = upload_file_to_s3(output_path, s3_key)
                logger.info(f"Uploaded render to S3: {s3_url}")
            except Exception as e:
                logger.error(f"S3 upload error: {e}")
        return s3_url or str(output_path)
        
    except Exception as e:
        logger.error(f"Render error: {e}")
        return None
