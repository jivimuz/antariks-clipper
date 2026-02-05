"""Render-related route handlers"""
import logging
import uuid
from pathlib import Path

import db
from schemas import RenderCreate
from services.jobs import submit_render
from exceptions import RenderException
from config import MAX_CONCURRENT_RENDERS

logger = logging.getLogger(__name__)


def _cleanup_old_renders(clip_id: str) -> None:
    """Delete output files from old renders of the same clip"""
    try:
        existing = db.get_renders_by_clip(clip_id)
        for render in existing:
            if render.get('output_path'):
                try:
                    file_path = Path(render['output_path'])
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Deleted old render file: {render['output_path']}")
                except Exception as e:
                    logger.warning(f"Failed to delete render file {render['output_path']}: {e}")
    except Exception as e:
        logger.warning(f"Error during cleanup: {e}")


def handle_create_render(clip_id: str, options: RenderCreate) -> dict:
    """
    Create a render job for a clip.
    
    Args:
        clip_id: Clip ID to render
        options: Render options
        
    Returns:
        Render creation result
    """
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise RenderException("Clip not found")

        # Check concurrent render limit
        all_renders = db.list_renders()
        active_renders = [r for r in all_renders if r.get("status") in {"queued", "processing"}]
        
        if len(active_renders) >= MAX_CONCURRENT_RENDERS:
            raise RenderException(
                f"Render limit tercapai. Maksimal {MAX_CONCURRENT_RENDERS} render bisa berjalan bersamaan. "
                f"Saat ini ada {len(active_renders)} render aktif. Mohon tunggu sampai ada yang selesai."
            )

        existing = db.get_renders_by_clip(clip_id)
        blocked_status = {"queued", "processing"}
        if any(r.get("status") in blocked_status for r in existing):
            raise RenderException("Render sudah ada untuk clip ini. Mohon tunggu sampai selesai atau hapus render lama.")
        # Clean up old render files before creating new one
        _cleanup_old_renders(clip_id)
        render_id = str(uuid.uuid4())
        db.create_render(render_id=render_id, clip_id=clip_id, options=options.dict())
        submit_render(render_id)

        return {"render_id": render_id, "status": "queued"}

    except RenderException:
        raise
    except Exception as e:
        logger.error(f"Create render error: {e}", exc_info=True)
        raise RenderException(f"Failed to create render: {str(e)}")


def handle_retry_render(render_id: str) -> dict:
    """
    Retry a failed render.
    
    Args:
        render_id: Render ID to retry
        
    Returns:
        Retry result
    """
    try:
        render = db.get_render(render_id)
        if not render:
            raise RenderException("Render not found")

        if render["status"] not in ["failed"]:
            raise RenderException(
                f"Can only retry failed renders. Current status: {render['status']}"
            )

        db.update_render(render_id, status="queued", error=None, progress=0)
        submit_render(render_id)

        return {
            "render_id": render_id,
            "status": "queued",
            "message": "Render requeued for processing",
        }

    except RenderException:
        raise
    except Exception as e:
        logger.error(f"Retry render error: {e}", exc_info=True)
        raise RenderException(f"Failed to retry render: {str(e)}")


def handle_batch_render(job_id: str, clip_ids: str, options: RenderCreate) -> dict:
    """
    Create render jobs for multiple selected clips.
    
    Args:
        job_id: Job ID
        clip_ids: Comma-separated clip IDs
        options: Render options
        
    Returns:
        Batch render result
    """
    try:
        job = db.get_job(job_id)
        if not job:
            raise RenderException("Job not found")

        clip_id_list = [cid.strip() for cid in clip_ids.split(",") if cid.strip()]
        render_ids = []
        skipped = []
        blocked_status = {"queued", "processing"}

        for clip_id in clip_id_list:
            clip = db.get_clip(clip_id)
            if not clip or clip["job_id"] != job_id:
                continue

            # Check concurrent render limit before creating new render
            all_renders = db.list_renders()
            active_renders = [r for r in all_renders if r.get("status") in blocked_status]
            
            if len(active_renders) >= MAX_CONCURRENT_RENDERS:
                skipped.append({
                    "clip_id": clip_id, 
                    "reason": f"concurrent_limit_reached ({len(active_renders)}/{MAX_CONCURRENT_RENDERS})"
                })
                continue

            existing = db.get_renders_by_clip(clip_id)
            if any(r.get("status") in blocked_status for r in existing):
                skipped.append({"clip_id": clip_id, "reason": "already_rendered_or_processing"})
                continue

            # Clean up old render files before creating new one
            _cleanup_old_renders(clip_id)

            render_id = str(uuid.uuid4())
            db.create_render(render_id=render_id, clip_id=clip_id, options=options.dict())
            submit_render(render_id)
            render_ids.append(render_id)

        return {
            "job_id": job_id,
            "render_ids": render_ids,
            "count": len(render_ids),
            "skipped": skipped,
            "status": "queued",
        }

    except RenderException:
        raise
    except Exception as e:
        logger.error(f"Batch render error: {e}", exc_info=True)
        raise RenderException(f"Failed to create batch render: {str(e)}")
