"""Background job processing using ThreadPoolExecutor"""
import logging
import uuid
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any
import db
from config import (
    MAX_WORKERS, RAW_DIR, NORMALIZED_DIR, TRANSCRIPTS_DIR,
    THUMBNAILS_DIR, RENDERS_DIR
)
from services.downloader import download_youtube, save_upload
from services.transcribe import transcribe_video, load_transcript
from services.highlight import generate_highlights
from services.thumbnails import generate_thumbnail
from services.render import render_clip

logger = logging.getLogger(__name__)

# Utility: call webhook
def notify_webhook(url: str, payload: dict):
    """Send webhook notification for job status updates"""
    try:
        if url:
            logger.debug(f"Sending webhook notification to: {url}")
            response = requests.post(url, json=payload, timeout=5)
            logger.debug(f"Webhook response: {response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to notify webhook {url}: {e}")

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
    Raw files are kept during processing for preview and rendering.
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
    Updated pipeline - no normalize step, preview-first approach
    1. Acquire (download or upload)
    2. Transcribe (from raw video directly)
    3. Generate highlights
    4. Create thumbnails
    5. Job ready for PREVIEW (no rendering yet)
    """
    raw_path = None
    
    try:
        logger.info("="*60)
        logger.info(f"STARTING JOB PROCESSING: {job_id}")
        logger.info("="*60)
        
        job = db.get_job(job_id)
        
        if not job:
            logger.error(f"❌ Job not found in database: {job_id}")
            return
        
        logger.info(f"Job type: {job.get('source_type', 'unknown')}")
        logger.info(f"Source: {job.get('source_url', job.get('raw_path', 'unknown'))}")
        
        # Define paths
        raw_path_youtube = RAW_DIR / f"{job_id}.mp4"
        transcript_path = TRANSCRIPTS_DIR / f"{job_id}.json"
        
        # ===== Step 1: Acquire =====
        logger.info("-"*60)
        logger.info("STEP 1: ACQUIRE VIDEO")
        logger.info("-"*60)
        db.update_job(job_id, status='processing', step='acquire', progress=10)
        
        if job['source_type'] == 'youtube':
            raw_path = raw_path_youtube
            
            # Progress callback to update job progress (maps download 0-100% to job 10-30%)
            def update_download_progress(percent, message):
                job_progress = 10 + int(percent * 0.2)
                db.update_job(job_id, progress=job_progress, step=f'download: {message}')
                logger.debug(f"Download progress: {percent}% -> Job progress: {job_progress}%")
            
            if raw_path.exists():
                file_size = raw_path.stat().st_size
                logger.info(f"✓ Raw file already exists: {raw_path} ({file_size / 1024 / 1024:.1f} MB)")
                logger.info("Skipping download")
            else:
                logger.info(f"Starting YouTube download...")
                logger.info(f"URL: {job['source_url']}")
                logger.info(f"Output: {raw_path}")
                
                success, error_message = download_youtube(
                    job['source_url'], 
                    raw_path,
                    progress_callback=update_download_progress
                )
                
                if not success:
                    error_msg = f"YouTube download failed: {error_message or 'Unknown error'}"
                    logger.error(f"❌ {error_msg}")
                    db.update_job(
                        job_id, 
                        status='failed', 
                        error=error_msg
                    )
                    # Notify webhook
                    if job.get('webhook_url'):
                        notify_webhook(job['webhook_url'], {
                            "job_id": job_id, 
                            "status": "failed", 
                            "error": error_msg
                        })
                    return
                
                logger.info(f"✓ Download successful: {raw_path}")
        else:
            # Upload case
            raw_path = Path(job['raw_path']) if job.get('raw_path') else None
            if not raw_path or not raw_path.exists():
                error_msg = 'Upload file not found or path not set'
                logger.error(f"❌ {error_msg}")
                db.update_job(job_id, status='failed', error=error_msg)
                return
            
            file_size = raw_path.stat().st_size
            logger.info(f"✓ Using uploaded file: {raw_path} ({file_size / 1024 / 1024:.1f} MB)")
        
        db.update_job(job_id, raw_path=str(raw_path), progress=30)
        logger.info(f"✓ Step 1 complete - Video acquired")
        
        # ===== Step 2: Transcribe (directly from raw) =====
        logger.info("-"*60)
        logger.info("STEP 2: TRANSCRIBE VIDEO")
        logger.info("-"*60)
        db.update_job(job_id, step='transcribe', progress=40)
        
        if transcript_path.exists():
            logger.info(f"✓ Transcript already exists: {transcript_path}")
            logger.info("Skipping transcription")
        else:
            logger.info(f"Starting transcription...")
            logger.info(f"Input: {raw_path}")
            logger.info(f"Output: {transcript_path}")
            
            if not transcribe_video(raw_path, transcript_path):
                error_msg = 'Transcription failed - video may not have audio or audio format is not supported'
                logger.error(f"❌ {error_msg}")
                db.update_job(job_id, status='failed', error=error_msg)
                return
            
            logger.info(f"✓ Transcription successful")
        
        db.update_job(job_id, progress=60)
        logger.info(f"✓ Step 2 complete - Transcription ready")
        
        # ===== Step 3: Generate highlights =====
        logger.info("-"*60)
        logger.info("STEP 3: GENERATE HIGHLIGHTS")
        logger.info("-"*60)
        db.update_job(job_id, step='generate_highlights', progress=70)
        
        existing_clips = db.get_clips_by_job(job_id)
        
        if existing_clips:
            logger.info(f"✓ Clips already exist: {len(existing_clips)} clips")
            logger.info("Skipping highlight generation")
        else:
            logger.info(f"Loading transcript from: {transcript_path}")
            transcript = load_transcript(transcript_path)
            
            if not transcript or not transcript.get('segments'):
                error_msg = 'No transcript data found - transcription may have failed'
                logger.error(f"❌ {error_msg}")
                db.update_job(job_id, status='failed', error=error_msg)
                return
            
            logger.info(f"Transcript loaded: {len(transcript.get('segments', []))} segments")
            logger.info("Generating highlights...")
            
            highlights = generate_highlights(transcript)
            
            if not highlights:
                error_msg = 'No highlights generated - video may not have enough spoken content'
                logger.error(f"❌ {error_msg}")
                db.update_job(job_id, status='failed', error=error_msg)
                return
            
            logger.info(f"✓ Generated {len(highlights)} highlight clips")
            
            # Create clips with thumbnails
            logger.info("-"*60)
            logger.info("STEP 4: CREATE CLIPS AND THUMBNAILS")
            logger.info("-"*60)
            db.update_job(job_id, step='create_clips', progress=80)
            
            for i, hl in enumerate(highlights):
                clip_id = str(uuid.uuid4())
                
                logger.info(f"Creating clip {i+1}/{len(highlights)}: {hl['title']}")
                logger.info(f"  Time: {hl['start']:.1f}s - {hl['end']:.1f}s (duration: {hl['end'] - hl['start']:.1f}s)")
                logger.info(f"  Score: {hl['score']:.2f}")
                
                mid_time = (hl['start'] + hl['end']) / 2
                thumbnail_path = THUMBNAILS_DIR / f"{clip_id}.jpg"
                
                logger.debug(f"  Generating thumbnail at {mid_time:.1f}s...")
                generate_thumbnail(raw_path, mid_time, thumbnail_path)
                
                if thumbnail_path.exists():
                    logger.debug(f"  ✓ Thumbnail created: {thumbnail_path}")
                else:
                    logger.warning(f"  ⚠ Thumbnail generation failed")
                
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
                
                logger.debug(f"  ✓ Clip saved to database: {clip_id}")
            
            logger.info(f"✓ All clips created successfully")
        
        # ===== Done - Ready for Preview =====
        logger.info("-"*60)
        logger.info("JOB COMPLETE - READY FOR PREVIEW")
        logger.info("-"*60)
        db.update_job(job_id, status='ready', step='preview_ready', progress=100)
        logger.info(f"✓ Job {job_id} is ready for preview and rendering")
        
        # Notify webhook if set
        job = db.get_job(job_id)
        if job and job.get('webhook_url'):
            logger.info(f"Sending success webhook notification")
            notify_webhook(job['webhook_url'], {"job_id": job_id, "status": "ready"})
        
        logger.info("="*60)
        logger.info(f"✓ JOB PROCESSING COMPLETE: {job_id}")
        logger.info("="*60)
        
    except Exception as e:
        error_msg = f"Unexpected error during job processing: {str(e)}"
        logger.error("="*60)
        logger.error(f"❌ JOB PROCESSING FAILED: {job_id}")
        logger.error("="*60)
        logger.error(error_msg, exc_info=True)
        
        db.update_job(job_id, status='failed', error=error_msg)
        
        # Notify webhook if set
        job = db.get_job(job_id)
        if job and job.get('webhook_url'):
            notify_webhook(job['webhook_url'], {
                "job_id": job_id, 
                "status": "failed", 
                "error": error_msg
            })

def process_render(render_id: str):
    """
    Process render job
    1. Get clip and render details
    2. Render vertical video from raw video
    """
    try:
        logger.info("="*60)
        logger.info(f"STARTING RENDER PROCESSING: {render_id}")
        logger.info("="*60)
        
        render = db.get_render(render_id)
        
        if not render:
            logger.error(f"❌ Render not found in database: {render_id}")
            return
        
        logger.info(f"Render options: {render.get('options', {})}")
        
        clip = db.get_clip(render['clip_id'])
        if not clip:
            error_msg = 'Clip not found'
            logger.error(f"❌ {error_msg}")
            db.update_render(render_id, status='failed', error=error_msg)
            return
        
        logger.info(f"Clip ID: {clip['id']}")
        logger.info(f"Clip time: {clip['start_sec']:.1f}s - {clip['end_sec']:.1f}s")
        
        job = db.get_job(clip['job_id'])
        if not job or not job.get('raw_path'):
            error_msg = 'Job video not found or raw_path not set'
            logger.error(f"❌ {error_msg}")
            db.update_render(render_id, status='failed', error=error_msg)
            return
        
        logger.info(f"Job ID: {job['id']}")
        
        raw_path = Path(job['raw_path'])
        if not raw_path.exists():
            error_msg = f'Raw video file not found: {raw_path}'
            logger.error(f"❌ {error_msg}")
            db.update_render(render_id, status='failed', error=error_msg)
            return
        
        file_size = raw_path.stat().st_size
        logger.info(f"Source video: {raw_path} ({file_size / 1024 / 1024:.1f} MB)")
        
        # Update status
        db.update_render(render_id, status='processing', progress=10)
        
        # Get options
        options = render.get('options', {})
        face_tracking = options.get('face_tracking', False)
        smart_crop = options.get('smart_crop', False)
        captions = options.get('captions', False)
        
        logger.info(f"Render settings:")
        logger.info(f"  - Face tracking: {face_tracking}")
        logger.info(f"  - Smart crop: {smart_crop}")
        logger.info(f"  - Captions: {captions}")
        
        # Output path
        output_path = RENDERS_DIR / f"{render_id}.mp4"
        
        # Check if render output already exists (resume case - unlikely but handle it)
        if output_path.exists():
            logger.info(f"✓ Render output already exists: {output_path}")
            db.update_render(
                render_id,
                status='ready',
                progress=100,
                output_path=str(output_path)
            )
            return
        
        # Render
        logger.info("-"*60)
        logger.info("RENDERING VIDEO")
        logger.info("-"*60)
        db.update_render(render_id, progress=30)
        
        logger.info(f"Starting render process...")
        logger.info(f"Output: {output_path}")
        
        s3_url = render_clip(
            video_path=raw_path,
            output_path=output_path,
            start_sec=clip['start_sec'],
            end_sec=clip['end_sec'],
            face_tracking=face_tracking,
            smart_crop=smart_crop,
            captions=captions,
            transcript_snippet=clip.get('transcript_snippet', '')
        )
        
        if not s3_url:
            error_msg = 'Render failed - check logs for details'
            logger.error(f"❌ {error_msg}")
            db.update_render(render_id, status='failed', error=error_msg)
            return
        
        # Verify output exists
        if not output_path.exists():
            error_msg = 'Render completed but output file not found'
            logger.error(f"❌ {error_msg}")
            db.update_render(render_id, status='failed', error=error_msg)
            return
        
        output_size = output_path.stat().st_size
        logger.info(f"✓ Render successful: {output_path} ({output_size / 1024 / 1024:.1f} MB)")
        
        # Done
        db.update_render(
            render_id,
            status='ready',
            progress=100,
            output_path=str(output_path)
        )
        
        logger.info("="*60)
        logger.info(f"✓ RENDER COMPLETE: {render_id}")
        logger.info("="*60)
        
        # Notify webhook if set
        render = db.get_render(render_id)
        if render and render.get('webhook_url'):
            logger.info(f"Sending success webhook notification")
            notify_webhook(render['webhook_url'], {"render_id": render_id, "status": "ready"})
        
    except Exception as e:
        error_msg = f"Unexpected error during render processing: {str(e)}"
        logger.error("="*60)
        logger.error(f"❌ RENDER PROCESSING FAILED: {render_id}")
        logger.error("="*60)
        logger.error(error_msg, exc_info=True)
        
        db.update_render(render_id, status='failed', error=error_msg)
        
        # Notify webhook if set
        render = db.get_render(render_id)
        if render and render.get('webhook_url'):
            notify_webhook(render['webhook_url'], {
                "render_id": render_id, 
                "status": "failed", 
                "error": error_msg
            })
