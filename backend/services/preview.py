"""Preview service for real-time clip preview with face tracking"""
import logging
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Generator
import tempfile
import subprocess
from services.face_track import detect_faces_sample
from config import PREVIEW_WIDTH, PREVIEW_HEIGHT, PREVIEW_SAMPLE_FRAMES

logger = logging.getLogger(__name__)

def get_face_crop_region(video_path: Path, start_sec: float, end_sec: float) -> Tuple[float, float]:
    """
    Sample frames to detect face region for cropping.
    Returns (center_x_ratio, center_y_ratio) relative to video dimensions.
    """
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return (0.5, 0.5)  # Default center
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        duration = end_sec - start_sec
        sample_interval = duration / PREVIEW_SAMPLE_FRAMES
        
        face_centers = []
        
        for i in range(PREVIEW_SAMPLE_FRAMES):
            timestamp = start_sec + (i * sample_interval)
            frame_num = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Detect face
            faces = detect_faces_sample(frame)
            if faces:
                # Use largest face
                largest = max(faces, key=lambda f: f['width'] * f['height'])
                cx = (largest['x'] + largest['width'] / 2) / width
                cy = (largest['y'] + largest['height'] / 2) / height
                face_centers.append((cx, cy))
        
        cap.release()
        
        if face_centers:
            # Average face center
            avg_cx = sum(c[0] for c in face_centers) / len(face_centers)
            avg_cy = sum(c[1] for c in face_centers) / len(face_centers)
            return (avg_cx, avg_cy)
        
        return (0.5, 0.5)  # Default center
        
    except Exception as e:
        logger.error(f"Face crop detection error: {e}")
        return (0.5, 0.5)

def generate_preview_stream(
    video_path: Path,
    start_sec: float,
    end_sec: float,
    face_tracking: bool = True
) -> Optional[Path]:
    """
    Generate low-res preview video with 9:16 crop.
    Returns path to temporary preview file.
    """
    try:
        duration = end_sec - start_sec
        
        # Get crop center
        if face_tracking:
            center_x, center_y = get_face_crop_region(video_path, start_sec, end_sec)
        else:
            center_x, center_y = 0.5, 0.5
        
        # Create temp file for preview
        preview_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        preview_path = Path(preview_file.name)
        preview_file.close()
        
        # Get video dimensions
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            str(video_path)
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        width, height = map(int, result.stdout.strip().split(','))
        
        # Calculate crop for 9:16 from source
        target_ratio = 9 / 16
        source_ratio = width / height
        
        if source_ratio > target_ratio:
            # Source is wider, crop width
            crop_h = height
            crop_w = int(height * target_ratio)
        else:
            # Source is taller, crop height
            crop_w = width
            crop_h = int(width / target_ratio)
        
        # Calculate crop position based on face center
        crop_x = int((width - crop_w) * center_x)
        crop_y = int((height - crop_h) * center_y)
        
        # Clamp to bounds
        crop_x = max(0, min(crop_x, width - crop_w))
        crop_y = max(0, min(crop_y, height - crop_h))
        
        # FFmpeg command for preview
        cmd = [
            'ffmpeg',
            '-ss', str(start_sec),
            '-i', str(video_path),
            '-t', str(duration),
            '-vf', f'crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={PREVIEW_WIDTH}:{PREVIEW_HEIGHT}',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '28',  # Lower quality for speed
            '-c:a', 'aac',
            '-b:a', '64k',
            '-y',
            str(preview_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            logger.error(f"Preview generation failed: {result.stderr}")
            return None
        
        return preview_path
        
    except Exception as e:
        logger.error(f"Preview stream error: {e}")
        return None

def get_preview_frame(
    video_path: Path,
    timestamp: float,
    face_tracking: bool = True,
    duration: float = 5.0
) -> Optional[bytes]:
    """
    Get single preview frame as JPEG bytes.
    Used for thumbnail preview with face tracking crop.
    """
    try:
        # Get crop region (sample around timestamp)
        start = max(0, timestamp - duration/2)
        end = timestamp + duration/2
        
        if face_tracking:
            center_x, center_y = get_face_crop_region(video_path, start, end)
        else:
            center_x, center_y = 0.5, 0.5
        
        # Get video dimensions
        cap = cv2.VideoCapture(str(video_path))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Seek to timestamp
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(timestamp * fps))
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None
        
        # Calculate 9:16 crop
        target_ratio = 9 / 16
        source_ratio = width / height
        
        if source_ratio > target_ratio:
            crop_h = height
            crop_w = int(height * target_ratio)
        else:
            crop_w = width
            crop_h = int(width / target_ratio)
        
        crop_x = int((width - crop_w) * center_x)
        crop_y = int((height - crop_h) * center_y)
        
        crop_x = max(0, min(crop_x, width - crop_w))
        crop_y = max(0, min(crop_y, height - crop_h))
        
        # Crop and resize
        cropped = frame[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        resized = cv2.resize(cropped, (PREVIEW_WIDTH, PREVIEW_HEIGHT))
        
        # Encode as JPEG
        _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buffer.tobytes()
        
    except Exception as e:
        logger.error(f"Preview frame error: {e}")
        return None
