"""FastAPI application for Antariks Clipper"""
import logging
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import db
from config import RAW_DIR, ALLOWED_ORIGINS, MAX_FILE_SIZE
from services.jobs import submit_job, submit_render
from services.preview import generate_preview_stream, get_preview_frame

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
db.init_db()

# Create FastAPI app
app = FastAPI(title="Antariks Clipper API", version="1.0.0")

# CORS configuration from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Models
class YouTubeJobCreate(BaseModel):
    source_type: str = "youtube"
    youtube_url: str

class RenderCreate(BaseModel):
    face_tracking: bool = False
    captions: bool = False

# Routes
@app.get("/")
def read_root():
    return {"message": "Antariks Clipper API", "version": "1.0.0"}

@app.post("/api/jobs")
async def create_job(
    source_type: str = Form(...),
    youtube_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Create a new job
    - YouTube: source_type=youtube, youtube_url=...
    - Upload: source_type=upload, file=...
    """
    try:
        job_id = str(uuid.uuid4())
        
        if source_type == "youtube":
            if not youtube_url:
                raise HTTPException(status_code=400, detail="youtube_url required")
            
            # Validate YouTube URL format
            if not youtube_url.startswith(('https://www.youtube.com', 'https://youtu.be', 'http://www.youtube.com', 'http://youtu.be')):
                raise HTTPException(status_code=400, detail="Invalid YouTube URL format")
            
            # Create job
            job = db.create_job(job_id, source_type="youtube", source_url=youtube_url)
            
            # Submit to background processing
            submit_job(job_id)
            
            return {"job_id": job_id, "status": "queued"}
        
        elif source_type == "upload":
            if not file:
                raise HTTPException(status_code=400, detail="file required")
            
            # Check file size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413, 
                    detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / (1024**3):.1f}GB"
                )
            
            # Save uploaded file
            file_ext = Path(file.filename).suffix if file.filename else ".mp4"
            raw_path = RAW_DIR / f"{job_id}_upload{file_ext}"
            
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            with open(raw_path, "wb") as f:
                f.write(content)
            
            # Create job
            job = db.create_job(job_id, source_type="upload")
            db.update_job(job_id, raw_path=str(raw_path))
            
            # Submit to background processing
            submit_job(job_id)
            
            return {"job_id": job_id, "status": "queued"}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/jobs")
def list_jobs(limit: int = 100):
    """List all jobs"""
    try:
        jobs = db.get_all_jobs(limit=limit)
        return {"jobs": jobs}
    except Exception as e:
        logger.error(f"List jobs error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

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
        logger.error(f"Get job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

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
        raise HTTPException(status_code=500, detail="Internal server error")

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
        logger.error(f"Get clips error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

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
        raise HTTPException(status_code=500, detail="Internal server error")

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
        logger.error(f"Get render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

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
        raise HTTPException(status_code=500, detail="Internal server error")

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
        logger.error(f"Download render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

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
        logger.error(f"Get thumbnail error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

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
        raise HTTPException(status_code=500, detail="Internal server error")


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
        raise HTTPException(status_code=500, detail="Internal server error")


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
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
