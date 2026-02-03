"""FastAPI application for Antariks Clipper"""
import logging
import os
import uuid
import json
from pathlib import Path
from typing import Optional, List, Dict

import db

from fastapi import (
    FastAPI, HTTPException, UploadFile, File, Form, Response,
    Request, Body, Header
)
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import RAW_DIR
import config
from services.cloud import upload_file_to_s3
from services.jobs import submit_job, submit_render
from services.preview import generate_preview_stream, get_preview_frame
from services.license import validate_license, get_license_status, check_license_valid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Init DB
db.init_db()

# Create app (INI WAJIB ADA DI ATAS SEBELUM ROUTES)
app = FastAPI(title="Antariks Clipper API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint to verify API is running"""
    return {
        "status": "healthy",
        "service": "Antariks Clipper API",
        "version": "1.0.0"
    }


# ==================== LICENSE ENDPOINTS ====================

class LicenseValidateRequest(BaseModel):
    license_key: Optional[str] = None

@app.post("/api/license/validate")
async def license_validate(payload: LicenseValidateRequest = None):
    """
    Validate license - single endpoint for all license operations.
    
    Request body (optional):
    - license_key: New license key for activation (if provided, activates new license)
    - If no license_key provided, checks existing license from storage
    
    Always sends to external server:
    - license_key: from request or from storage
    - product_code: from engine (obfuscated)
    - account: MAC address
    
    Response:
    - valid: true/false
    - owner: owner name (if valid)
    - expires: expiration date YYYY-MM-DD (if valid)
    - error: error message (if not valid)
    """
    try:
        # Extract license_key from payload if provided
        license_key = None
        if payload and payload.license_key:
            license_key = payload.license_key
        
        result = await validate_license(license_key)
        
        if not result.get("valid"):
            # Return error but with 200 status to match spec
            return result
        
        logger.info(f"License valid for {result.get('owner')}")
        return result
        
    except Exception as e:
        logger.error(f"License validation error: {e}")
        return {
            "valid": False,
            "error": f"License validation failed: {str(e)}"
        }


# License middleware - checks license on protected endpoints
@app.middleware("http")
async def license_middleware(request: Request, call_next):
    """
    Middleware to check license validity for all API endpoints.
    Excludes license endpoints and health check.
    """
    # Normalize path by removing trailing slash
    path = request.url.path.rstrip('/')
    
    # Skip these paths completely
    skip_paths = [
        "/health",
        "/api/license",  # All license endpoints
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico"
    ]
    
    # Check if should skip
    should_skip = any(path.startswith(p) or path == p for p in skip_paths)
    
    if not should_skip and path.startswith("/api"):
        try:
            status = get_license_status()
            logger.debug(f"License check for {path}: activated={status.get('activated')}, valid={status.get('valid')}")
            
            if not status.get("activated"):
                return Response(
                    content=json.dumps({"detail": "License not activated. Please activate your license first."}),
                    status_code=401,
                    media_type="application/json"
                )
            
            if not status.get("valid"):
                return Response(
                    content=json.dumps({
                        "detail": status.get("error", "License is invalid or expired")
                    }),
                    status_code=403,
                    media_type="application/json"
                )
        except Exception as e:
            logger.error(f"License check error: {e}")
            return Response(
                content=json.dumps({"detail": "License validation error"}),
                status_code=500,
                media_type="application/json"
            )
    
    response = await call_next(request)
    return response


# Models
class AutomateRequest(BaseModel):
    source_type: str
    youtube_url: Optional[str] = None
    file_url: Optional[str] = None
    clips: Optional[list] = None  # List of {start_sec, end_sec, title}
    render_options: Optional[dict] = None  # face_tracking, captions, watermark_text
    webhook_url: Optional[str] = None

@app.post("/api/automate")
async def automate(
    payload: AutomateRequest = Body(...)
):
    """
    Automate: create job, create clips, render batch, and register webhook in one call.
    - source_type: 'youtube' or 'upload'
    - youtube_url or file_url (file_url: public URL to video file)
    - clips: list of {start_sec, end_sec, title}
    - render_options: dict for batch render
    - webhook_url: optional, for job/render status
    """
    import requests
    try:
        # 1. Create job
        job_id = str(uuid.uuid4())
        if payload.source_type == 'youtube':
            job = db.create_job(job_id, source_type='youtube', source_url=payload.youtube_url)
            submit_job(job_id)
        elif payload.source_type == 'upload':
            # Download file_url to RAW_DIR
            if not payload.file_url:
                raise HTTPException(status_code=400, detail='file_url required for upload')
            file_ext = Path(payload.file_url).suffix or '.mp4'
            raw_path = RAW_DIR / f"{job_id}_upload{file_ext}"
            r = requests.get(payload.file_url, stream=True)
            with open(raw_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            job = db.create_job(job_id, source_type='upload')
            db.update_job(job_id, raw_path=str(raw_path))
            submit_job(job_id)
        else:
            raise HTTPException(status_code=400, detail='Invalid source_type')

        # 2. Register webhook if provided
        if payload.webhook_url:
            db.update_job(job_id, webhook_url=payload.webhook_url)

        # 3. Wait until job.status == 'ready' (simple polling, max 60s)
        import time
        for _ in range(60):
            job = db.get_job(job_id)
            if job and job.get('status') == 'ready':
                break
            time.sleep(1)
        else:
            raise HTTPException(status_code=504, detail='Job not ready after 60s')

        # 4. Create clips if provided
        created_clips = []
        if payload.clips:
            for clip in payload.clips:
                clip_id = str(uuid.uuid4())
                db.create_clip(
                    clip_id=clip_id,
                    job_id=job_id,
                    start_sec=clip['start_sec'],
                    end_sec=clip['end_sec'],
                    score=clip.get('score', 0),
                    title=clip.get('title', ''),
                    transcript_snippet=clip.get('transcript_snippet', ''),
                    thumbnail_path=""
                )
                created_clips.append(clip_id)

        # 5. Render all clips (batch) if render_options provided
        render_ids = []
        if payload.render_options and created_clips:
            for clip_id in created_clips:
                render_id = str(uuid.uuid4())
                db.create_render(
                    render_id=render_id,
                    clip_id=clip_id,
                    options=payload.render_options
                )
                submit_render(render_id)
                render_ids.append(render_id)

        return {
            "job_id": job_id,
            "created_clips": created_clips,
            "render_ids": render_ids,
            "status": "queued"
        }
    except Exception as e:
        logger.error(f"Automate error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
# Analytics endpoint
@app.get("/api/analytics")
def get_analytics():
    """Simple analytics: total jobs, clips, renders, latest jobs/clips"""
    try:
        total_jobs = db.count_jobs()
        total_clips = db.count_clips()
        total_renders = db.count_renders()
        latest_jobs = db.get_all_jobs(limit=5)
        latest_clips = db.get_latest_clips(limit=5)
        return {
            "total_jobs": total_jobs,
            "total_clips": total_clips,
            "total_renders": total_renders,
            "latest_jobs": latest_jobs,
            "latest_clips": latest_clips
        }
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Models
class YouTubeJobCreate(BaseModel):
    source_type: str = "youtube"
    youtube_url: str

class WebhookRegister(BaseModel):
    webhook_url: str

class ClipCreate(BaseModel):
    start_sec: float
    end_sec: float
    score: float = 0
    title: str = ""
    transcript_snippet: str = ""
    thumbnail_path: str = ""

class MultiClipCreate(BaseModel):
    clips: List[ClipCreate]

class RenderCreate(BaseModel):
    face_tracking: bool = False
    smart_crop: bool = False
    captions: bool = False
    watermark_text: str = ""

# Webhook registration endpoints
@app.post("/api/jobs/{job_id}/webhook")
def register_job_webhook(job_id: str, payload: WebhookRegister):
    """Register a webhook URL for job status notification"""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.update_job(job_id, webhook_url=payload.webhook_url)
    return {"job_id": job_id, "webhook_url": payload.webhook_url}

@app.post("/api/renders/{render_id}/webhook")
def register_render_webhook(render_id: str, payload: WebhookRegister):
    """Register a webhook URL for render status notification"""
    render = db.get_render(render_id)
    if not render:
        raise HTTPException(status_code=404, detail="Render not found")
    db.update_render(render_id, webhook_url=payload.webhook_url)
    return {"render_id": render_id, "webhook_url": payload.webhook_url}
# Routes
@app.post("/api/jobs/{job_id}/clips")
def create_clips(job_id: str, payload: MultiClipCreate):
    """Create multiple clips for a job"""
    try:
        from services.caption_generator import generate_caption, generate_hashtags
        
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        created = []
        for clip in payload.clips:
            clip_id = str(uuid.uuid4())
            
            # Generate caption and hashtags for manually created clips
            caption = generate_caption(
                title=clip.title,
                transcript_snippet=clip.transcript_snippet,
                metadata={}
            )
            hashtags = generate_hashtags(
                title=clip.title,
                transcript_snippet=clip.transcript_snippet,
                metadata={}
            )
            
            new_clip = db.create_clip(
                clip_id=clip_id,
                job_id=job_id,
                start_sec=clip.start_sec,
                end_sec=clip.end_sec,
                score=clip.score,
                title=clip.title,
                transcript_snippet=clip.transcript_snippet,
                thumbnail_path=clip.thumbnail_path,
                caption_text=caption,
                hashtags_text=hashtags
            )
            created.append(new_clip)
        return {"created": created, "count": len(created)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create multi-clip error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Routes
@app.get("/")
def read_root():
    return {"message": "Antariks Clipper API", "version": "1.0.0"}


# --- SaaS Licensing: require license_key in job creation ---
from fastapi import Header

@app.post("/api/jobs")
async def create_job(
    source_type: str = Form(...),
    youtube_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    license_key: Optional[str] = Header(None, alias="X-License-Key")
):
    """
    Create a new job (requires valid license)
    - YouTube: source_type=youtube, youtube_url=...
    - Upload: source_type=upload, file=...
    """
    # --- License check ---
    # Check local license first (from validate endpoint)
    license_status = get_license_status()
    
    if not license_status.get("activated"):
        raise HTTPException(status_code=401, detail="License not activated. Please activate your license first.")
    
    if not license_status.get("valid"):
        raise HTTPException(status_code=403, detail=license_status.get("error", "License is invalid or expired"))

    try:
        job_id = str(uuid.uuid4())
        if source_type == "youtube":
            if not youtube_url:
                raise HTTPException(status_code=400, detail="youtube_url required")
            # Create job
            job = db.create_job(job_id, source_type="youtube", source_url=youtube_url)
            # Submit to background processing
            submit_job(job_id)
            log_action(None, "create_job", f"Job created: {job_id}")
            return {"job_id": job_id, "status": "queued"}
        elif source_type == "upload":
            if not file:
                raise HTTPException(status_code=400, detail="file required")
            # Save uploaded file locally
            file_ext = Path(file.filename).suffix if file.filename else ".mp4"
            raw_path = RAW_DIR / f"{job_id}_upload{file_ext}"
            content = await file.read()
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            with open(raw_path, "wb") as f:
                f.write(content)
            # Upload to S3
            s3_key = f"uploads/{job_id}{file_ext}"
            try:
                s3_url = upload_file_to_s3(raw_path, s3_key)
            except Exception as e:
                logger.error(f"S3 upload error: {e}")
                s3_url = None
            # Create job
            job = db.create_job(job_id, source_type="upload")
            db.update_job(job_id, raw_path=str(raw_path))
            # Submit to background processing
            submit_job(job_id)
            log_action(None, "create_job", f"Job created: {job_id}")
            return {"job_id": job_id, "status": "queued"}
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
def list_jobs(page: int = 1, limit: int = 20):
    """
    List all jobs with pagination
    
    Args:
        page: Page number (1-indexed)
        limit: Number of jobs per page (max 100)
    
    Returns:
        jobs: List of jobs
        page: Current page
        limit: Items per page
        total: Total number of jobs
        total_pages: Total number of pages
    """
    try:
        # Validate and constrain parameters
        page = max(1, page)
        limit = max(1, min(100, limit))
        offset = (page - 1) * limit
        
        # Get jobs and total count
        jobs = db.get_all_jobs(limit=limit, offset=offset)
        total = db.get_total_jobs_count()
        total_pages = max(1, (total + limit - 1) // limit)  # Ceiling division, min 1
        
        return {
            "jobs": jobs,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"List jobs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    """Get job details"""
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/retry")
def retry_job(job_id: str):
    """
    Retry a failed job from the last failed step.
    If files from previous steps exist, resume from there.
    """
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job['status'] not in ['failed', 'ready']:
            raise HTTPException(
                status_code=400, 
                detail=f"Can only retry failed or ready jobs. Current status: {job['status']}"
            )
        
        # Reset job status
        db.update_job(
            job_id, 
            status='queued', 
            error=None,
            progress=0
        )
        
        # Submit to background processing (will resume from appropriate step)
        submit_job(job_id)
        
        return {
            "job_id": job_id, 
            "status": "queued",
            "message": "Job requeued for processing"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    """
    Delete a job and all associated data including:
    - All clips and renders
    - Raw video file
    - Normalized video file
    - Transcripts
    - Thumbnails
    - Rendered videos
    - Any temporary or partial download files
    
    Note: Only jobs with status 'ready' can be deleted to prevent deletion
    of jobs that are still being processed or downloaded.
    """
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if job status allows deletion
        job_status = job.get('status', '')
        if job_status != 'ready':
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot delete job with status '{job_status}'. Only jobs with status 'ready' can be deleted. Please wait for the job to complete or fail completely before deleting."
            )
        
        logger.info(f"=== Starting deletion for job {job_id} ===")
        
        # Get all associated data before deletion
        clips = db.get_clips_by_job(job_id)
        renders = db.get_renders_by_job(job_id)
        
        logger.info(f"Found {len(clips)} clips and {len(renders)} renders to delete")
        
        # Delete files
        files_to_delete = []
        
        # Add job files
        if job.get('raw_path'):
            files_to_delete.append(job['raw_path'])
            # Also check for potential partial/temp files with same base name
            raw_path = Path(job['raw_path'])
            base_name = raw_path.stem
            for ext in ['.part', '.temp', '.tmp', '.ytdl']:
                temp_file = raw_path.parent / f"{base_name}{ext}"
                if temp_file.exists():
                    files_to_delete.append(str(temp_file))
        
        if job.get('normalized_path'):
            files_to_delete.append(job['normalized_path'])
        
        # Add transcript file
        transcript_path = Path(config.TRANSCRIPTS_DIR) / f"{job_id}.json"
        if transcript_path.exists():
            files_to_delete.append(str(transcript_path))
        
        # Check for any other transcript-related files
        for ext in ['.txt', '.srt', '.vtt']:
            alt_transcript = Path(config.TRANSCRIPTS_DIR) / f"{job_id}{ext}"
            if alt_transcript.exists():
                files_to_delete.append(str(alt_transcript))
        
        # Add clip thumbnails
        for clip in clips:
            if clip.get('thumbnail_path'):
                files_to_delete.append(clip['thumbnail_path'])
        
        # Add render output files
        for render in renders:
            if render.get('output_path'):
                files_to_delete.append(render['output_path'])
        
        # Check for any orphaned files with this job_id in various directories
        for directory in [config.RAW_DIR, config.NORMALIZED_DIR, config.TRANSCRIPTS_DIR, 
                         config.THUMBNAILS_DIR, config.RENDERS_DIR]:
            if directory.exists():
                for file_path in directory.glob(f"{job_id}*"):
                    file_str = str(file_path)
                    if file_str not in files_to_delete:
                        files_to_delete.append(file_str)
                        logger.info(f"Found orphaned file: {file_path}")
        
        logger.info(f"Total files to delete: {len(files_to_delete)}")
        
        # Delete files from filesystem
        deleted_files = []
        failed_files = []
        total_size_freed = 0
        for file_path in files_to_delete:
            try:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    total_size_freed += file_size
                    logger.info(f"✓ Deleted file: {file_path} ({file_size / 1024 / 1024:.2f} MB)")
                else:
                    logger.debug(f"File not found (already deleted?): {file_path}")
            except Exception as e:
                logger.error(f"❌ Failed to delete file {file_path}: {e}")
                failed_files.append(file_path)
        
        # Delete database records (cascading deletion)
        db.delete_job(job_id)
        
        logger.info(f"✓ Job {job_id} deleted successfully")
        logger.info(f"  - Files deleted: {len(deleted_files)}")
        logger.info(f"  - Failed deletions: {len(failed_files)}")
        logger.info(f"  - Disk space freed: {total_size_freed / 1024 / 1024:.2f} MB")
        
        return {
            "message": "Job deleted successfully",
            "job_id": job_id,
            "files_deleted": len(deleted_files),
            "files_failed": len(failed_files),
            "failed_files": failed_files if failed_files else None,
            "space_freed_mb": round(total_size_freed / 1024 / 1024, 2)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}/clips")
def get_job_clips(job_id: str):
    """Get all clips for a job"""
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        clips = db.get_clips_by_job(job_id)
        return {"clips": clips}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get clips error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RegenerateHighlightsRequest(BaseModel):
    clip_count: Optional[int] = None  # None = auto-calculate
    adaptive: bool = True


@app.post("/api/jobs/{job_id}/regenerate-highlights")
def regenerate_highlights(job_id: str, payload: RegenerateHighlightsRequest):
    """
    Regenerate highlight clips for a job with custom parameters.
    Deletes existing clips and generates new ones.
    """
    try:
        from services.transcribe import load_transcript
        from services.highlight import generate_highlights
        from services.thumbnails import generate_thumbnail
        from services.caption_generator import generate_caption, generate_hashtags
        from pathlib import Path
        
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job['status'] != 'ready':
            raise HTTPException(
                status_code=400, 
                detail=f"Job must be in 'ready' status to regenerate highlights. Current: {job['status']}"
            )
        
        # Load transcript
        transcript_path = Path(config.TRANSCRIPTS_DIR) / f"{job_id}.json"
        if not transcript_path.exists():
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        transcript = load_transcript(transcript_path)
        if not transcript or not transcript.get('segments'):
            raise HTTPException(status_code=400, detail="Invalid transcript data")
        
        logger.info(f"Regenerating highlights for job {job_id}")
        logger.info(f"  Clip count: {payload.clip_count or 'auto'}")
        logger.info(f"  Adaptive: {payload.adaptive}")
        
        # Delete existing clips
        existing_clips = db.get_clips_by_job(job_id)
        for clip in existing_clips:
            # Delete thumbnail if exists
            if clip.get('thumbnail_path'):
                try:
                    Path(clip['thumbnail_path']).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to delete thumbnail: {e}")
            
            # Delete clip from database using db function
            db.delete_clip(clip['id'])
        
        logger.info(f"Deleted {len(existing_clips)} existing clips")
        
        # Generate new highlights
        highlights = generate_highlights(
            transcript, 
            top_n=payload.clip_count,
            adaptive=payload.adaptive
        )
        
        if not highlights:
            raise HTTPException(status_code=500, detail="Failed to generate highlights")
        
        # Get raw video path for thumbnails
        raw_path = Path(job['raw_path']) if job.get('raw_path') else None
        if not raw_path or not raw_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # Create new clips with thumbnails
        created_clips = []
        for i, hl in enumerate(highlights):
            clip_id = str(uuid.uuid4())
            
            logger.info(f"Creating clip {i+1}/{len(highlights)}: {hl['title']}")
            
            mid_time = (hl['start'] + hl['end']) / 2
            thumbnail_path = Path(config.THUMBNAILS_DIR) / f"{clip_id}.jpg"
            
            generate_thumbnail(raw_path, mid_time, thumbnail_path)
            
            # Generate caption and hashtags
            caption = generate_caption(
                title=hl['title'],
                transcript_snippet=hl['snippet'],
                metadata=hl.get('metadata', {})
            )
            hashtags = generate_hashtags(
                title=hl['title'],
                transcript_snippet=hl['snippet'],
                metadata=hl.get('metadata', {})
            )
            
            clip = db.create_clip(
                clip_id=clip_id,
                job_id=job_id,
                start_sec=hl['start'],
                end_sec=hl['end'],
                score=hl['score'],
                title=hl['title'],
                transcript_snippet=hl['snippet'],
                thumbnail_path=str(thumbnail_path) if thumbnail_path.exists() else "",
                metadata=hl.get('metadata', {}),
                caption_text=caption,
                hashtags_text=hashtags
            )
            created_clips.append(clip)
        
        logger.info(f"Created {len(created_clips)} new clips")
        
        return {
            "success": True,
            "deleted": len(existing_clips),
            "created": len(created_clips),
            "clips": created_clips
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regenerate highlights error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@app.delete("/api/clips/{clip_id}")
def delete_clip_endpoint(clip_id: str):
    """
    Delete a clip and its associated renders and files
    """
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        logger.info(f"Deleting clip {clip_id}")
        
        # Get associated renders
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM renders WHERE clip_id = ?", (clip_id,))
        renders = [dict(row) for row in cursor.fetchall()]
        
        # Delete render files and records
        for render in renders:
            if render.get('output_path'):
                try:
                    Path(render['output_path']).unlink(missing_ok=True)
                    logger.info(f"  Deleted render file: {render['output_path']}")
                except Exception as e:
                    logger.warning(f"  Failed to delete render file: {e}")
            
            cursor.execute("DELETE FROM renders WHERE id = ?", (render['id'],))
        
        # Delete thumbnail
        if clip.get('thumbnail_path'):
            try:
                Path(clip['thumbnail_path']).unlink(missing_ok=True)
                logger.info(f"  Deleted thumbnail: {clip['thumbnail_path']}")
            except Exception as e:
                logger.warning(f"  Failed to delete thumbnail: {e}")
        
        # Delete clip record using db function
        db.delete_clip(clip_id)
        
        conn.commit()
        conn.close()
        
        logger.info(f"  Deleted clip {clip_id} and {len(renders)} associated renders")
        
        return {
            "success": True,
            "clip_id": clip_id,
            "deleted_renders": len(renders)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete clip error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clips/{clip_id}/render")
def create_render(clip_id: str, options: RenderCreate):
    """Create a render job for a clip"""
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        render_id = str(uuid.uuid4())
        
        # Create render
        render = db.create_render(
            render_id=render_id,
            clip_id=clip_id,
            options=options.dict()
        )
        
        # Submit to background processing
        submit_render(render_id)
        
        return {"render_id": render_id, "status": "queued"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/renders/{render_id}")
def get_render(render_id: str):
    """Get render details"""
    try:
        render = db.get_render(render_id)
        if not render:
            raise HTTPException(status_code=404, detail="Render not found")
        return render
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get render error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/renders/{render_id}/retry")
def retry_render(render_id: str):
    """Retry a failed render"""
    try:
        render = db.get_render(render_id)
        if not render:
            raise HTTPException(status_code=404, detail="Render not found")
        
        if render['status'] not in ['failed']:
            raise HTTPException(
                status_code=400,
                detail=f"Can only retry failed renders. Current status: {render['status']}"
            )
        
        # Reset render status
        db.update_render(
            render_id,
            status='queued',
            error=None,
            progress=0
        )
        
        # Submit to background processing
        submit_render(render_id)
        
        return {
            "render_id": render_id,
            "status": "queued",
            "message": "Render requeued for processing"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/renders/{render_id}/download")
def download_render(render_id: str):
    """Download rendered video"""
    try:
        render = db.get_render(render_id)
        if not render:
            raise HTTPException(status_code=404, detail="Render not found")
        
        if render['status'] != 'ready' or not render.get('output_path'):
            raise HTTPException(status_code=400, detail="Render not ready")
        
        output_path = Path(render['output_path'])
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Render file not found")
        
        return FileResponse(
            path=str(output_path),
            media_type="video/mp4",
            filename=f"clip_{render_id}.mp4"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download render error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/thumbnails/{clip_id}")
def get_thumbnail(clip_id: str):
    """Get clip thumbnail"""
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        if not clip.get('thumbnail_path'):
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        thumbnail_path = Path(clip['thumbnail_path'])
        if not thumbnail_path.exists():
            raise HTTPException(status_code=404, detail="Thumbnail file not found")
        
        return FileResponse(
            path=str(thumbnail_path),
            media_type="image/jpeg"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get thumbnail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clips/{clip_id}/preview")
async def get_clip_preview(clip_id: str, face_tracking: bool = True):
    """
    Stream preview of clip with 9:16 crop and optional face tracking.
    Returns low-res preview video for fast playback.
    """
    preview_path = None
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        job = db.get_job(clip['job_id'])
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Use raw_path (not normalized)
        video_path = Path(job['raw_path']) if job.get('raw_path') else None
        if not video_path or not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # Generate preview
        preview_path = generate_preview_stream(
            video_path,
            clip['start_sec'],
            clip['end_sec'],
            face_tracking=face_tracking
        )
        
        if not preview_path or not preview_path.exists():
            raise HTTPException(status_code=500, detail="Preview generation failed")
        
        # Stream the file and cleanup after
        def iterfile():
            try:
                with open(preview_path, 'rb') as f:
                    yield from f
            finally:
                # Cleanup temp file even if streaming is interrupted
                try:
                    if preview_path and preview_path.exists():
                        os.unlink(preview_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup preview file: {e}")
        
        return StreamingResponse(
            iterfile(),
            media_type="video/mp4",
            headers={"Content-Disposition": f"inline; filename=preview_{clip_id}.mp4"}
        )
        
    except HTTPException:
        # Cleanup on error
        if preview_path and preview_path.exists():
            try:
                os.unlink(preview_path)
            except Exception:
                pass
        raise
    except Exception as e:
        # Cleanup on error
        if preview_path and preview_path.exists():
            try:
                os.unlink(preview_path)
            except Exception:
                pass
        logger.error(f"Preview error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/clips/{clip_id}/preview-frame")
async def get_clip_preview_frame(clip_id: str, face_tracking: bool = True):
    """
    Get single preview frame (thumbnail) with 9:16 crop.
    """
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        job = db.get_job(clip['job_id'])
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        video_path = Path(job['raw_path']) if job.get('raw_path') else None
        if not video_path or not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        mid_time = (clip['start_sec'] + clip['end_sec']) / 2
        duration = clip['end_sec'] - clip['start_sec']
        
        frame_bytes = get_preview_frame(
            video_path,
            mid_time,
            face_tracking=face_tracking,
            duration=duration
        )
        
        if not frame_bytes:
            raise HTTPException(status_code=500, detail="Frame extraction failed")
        
        return Response(
            content=frame_bytes,
            media_type="image/jpeg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview frame error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/{job_id}/render-selected")
async def render_selected_clips(
    job_id: str, 
    clip_ids: str,  # Comma-separated clip IDs from query params
    options: RenderCreate
):
    """
    Render only selected clips (batch render).
    """
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Parse comma-separated clip IDs
        clip_id_list = [cid.strip() for cid in clip_ids.split(',') if cid.strip()]
        
        render_ids = []
        for clip_id in clip_id_list:
            clip = db.get_clip(clip_id)
            if not clip or clip['job_id'] != job_id:
                continue
            
            render_id = str(uuid.uuid4())
            db.create_render(
                render_id=render_id,
                clip_id=clip_id,
                options=options.dict()
            )
            submit_render(render_id)
            render_ids.append(render_id)
        
        return {
            "job_id": job_id,
            "render_ids": render_ids,
            "count": len(render_ids),
            "status": "queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
