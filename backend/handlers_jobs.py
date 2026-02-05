"""Job-related route handlers"""
import logging
import uuid
from pathlib import Path
from typing import Optional, Tuple
import requests

import db
import config
from schemas import AutomateRequest
from services.cloud import upload_file_to_s3
from services.jobs import submit_job, submit_render
from utils import log_action, safe_delete_files, collect_job_files_for_deletion
from exceptions import JobException

logger = logging.getLogger(__name__)


def check_existing_youtube_job(youtube_url: str) -> Tuple[Optional[dict], str]:
    """
    Check if YouTube URL already has a processing job.
    
    Args:
        youtube_url: YouTube URL to check
        
    Returns:
        Tuple of (existing_job, status_message)
        - existing_job: Job dict if found, None otherwise
        - status_message: Description of job status
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM jobs WHERE source_type = 'youtube' AND source_url = ? ORDER BY created_at DESC LIMIT 1",
            (youtube_url,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None, ""
        
        job = dict(row)
        job_id = job['id']
        job_status = job.get('status')
        
        if job_status == 'processing':
            message = f"URL masih diproses (Job ID: {job_id}). Tunggu hingga selesai atau hapus job yang sedang berjalan terlebih dahulu."
            logger.warning(f"YouTube URL already processing: {job_id}")
            return job, message
            
        elif job_status == 'queued':
            message = f"URL sedang dalam antrian (Job ID: {job_id}). Tunggu hingga diproses atau hapus job terlebih dahulu."
            logger.warning(f"YouTube URL already queued: {job_id}")
            return job, message
            
        elif job_status == 'ready':
            message = f"URL sudah pernah diproses (Job ID: {job_id}). Silakan hapus job lama terlebih dahulu jika ingin memproses ulang."
            logger.info(f"YouTube URL already processed: {job_id}")
            return job, message
            
        elif job_status == 'failed':
            message = f"URL memiliki job yang gagal (Job ID: {job_id}). Silakan hapus job lama terlebih dahulu sebelum memproses ulang."
            logger.info(f"YouTube URL has failed job: {job_id}")
            return job, message
        
        return job, f"URL memiliki job dengan status: {job_status}"
        
    except Exception as e:
        logger.error(f"Error checking existing YouTube job: {e}")
        return None, ""


async def handle_create_youtube_job(youtube_url: str) -> dict:
    """
    Create and queue a YouTube job.
    
    Args:
        youtube_url: YouTube URL to process
        
    Returns:
        Job creation result with job_id
        
    Raises:
        JobException: If URL already has an active job
    """
    try:
        # Check if URL already has an active job
        existing_job, status_message = check_existing_youtube_job(youtube_url)
        
        if existing_job:
            # URL sudah pernah diproses atau sedang diproses
            logger.warning(f"Cannot create job for URL - existing job found: {status_message}")
            raise JobException(
                f"URL tidak dapat diproses sekarang. {status_message}"
            )
        
        # Create new job
        job_id = str(uuid.uuid4())
        db.create_job(job_id, source_type="youtube", source_url=youtube_url)
        submit_job(job_id)
        log_action(None, "create_job", f"YouTube job created: {job_id} (URL: {youtube_url})")
        
        logger.info(f"✓ New YouTube job created: {job_id}")
        return {"job_id": job_id, "status": "queued"}
        
    except JobException:
        raise
    except Exception as e:
        logger.error(f"YouTube job creation error: {e}", exc_info=True)
        raise JobException(f"Gagal membuat job: {str(e)}")


async def handle_create_upload_job(file_content: bytes, filename: str) -> dict:
    """
    Create and queue an upload job.
    
    Args:
        file_content: File content bytes
        filename: Original filename
        
    Returns:
        Job creation result with job_id
    """
    try:
        job_id = str(uuid.uuid4())
        file_ext = Path(filename).suffix if filename else ".mp4"
        raw_path = config.RAW_DIR / f"{job_id}_upload{file_ext}"

        # Save locally
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        with open(raw_path, "wb") as f:
            f.write(file_content)

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

        submit_job(job_id)
        log_action(None, "create_job", f"Upload job created: {job_id}")

        return {"job_id": job_id, "status": "queued"}

    except Exception as e:
        logger.error(f"Upload job creation error: {e}", exc_info=True)
        raise JobException(f"Failed to create upload job: {str(e)}")


async def handle_automate(payload: AutomateRequest) -> dict:
    """
    Execute full automation: create job, clips, render, and webhook in one call.
    
    Args:
        payload: Automation request payload
        
    Returns:
        Automation result with created IDs
    """
    try:
        job_id = str(uuid.uuid4())

        # 1. Create job
        if payload.source_type == "youtube":
            if not payload.youtube_url:
                raise JobException("youtube_url required for YouTube source")
            db.create_job(job_id, source_type="youtube", source_url=payload.youtube_url)
            submit_job(job_id)

        elif payload.source_type == "upload":
            if not payload.file_url:
                raise JobException("file_url required for upload source")

            file_ext = Path(payload.file_url).suffix or ".mp4"
            raw_path = config.RAW_DIR / f"{job_id}_upload{file_ext}"

            r = requests.get(payload.file_url, stream=True)
            r.raise_for_status()

            with open(raw_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            job = db.create_job(job_id, source_type="upload")
            db.update_job(job_id, raw_path=str(raw_path))
            submit_job(job_id)
        else:
            raise JobException("Invalid source_type")

        # 2. Register webhook
        if payload.webhook_url:
            db.update_job(job_id, webhook_url=payload.webhook_url)

        # 3. Wait for job ready (polling, max 60s)
        import time
        for _ in range(60):
            job = db.get_job(job_id)
            if job and job.get("status") == "ready":
                break
            time.sleep(1)
        else:
            raise JobException("Job not ready after 60s")

        # 4. Create clips
        created_clips = []
        if payload.clips:
            for clip in payload.clips:
                clip_id = str(uuid.uuid4())
                db.create_clip(
                    clip_id=clip_id,
                    job_id=job_id,
                    start_sec=clip["start_sec"],
                    end_sec=clip["end_sec"],
                    score=clip.get("score", 0),
                    title=clip.get("title", ""),
                    transcript_snippet=clip.get("transcript_snippet", ""),
                    thumbnail_path="",
                )
                created_clips.append(clip_id)

        # 5. Render clips
        render_ids = []
        if payload.render_options and created_clips:
            for clip_id in created_clips:
                render_id = str(uuid.uuid4())
                db.create_render(render_id=render_id, clip_id=clip_id, options=payload.render_options)
                submit_render(render_id)
                render_ids.append(render_id)

        return {
            "job_id": job_id,
            "created_clips": created_clips,
            "render_ids": render_ids,
            "status": "queued",
        }

    except JobException:
        raise
    except Exception as e:
        logger.error(f"Automate error: {e}", exc_info=True)
        raise JobException(f"Automation failed: {str(e)}")


def handle_delete_job(job_id: str) -> dict:
    """
    Delete job and all associated data.
    
    Args:
        job_id: Job ID to delete
        
    Returns:
        Deletion result with file count and space freed
    """
    try:
        job = db.get_job(job_id)
        if not job:
            raise JobException("Job not found")

        job_status = job.get("status", "")
        if job_status not in ["ready", "failed", "cancelled"]:
            raise JobException(
                f"Cannot delete job with status '{job_status}'. Only completed/failed/cancelled jobs can be deleted."
            )

        logger.info(f"=== Starting deletion for job {job_id} ===")

        # Collect files and records
        clips = db.get_clips_by_job(job_id)
        renders = db.get_renders_by_job(job_id)

        logger.info(f"Found {len(clips)} clips and {len(renders)} renders to delete")

        files_to_delete = collect_job_files_for_deletion(job, clips, renders, config)
        logger.info(f"Total files to delete: {len(files_to_delete)}")

        # Delete files
        deleted_files, failed_files, total_size_freed = safe_delete_files(files_to_delete)

        # Delete database records
        db.delete_job(job_id)

        logger.info(f"✓ Job {job_id} deleted successfully")
        logger.info(f"  - Files deleted: {len(deleted_files)}")
        logger.info(f"  - Failed deletions: {len(failed_files)}")
        logger.info(f"  - Disk space freed: {total_size_freed:.2f} MB")

        return {
            "message": "Job deleted successfully",
            "job_id": job_id,
            "files_deleted": len(deleted_files),
            "files_failed": len(failed_files),
            "failed_files": failed_files if failed_files else None,
            "space_freed_mb": round(total_size_freed, 2),
        }

    except JobException:
        raise
    except Exception as e:
        logger.error(f"Delete job error: {e}", exc_info=True)
        raise JobException(f"Job deletion failed: {str(e)}")


def handle_cancel_job(job_id: str) -> dict:
    """
    Cancel a job that is queued or processing.
    """
    try:
        job = db.get_job(job_id)
        if not job:
            raise JobException("Job not found")

        job_status = job.get("status", "")
        if job_status not in ["queued", "processing"]:
            raise JobException(
                f"Cannot cancel job with status '{job_status}'."
            )

        db.update_job(job_id, status="cancelled", step="cancelled", error="Cancelled by user")
        logger.info(f"Job cancelled: {job_id}")

        return {"job_id": job_id, "status": "cancelled", "message": "Job cancelled"}

    except JobException:
        raise
    except Exception as e:
        logger.error(f"Cancel job error: {e}", exc_info=True)
        raise JobException(f"Job cancellation failed: {str(e)}")


def handle_retry_job(job_id: str) -> dict:
    """
    Retry a failed job from the last step.
    
    Args:
        job_id: Job ID to retry
        
    Returns:
        Retry result
    """
    try:
        job = db.get_job(job_id)
        if not job:
            raise JobException("Job tidak ditemukan")

        if job["status"] not in ["failed", "ready"]:
            raise JobException(
                f"Hanya job yang gagal atau selesai yang bisa di-retry. Status saat ini: {job['status']}"
            )

        db.update_job(job_id, status="queued", error=None, progress=0)
        submit_job(job_id)

        return {"job_id": job_id, "status": "queued", "message": "Job dikerjakan ulang"}

    except JobException:
        raise
    except Exception as e:
        logger.error(f"Retry job error: {e}", exc_info=True)
        raise JobException(f"Gagal retry job: {str(e)}")


def handle_cleanup_and_create_youtube_job(youtube_url: str) -> dict:
    """
    Clean up existing job for YouTube URL and create a new one.
    This forcefully removes the old job and creates a fresh one.
    
    Args:
        youtube_url: YouTube URL to process
        
    Returns:
        New job creation result
    """
    try:
        # Find and delete existing job
        existing_job, status_message = check_existing_youtube_job(youtube_url)
        
        if existing_job:
            old_job_id = existing_job['id']
            old_status = existing_job.get('status')
            
            logger.info(f"Cleaning up existing YouTube job: {old_job_id} (Status: {old_status})")
            
            # Delete existing job and its data
            clips = db.get_clips_by_job(old_job_id)
            renders = db.get_renders_by_job(old_job_id)
            
            files_to_delete = collect_job_files_for_deletion(existing_job, clips, renders, config)
            deleted_files, failed_files, total_size = safe_delete_files(files_to_delete)
            
            # Delete from database
            db.delete_job(old_job_id)
            
            logger.info(f"✓ Deleted old job: {old_job_id}")
            logger.info(f"  - Files deleted: {len(deleted_files)}")
            logger.info(f"  - Space freed: {total_size:.2f} MB")
        
        # Create new job
        job_id = str(uuid.uuid4())
        db.create_job(job_id, source_type="youtube", source_url=youtube_url)
        submit_job(job_id)
        log_action(
            None, 
            "create_job_with_cleanup", 
            f"YouTube job created (after cleanup): {job_id} (URL: {youtube_url})"
        )
        
        logger.info(f"✓ New YouTube job created: {job_id}")
        return {
            "job_id": job_id, 
            "status": "queued",
            "previous_job_cleaned": existing_job is not None
        }
        
    except Exception as e:
        logger.error(f"Cleanup and create job error: {e}", exc_info=True)
        raise JobException(f"Gagal membersihkan dan membuat job baru: {str(e)}")
