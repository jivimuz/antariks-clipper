"""Background job processing using ThreadPoolExecutor"""
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any
import db
from config import (
    MAX_WORKERS, RAW_DIR, NORMALIZED_DIR, TRANSCRIPTS_DIR,
    THUMBNAILS_DIR, RENDERS_DIR
)
from services.downloader import download_youtube, save_upload
from services.ffmpeg import normalize_video
from services.transcribe import transcribe_video, load_transcript
from services.highlight import generate_highlights
from services.thumbnails import generate_thumbnail
from services.render import render_clip

logger = logging.getLogger(__name__)

# Global thread pool
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

def submit_job(job_id: str):
    """Submit job to background processing"""
    executor.submit(process_job, job_id)

def submit_render(render_id: str):
    """Submit render to background processing"""
    executor.submit(process_render, render_id)

def cleanup_raw_file(raw_path: str) -> bool:
    """
    Delete raw file after processing completes to save disk space.
    Normalized files are kept for rendering clips.
    """
    try:
        if raw_path and Path(raw_path).exists():
            Path(raw_path).unlink()
            logger.info(f"Cleaned up raw file: {raw_path}")
            return True
        return False
    except Exception as e:
        logger.warning(f"Failed to cleanup raw file {raw_path}: {e}")
        return False

def process_job(job_id: str):
    """
    Main job processing pipeline with resume support.
    Steps:
    1. Acquire (download or upload)
    2. Normalize
    3. Transcribe
    4. Generate highlights
    5. Create thumbnails
    6. Cleanup raw files
    
    Will skip steps if output files already exist (for retry/resume).
    """
    raw_path = None
    
    try:
        logger.info(f"Processing job: {job_id}")
        job = db.get_job(job_id)
        
        if not job:
            logger.error(f"Job not found: {job_id}")
            return
        
        # Define paths
        raw_path_youtube = RAW_DIR / f"{job_id}.mp4"
        normalized_path = NORMALIZED_DIR / f"{job_id}.mp4"
        transcript_path = TRANSCRIPTS_DIR / f"{job_id}.json"
        
        # ===== Step 1: Acquire =====
        db.update_job(job_id, status='processing', step='acquire', progress=10)
        
        if job['source_type'] == 'youtube':
            raw_path = raw_path_youtube
            
            # Check if raw file already exists (resume case)
            if raw_path.exists():
                logger.info(f"Raw file exists, skipping download: {raw_path}")
            else:
                if not download_youtube(job['source_url'], raw_path):
                    db.update_job(job_id, status='failed', error='Download failed')
                    return
        else:
            # Upload - path should already be set
            raw_path = Path(job['raw_path']) if job.get('raw_path') else None
            if not raw_path or not raw_path.exists():
                db.update_job(job_id, status='failed', error='Upload file not found')
                return
        
        db.update_job(job_id, raw_path=str(raw_path), progress=20)
        
        # ===== Step 2: Normalize =====
        db.update_job(job_id, step='normalize', progress=30)
        
        # Check if normalized file already exists (resume case)
        if normalized_path.exists():
            logger.info(f"Normalized file exists, skipping normalization: {normalized_path}")
        else:
            if not normalize_video(raw_path, normalized_path):
                db.update_job(job_id, status='failed', error='Normalization failed')
                return
        
        db.update_job(job_id, normalized_path=str(normalized_path), progress=40)
        
        # ===== Step 3: Transcribe =====
        db.update_job(job_id, step='transcribe', progress=50)
        
        # Check if transcript already exists (resume case)
        if transcript_path.exists():
            logger.info(f"Transcript exists, skipping transcription: {transcript_path}")
        else:
            if not transcribe_video(normalized_path, transcript_path):
                db.update_job(job_id, status='failed', error='Transcription failed')
                return
        
        db.update_job(job_id, progress=60)
        
        # ===== Step 4: Generate highlights =====
        db.update_job(job_id, step='generate_highlights', progress=70)
        
        # Check if clips already exist for this job (resume case)
        existing_clips = db.get_clips_by_job(job_id)
        
        if existing_clips:
            logger.info(f"Clips already exist ({len(existing_clips)}), skipping highlight generation")
        else:
            transcript = load_transcript(transcript_path)
            highlights = generate_highlights(transcript)
            
            if not highlights:
                db.update_job(job_id, status='failed', error='No highlights generated')
                return
            
            # Step 5: Create clips and thumbnails
            db.update_job(job_id, step='create_clips', progress=80)
            
            for i, hl in enumerate(highlights):
                clip_id = str(uuid.uuid4())
                
                # Generate thumbnail
                mid_time = (hl['start'] + hl['end']) / 2
                thumbnail_path = THUMBNAILS_DIR / f"{clip_id}.jpg"
                generate_thumbnail(normalized_path, mid_time, thumbnail_path)
                
                # Create clip record
                db.create_clip(
                    clip_id=clip_id,
                    job_id=job_id,
                    start_sec=hl['start'],
                    end_sec=hl['end'],
                    score=hl['score'],
                    title=hl['title'],
                    transcript_snippet=hl['snippet'],
                    thumbnail_path=str(thumbnail_path) if thumbnail_path.exists() else ""
                )
        
        # ===== Step 6: Cleanup raw file =====
        db.update_job(job_id, step='cleanup', progress=95)
        if raw_path and raw_path.exists():
            if cleanup_raw_file(str(raw_path)):
                # Clear raw_path in database only if cleanup succeeded
                db.update_job(job_id, raw_path="")
        
        # ===== Done =====
        db.update_job(job_id, status='ready', step='complete', progress=100)
        logger.info(f"Job complete: {job_id}")
        
    except Exception as e:
        logger.error(f"Job processing error: {e}", exc_info=True)
        db.update_job(job_id, status='failed', error=str(e))
        # Don't cleanup on failure - might need files for retry

def process_render(render_id: str):
    """
    Process render job
    1. Get clip and render details
    2. Render vertical video
    """
    try:
        logger.info(f"Processing render: {render_id}")
        render = db.get_render(render_id)
        
        if not render:
            logger.error(f"Render not found: {render_id}")
            return
        
        clip = db.get_clip(render['clip_id'])
        if not clip:
            db.update_render(render_id, status='failed', error='Clip not found')
            return
        
        job = db.get_job(clip['job_id'])
        if not job or not job.get('normalized_path'):
            db.update_render(render_id, status='failed', error='Job video not found')
            return
        
        normalized_path = Path(job['normalized_path'])
        if not normalized_path.exists():
            db.update_render(render_id, status='failed', error='Normalized video file not found')
            return
        
        # Update status
        db.update_render(render_id, status='processing', progress=10)
        
        # Get options
        options = render.get('options', {})
        face_tracking = options.get('face_tracking', False)
        captions = options.get('captions', False)
        
        # Output path
        output_path = RENDERS_DIR / f"{render_id}.mp4"
        
        # Check if render output already exists (resume case - unlikely but handle it)
        if output_path.exists():
            logger.info(f"Render output exists: {output_path}")
            db.update_render(
                render_id,
                status='ready',
                progress=100,
                output_path=str(output_path)
            )
            return
        
        # Render
        db.update_render(render_id, progress=30)
        
        success = render_clip(
            video_path=normalized_path,
            output_path=output_path,
            start_sec=clip['start_sec'],
            end_sec=clip['end_sec'],
            face_tracking=face_tracking,
            captions=captions,
            transcript_snippet=clip.get('transcript_snippet', '')
        )
        
        if not success:
            db.update_render(render_id, status='failed', error='Render failed')
            return
        
        # Done
        db.update_render(
            render_id,
            status='ready',
            progress=100,
            output_path=str(output_path)
        )
        logger.info(f"Render complete: {render_id}")
        
    except Exception as e:
        logger.error(f"Render processing error: {e}", exc_info=True)
        db.update_render(render_id, status='failed', error=str(e))
