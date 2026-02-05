"""Main FastAPI application with clean route organization"""
import logging
import signal
import sys
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Body, Header, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional
import os
import json
import threading
import time

import db
import config
from schemas import (
    LicenseValidateRequest, WebhookRegister, MultiClipCreate, RenderCreate,
    AutomateRequest, RegenerateHighlightsRequest
)
from handlers_license import handle_license_validation, get_license_middleware_response
from handlers_jobs import (
    handle_create_youtube_job, handle_create_upload_job, handle_automate,
    handle_delete_job, handle_retry_job, handle_cleanup_and_create_youtube_job,
    handle_cancel_job
)
from handlers_clips import handle_create_clips, handle_delete_clip, handle_regenerate_highlights
from handlers_renders import handle_create_render, handle_retry_render, handle_batch_render
from exceptions import AntariksException
from services.preview import generate_preview_stream, get_preview_frame
from utils import log_action

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize database
db.init_db()

# Create FastAPI app
app = FastAPI(
    title="Antariks Clipper API",
    version="1.0.0",
    description="Video clip generation and rendering API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for desktop app (runs locally)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
)


# ==================== MIDDLEWARE ====================

@app.middleware("http")
async def license_check_middleware(request: Request, call_next):
    """Check license validity for protected endpoints"""
    path = request.url.path.rstrip('/')

    skip_paths = ["/health", "/api/license", "/docs", "/redoc", "/openapi.json", "/favicon.ico"]
    should_skip = any(path.startswith(p) or path == p for p in skip_paths)

    if not should_skip and path.startswith("/api"):
        should_continue, error_response = get_license_middleware_response()
        if not should_continue:
            return error_response

    return await call_next(request)


# ==================== HEALTH CHECK ====================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Antariks Clipper API",
        "version": "1.0.0"
    }


# ==================== LICENSE ENDPOINTS ====================

@app.post("/api/license/validate")
async def license_validate(payload: LicenseValidateRequest = None):
    """Validate and activate license"""
    return await handle_license_validation(payload)


# ==================== JOB ENDPOINTS ====================

@app.post("/api/jobs")
async def create_job(
    source_type: str = Form(...),
    youtube_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """Create a new job (YouTube or upload)"""
    try:
        if source_type == "youtube":
            if not youtube_url:
                raise HTTPException(status_code=400, detail="youtube_url required")
            return await handle_create_youtube_job(youtube_url)

        elif source_type == "upload":
            if not file:
                raise HTTPException(status_code=400, detail="file required")
            content = await file.read()
            return await handle_create_upload_job(content, file.filename)

        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")

    except AntariksException as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Create job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create job")


@app.get("/api/jobs")
def list_jobs(page: int = 1, limit: int = 20):
    """List all jobs with pagination"""
    try:
        page = max(1, page)
        limit = max(1, min(100, limit))
        offset = (page - 1) * limit

        jobs = db.get_all_jobs(limit=limit, offset=offset)
        total = db.get_total_jobs_count()
        total_pages = max(1, (total + limit - 1) // limit)

        return {
            "jobs": jobs,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        logger.error(f"List jobs error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list jobs")


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
        raise HTTPException(status_code=500, detail="Failed to get job")


@app.post("/api/jobs/{job_id}/retry")
def retry_job(job_id: str):
    """Retry a failed job"""
    try:
        return handle_retry_job(job_id)
    except AntariksException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Retry job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retry job")


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """Cancel a queued or processing job"""
    try:
        return handle_cancel_job(job_id)
    except AntariksException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Cancel job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel job")


@app.post("/api/jobs/youtube/cleanup-and-create")
async def cleanup_youtube_and_create(youtube_url: str = Body(..., embed=True)):
    """
    Clean up existing job for YouTube URL and create a new one.
    This endpoint:
    1. Finds the existing job (if any) for the YouTube URL
    2. Deletes all associated files and database records
    3. Creates a new job for processing
    
    Use this when you want to re-process a URL that was already processed.
    
    Request body:
    {
        "youtube_url": "https://www.youtube.com/watch?v=..."
    }
    """
    try:
        return await handle_cleanup_and_create_youtube_job(youtube_url)
    except AntariksException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Cleanup and create job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cleanup and create job")


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    """Delete job and all associated data"""
    try:
        return handle_delete_job(job_id)
    except AntariksException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Delete job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete job")


@app.post("/api/automate")
async def automate(payload: AutomateRequest = Body(...)):
    """Automate: create job, clips, render in one call"""
    try:
        return await handle_automate(payload)
    except AntariksException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Automate error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Automation failed")


# ==================== CLIP ENDPOINTS ====================

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
        raise HTTPException(status_code=500, detail="Failed to get clips")


@app.post("/api/jobs/{job_id}/clips")
def create_clips(job_id: str, payload: MultiClipCreate):
    """Create multiple clips for a job"""
    try:
        return handle_create_clips(job_id, payload)
    except AntariksException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Create clips error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create clips")


@app.post("/api/jobs/{job_id}/regenerate-highlights")
def regenerate_highlights(job_id: str, payload: RegenerateHighlightsRequest):
    """Regenerate highlight clips"""
    try:
        return handle_regenerate_highlights(job_id, payload.clip_count, payload.adaptive)
    except AntariksException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Regenerate highlights error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to regenerate highlights")


@app.delete("/api/clips/{clip_id}")
def delete_clip_endpoint(clip_id: str):
    """Delete a clip and associated renders"""
    try:
        return handle_delete_clip(clip_id)
    except AntariksException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Delete clip error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete clip")


@app.post("/api/clips/{clip_id}/generate-caption")
def generate_caption_endpoint(
    clip_id: str,
    style: str = "engaging",
    max_length: int = 150
):
    """Generate AI caption for a clip"""
    try:
        from services.caption_generator import generate_caption_with_ai
        
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        transcript = clip.get('transcript_snippet', '')
        if not transcript:
            raise HTTPException(status_code=400, detail="No transcript available for this clip")
        
        caption = generate_caption_with_ai(transcript, style, max_length)
        if not caption:
            raise HTTPException(status_code=500, detail="Failed to generate caption. Check logs for details.")
        
        return {"caption": caption, "clip_id": clip_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate caption error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate caption: {str(e)}")


@app.post("/api/clips/{clip_id}/generate-hashtags")
def generate_hashtags_endpoint(
    clip_id: str,
    count: int = 10
):
    """Generate AI hashtags for a clip"""
    try:
        from services.caption_generator import generate_hashtags_with_ai
        
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        transcript = clip.get('transcript_snippet', '')
        if not transcript:
            raise HTTPException(status_code=400, detail="No transcript available for this clip")
        
        hashtags = generate_hashtags_with_ai(transcript, count)
        if not hashtags:
            raise HTTPException(status_code=500, detail="Failed to generate hashtags. Check logs for details.")
        
        return {"hashtags": hashtags, "clip_id": clip_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate hashtags error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate hashtags: {str(e)}")


# ==================== RENDER ENDPOINTS ====================

@app.post("/api/clips/{clip_id}/render")
def create_render(clip_id: str, options: RenderCreate):
    """Create a render job for a clip"""
    try:
        return handle_create_render(clip_id, options)
    except AntariksException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Create render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create render")


@app.get("/api/jobs/{job_id}/renders")
def get_job_renders(job_id: str):
    """Get all renders for a job"""
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        renders = db.get_renders_by_job(job_id)
        return {"job_id": job_id, "renders": renders}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job renders error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get job renders")


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
        raise HTTPException(status_code=500, detail="Failed to get render")


@app.post("/api/renders/{render_id}/retry")
def retry_render(render_id: str):
    """Retry a failed render"""
    try:
        return handle_retry_render(render_id)
    except AntariksException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Retry render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retry render")


@app.get("/api/renders/{render_id}/download")
def download_render(render_id: str):
    """Download rendered video - forces browser download instead of opening in new tab"""
    try:
        render = db.get_render(render_id)
        if not render:
            logger.error(f"Render not found in database: {render_id}")
            raise HTTPException(status_code=404, detail="Render not found")
        
        logger.info(f"Download request for render {render_id}, status: {render['status']}")
        
        if render["status"] != "ready":
            logger.error(f"Render not ready: status={render['status']}")
            raise HTTPException(status_code=400, detail=f"Render not ready (status: {render['status']})")
        
        if not render.get("output_path"):
            logger.error(f"Render has no output_path: {render_id}")
            raise HTTPException(status_code=400, detail="Render output path not set")
        
        output_path = Path(render["output_path"])
        logger.info(f"Checking file existence: {output_path}")
        
        if not output_path.exists():
            logger.error(f"Render file not found on disk: {output_path}")
            logger.error(f"Database says: status={render['status']}, output_path={render.get('output_path')}")
            raise HTTPException(status_code=404, detail=f"Render file not found: {output_path.name}")

        file_size = output_path.stat().st_size
        logger.info(f"Serving render file: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
        
        # Force download with Content-Disposition header
        return FileResponse(
            path=str(output_path),
            media_type="video/mp4",
            filename=f"clip_{render_id}.mp4",
            headers={"Content-Disposition": f"attachment; filename=clip_{render_id}.mp4"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to download render")


@app.delete("/api/renders/{render_id}")
def delete_render(render_id: str):
    """Delete render record and file after download completes"""
    try:
        render = db.get_render(render_id)
        if not render:
            raise HTTPException(status_code=404, detail="Render not found")
        
        # Delete file if exists
        if render.get("output_path"):
            output_path = Path(render["output_path"])
            if output_path.exists():
                try:
                    output_path.unlink()
                    logger.info(f"Deleted render file: {output_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete render file {output_path}: {e}")
        
        # Delete render record from database
        db.delete_render(render_id)
        logger.info(f"Deleted render record: {render_id}")
        
        return {"success": True, "message": "Render deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete render error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete render")


@app.post("/api/renders/{render_id}/cancel")
def cancel_render(render_id: str):
    """Cancel a render that is queued or processing"""
    try:
        render = db.get_render(render_id)
        if not render:
            raise HTTPException(status_code=404, detail="Render not found")
        
        status = render.get("status")
        
        # Only allow cancelling queued or processing renders
        if status not in ["queued", "processing"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel render with status: {status}"
            )
        
        # Update status to cancelled
        db.update_render(render_id, status="cancelled", error="Cancelled by user")
        logger.info(f"Cancelled render: {render_id}")
        
        return {"success": True, "message": "Render cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel render error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel render")


@app.post("/api/jobs/{job_id}/render-selected")
async def render_selected_clips(
    job_id: str,
    clip_ids: str,
    options: RenderCreate
):
    """Batch render selected clips"""
    try:
        return handle_batch_render(job_id, clip_ids, options)
    except AntariksException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Batch render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to batch render")


# ==================== PREVIEW ENDPOINTS ====================

@app.get("/api/clips/{clip_id}/preview")
async def get_clip_preview(clip_id: str, face_tracking: bool = True):
    """Stream preview of clip"""
    preview_path = None
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")

        job = db.get_job(clip["job_id"])
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Use raw video for preview (consistent with render, preserves A/V sync)
        video_path = Path(job["raw_path"]) if job.get("raw_path") else None
        if not video_path or not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")

        preview_path = generate_preview_stream(
            video_path,
            clip["start_sec"],
            clip["end_sec"],
            face_tracking=face_tracking
        )

        if not preview_path or not preview_path.exists():
            raise HTTPException(status_code=500, detail="Preview generation failed")

        def iterfile():
            try:
                with open(preview_path, "rb") as f:
                    yield from f
            finally:
                try:
                    if preview_path and preview_path.exists():
                        os.unlink(preview_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup preview: {e}")

        return StreamingResponse(
            iterfile(),
            media_type="video/mp4",
            headers={"Content-Disposition": f"inline; filename=preview_{clip_id}.mp4"}
        )

    except HTTPException:
        if preview_path and preview_path.exists():
            try:
                os.unlink(preview_path)
            except Exception:
                pass
        raise
    except Exception as e:
        if preview_path and preview_path.exists():
            try:
                os.unlink(preview_path)
            except Exception:
                pass
        logger.error(f"Preview error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate preview")


@app.get("/api/clips/{clip_id}/preview-frame")
async def get_clip_preview_frame(clip_id: str, face_tracking: bool = True):
    """Get single preview frame"""
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")

        job = db.get_job(clip["job_id"])
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Use raw video for preview frame (consistent with render, preserves A/V sync)
        video_path = Path(job["raw_path"]) if job.get("raw_path") else None
        if not video_path or not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")

        mid_time = (clip["start_sec"] + clip["end_sec"]) / 2
        duration = clip["end_sec"] - clip["start_sec"]

        frame_bytes = get_preview_frame(
            video_path,
            mid_time,
            face_tracking=face_tracking,
            duration=duration
        )

        if not frame_bytes:
            raise HTTPException(status_code=500, detail="Frame extraction failed")

        return Response(content=frame_bytes, media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview frame error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get preview frame")


# ==================== THUMBNAIL ENDPOINTS ====================

@app.get("/api/thumbnails/{clip_id}")
def get_thumbnail(clip_id: str):
    """Get clip thumbnail"""
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        if not clip.get("thumbnail_path"):
            raise HTTPException(status_code=404, detail="Thumbnail not found")

        thumbnail_path = Path(clip["thumbnail_path"])
        if not thumbnail_path.exists():
            raise HTTPException(status_code=404, detail="Thumbnail file not found")

        return FileResponse(path=str(thumbnail_path), media_type="image/jpeg")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get thumbnail error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get thumbnail")


# ==================== WEBHOOK ENDPOINTS ====================

@app.post("/api/jobs/{job_id}/webhook")
def register_job_webhook(job_id: str, payload: WebhookRegister):
    """Register webhook for job status"""
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        db.update_job(job_id, webhook_url=payload.webhook_url)
        return {"job_id": job_id, "webhook_url": payload.webhook_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Register job webhook error: {e}")
        raise HTTPException(status_code=500, detail="Failed to register webhook")


@app.post("/api/renders/{render_id}/webhook")
def register_render_webhook(render_id: str, payload: WebhookRegister):
    """Register webhook for render status"""
    try:
        render = db.get_render(render_id)
        if not render:
            raise HTTPException(status_code=404, detail="Render not found")
        db.update_render(render_id, webhook_url=payload.webhook_url)
        return {"render_id": render_id, "webhook_url": payload.webhook_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Register render webhook error: {e}")
        raise HTTPException(status_code=500, detail="Failed to register webhook")


# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/api/analytics")
def get_analytics():
    """Get API analytics"""
    try:
        return {
            "total_jobs": db.count_jobs(),
            "total_clips": db.count_clips(),
            "total_renders": db.count_renders(),
            "latest_jobs": db.get_all_jobs(limit=5),
            "latest_clips": db.get_latest_clips(limit=5)
        }
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


# ==================== ROOT ENDPOINT ====================

@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Antariks Clipper API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Received shutdown signal, cleaning up...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
