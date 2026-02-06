"""Utility functions for common operations"""
import logging
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, List
import json

logger = logging.getLogger(__name__)


def get_subprocess_startup_info():
    """
    Get startup info to hide console window on Windows.
    Returns None on non-Windows platforms.
    """
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None


def get_subprocess_creation_flags():
    """
    Get creation flags to hide console window on Windows.
    Returns 0 on non-Windows platforms.
    """
    if sys.platform == 'win32':
        # CREATE_NO_WINDOW = 0x08000000
        return 0x08000000
    return 0


def log_action(user: Optional[str], action: str, message: str) -> None:
    """
    Log user action with consistent formatting.
    
    Args:
        user: Username or None for anonymous
        action: Action type/name
        message: Action details
    """
    user_info = f"user={user}" if user else "anonymous"
    logger.info(f"[ACTION] {user_info} | {action} | {message}")


def safe_delete_file(file_path: str, description: str = "") -> tuple[bool, Optional[float]]:
    """
    Safely delete a file and return success status.
    
    Args:
        file_path: Path to file to delete
        description: Optional description for logging
        
    Returns:
        Tuple of (success, file_size_mb)
    """
    try:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            os.remove(file_path)
            size_mb = file_size / 1024 / 1024
            desc_str = f" ({description})" if description else ""
            logger.info(f"✓ Deleted file{desc_str}: {file_path} ({size_mb:.2f} MB)")
            return True, size_mb
        else:
            logger.debug(f"File not found (already deleted?): {file_path}")
            return False, None
    except Exception as e:
        logger.error(f"❌ Failed to delete file {file_path}: {e}")
        return False, None


def safe_delete_files(file_paths: List[str]) -> tuple[List[str], List[str], float]:
    """
    Safely delete multiple files.
    
    Args:
        file_paths: List of file paths to delete
        
    Returns:
        Tuple of (deleted_files, failed_files, total_size_mb)
    """
    deleted_files = []
    failed_files = []
    total_size = 0.0

    for file_path in file_paths:
        success, size_mb = safe_delete_file(file_path)
        if success:
            deleted_files.append(file_path)
            if size_mb:
                total_size += size_mb
        else:
            failed_files.append(file_path)

    return deleted_files, failed_files, total_size


def collect_orphaned_files(job_id: str, directories: List[Path]) -> List[str]:
    """
    Find orphaned files related to a job in specified directories.
    
    Args:
        job_id: Job ID to search for
        directories: List of directories to search
        
    Returns:
        List of orphaned file paths
    """
    orphaned = []
    for directory in directories:
        if directory.exists():
            for file_path in directory.glob(f"{job_id}*"):
                orphaned.append(str(file_path))
                logger.info(f"Found orphaned file: {file_path}")
    return orphaned


def collect_job_files_for_deletion(
    job: dict, 
    clips: List[dict], 
    renders: List[dict],
    config
) -> List[str]:
    """
    Collect all files associated with a job for deletion.
    
    Args:
        job: Job record from database
        clips: List of clip records
        renders: List of render records
        config: Configuration module
        
    Returns:
        List of file paths to delete
    """
    files_to_delete = []

    # Job files
    if job.get('raw_path'):
        files_to_delete.append(job['raw_path'])
        # Check for partial/temp files
        raw_path = Path(job['raw_path'])
        for ext in ['.part', '.temp', '.tmp', '.ytdl']:
            temp_file = raw_path.parent / f"{raw_path.stem}{ext}"
            if temp_file.exists():
                files_to_delete.append(str(temp_file))

    if job.get('normalized_path'):
        files_to_delete.append(job['normalized_path'])

    # Transcript files
    transcript_path = Path(config.TRANSCRIPTS_DIR) / f"{job['id']}.json"
    if transcript_path.exists():
        files_to_delete.append(str(transcript_path))

    for ext in ['.txt', '.srt', '.vtt']:
        alt_transcript = Path(config.TRANSCRIPTS_DIR) / f"{job['id']}{ext}"
        if alt_transcript.exists():
            files_to_delete.append(str(alt_transcript))

    # Clip thumbnails
    for clip in clips:
        if clip.get('thumbnail_path'):
            files_to_delete.append(clip['thumbnail_path'])

    # Render files
    for render in renders:
        if render.get('output_path'):
            files_to_delete.append(render['output_path'])

    # Orphaned files
    directories = [
        config.RAW_DIR,
        config.NORMALIZED_DIR,
        config.TRANSCRIPTS_DIR,
        config.THUMBNAILS_DIR,
        config.RENDERS_DIR,
    ]
    orphaned = collect_orphaned_files(job['id'], directories)
    files_to_delete.extend(orphaned)

    return files_to_delete
