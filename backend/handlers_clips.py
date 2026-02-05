"""Clip-related route handlers"""
import logging
import uuid
from pathlib import Path

import db
import config
from schemas import MultiClipCreate
from services.caption_generator import generate_caption, generate_hashtags
from services.thumbnails import generate_thumbnail
from services.transcribe import load_transcript
from services.highlight import generate_highlights
from utils import log_action, safe_delete_files
from exceptions import ClipException

logger = logging.getLogger(__name__)


def handle_create_clips(job_id: str, payload: MultiClipCreate) -> dict:
    """
    Create multiple clips for a job with auto-generated captions.
    
    Args:
        job_id: Job ID
        payload: Clip creation payload
        
    Returns:
        Created clips list
    """
    try:
        job = db.get_job(job_id)
        if not job:
            raise ClipException("Job not found")

        created = []
        for clip in payload.clips:
            clip_id = str(uuid.uuid4())

            caption = generate_caption(
                title=clip.title,
                transcript_snippet=clip.transcript_snippet,
                metadata={},
            )
            hashtags = generate_hashtags(
                title=clip.title,
                transcript_snippet=clip.transcript_snippet,
                metadata={},
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
                hashtags_text=hashtags,
            )
            created.append(new_clip)

        return {"created": created, "count": len(created)}

    except ClipException:
        raise
    except Exception as e:
        logger.error(f"Create multi-clip error: {e}", exc_info=True)
        raise ClipException(f"Failed to create clips: {str(e)}")


def handle_delete_clip(clip_id: str) -> dict:
    """
    Delete a clip and all associated renders.
    
    Args:
        clip_id: Clip ID to delete
        
    Returns:
        Deletion result
    """
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise ClipException("Clip not found")

        logger.info(f"Deleting clip {clip_id}")

        # Get renders
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM renders WHERE clip_id = ?", (clip_id,))
        renders = [dict(row) for row in cursor.fetchall()]

        # Delete render files
        for render in renders:
            if render.get("output_path"):
                try:
                    Path(render["output_path"]).unlink(missing_ok=True)
                    logger.info(f"  Deleted render file: {render['output_path']}")
                except Exception as e:
                    logger.warning(f"  Failed to delete render file: {e}")

            cursor.execute("DELETE FROM renders WHERE id = ?", (render["id"],))

        # Delete thumbnail
        if clip.get("thumbnail_path"):
            try:
                Path(clip["thumbnail_path"]).unlink(missing_ok=True)
                logger.info(f"  Deleted thumbnail: {clip['thumbnail_path']}")
            except Exception as e:
                logger.warning(f"  Failed to delete thumbnail: {e}")

        # Delete clip
        db.delete_clip(clip_id)
        conn.commit()
        conn.close()

        logger.info(f"  Deleted clip {clip_id} and {len(renders)} associated renders")

        return {"success": True, "clip_id": clip_id, "deleted_renders": len(renders)}

    except ClipException:
        raise
    except Exception as e:
        logger.error(f"Delete clip error: {e}", exc_info=True)
        raise ClipException(f"Failed to delete clip: {str(e)}")


def handle_regenerate_highlights(job_id: str, clip_count: int = None, adaptive: bool = True) -> dict:
    """
    Regenerate highlight clips for a job.
    
    Args:
        job_id: Job ID
        clip_count: Number of clips to generate (None = auto)
        adaptive: Use adaptive generation
        
    Returns:
        Regeneration result with clip counts
    """
    try:
        job = db.get_job(job_id)
        if not job:
            raise ClipException("Job not found")

        if job["status"] != "ready":
            raise ClipException(
                f"Job must be in 'ready' status. Current: {job['status']}"
            )

        # Load transcript
        transcript_path = Path(config.TRANSCRIPTS_DIR) / f"{job_id}.json"
        if not transcript_path.exists():
            raise ClipException("Transcript not found")

        transcript = load_transcript(transcript_path)
        if not transcript or not transcript.get("segments"):
            raise ClipException("Invalid transcript data")

        logger.info(f"Regenerating highlights for job {job_id}")
        logger.info(f"  Clip count: {clip_count or 'auto'}")
        logger.info(f"  Adaptive: {adaptive}")

        # Delete existing clips
        existing_clips = db.get_clips_by_job(job_id)
        files_to_delete = []

        for clip in existing_clips:
            if clip.get("thumbnail_path"):
                files_to_delete.append(clip["thumbnail_path"])
            db.delete_clip(clip["id"])

        if files_to_delete:
            safe_delete_files(files_to_delete)

        logger.info(f"Deleted {len(existing_clips)} existing clips")

        # Generate new highlights
        highlights = generate_highlights(transcript, top_n=clip_count, adaptive=adaptive)
        if not highlights:
            raise ClipException("Failed to generate highlights")

        # Get video path
        raw_path = Path(job["raw_path"]) if job.get("raw_path") else None
        if not raw_path or not raw_path.exists():
            raise ClipException("Video file not found")

        # Create new clips
        created_clips = []
        for i, hl in enumerate(highlights):
            clip_id = str(uuid.uuid4())
            logger.info(f"Creating clip {i + 1}/{len(highlights)}: {hl['title']}")

            mid_time = (hl["start"] + hl["end"]) / 2
            thumbnail_path = Path(config.THUMBNAILS_DIR) / f"{clip_id}.jpg"

            generate_thumbnail(raw_path, mid_time, thumbnail_path)

            caption = generate_caption(
                title=hl["title"],
                transcript_snippet=hl["snippet"],
                metadata=hl.get("metadata", {}),
            )
            hashtags = generate_hashtags(
                title=hl["title"],
                transcript_snippet=hl["snippet"],
                metadata=hl.get("metadata", {}),
            )

            clip = db.create_clip(
                clip_id=clip_id,
                job_id=job_id,
                start_sec=hl["start"],
                end_sec=hl["end"],
                score=hl["score"],
                title=hl["title"],
                transcript_snippet=hl["snippet"],
                thumbnail_path=str(thumbnail_path) if thumbnail_path.exists() else "",
                metadata=hl.get("metadata", {}),
                caption_text=caption,
                hashtags_text=hashtags,
            )
            created_clips.append(clip)

        logger.info(f"Created {len(created_clips)} new clips")

        return {
            "success": True,
            "deleted": len(existing_clips),
            "created": len(created_clips),
            "clips": created_clips,
        }

    except ClipException:
        raise
    except Exception as e:
        logger.error(f"Regenerate highlights error: {e}", exc_info=True)
        raise ClipException(f"Failed to regenerate highlights: {str(e)}")
