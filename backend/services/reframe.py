"""Reframe service for active speaker tracking and cropping"""
import logging
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from services.face_track import FaceTracker, match_tracks
from services.speaker_detect import SpeakerDetector
from services.smart_crop import SmartCropper
from config import FACE_DETECTION_INTERVAL, EMA_ALPHA

logger = logging.getLogger(__name__)

class ActiveSpeakerTracker:
    """Track active speaker and determine crop center"""
    
    def __init__(self, video_width: int, video_height: int, output_width: int, output_height: int):
        self.video_width = video_width
        self.video_height = video_height
        self.output_width = output_width
        self.output_height = output_height
        
        # Calculate crop dimensions for 9:16 aspect ratio
        target_aspect = output_width / output_height
        self.crop_width = int(video_height * target_aspect)
        self.crop_height = video_height
        
        # Center tracking with EMA
        self.center_x = video_width // 2
        self.center_y = video_height // 2
        
        self.tracker = FaceTracker()
        self.tracks = []
        self.mouth_history = {}  # track_id -> list of openness values
    
    def update(self, frame: np.ndarray, frame_idx: int) -> Tuple[int, int]:
        """
        Update tracker with new frame
        Returns (center_x, center_y) for crop
        """
        # Detect faces periodically
        if frame_idx % FACE_DETECTION_INTERVAL == 0:
            faces = self.tracker.detect_faces(frame)
            self.tracks = match_tracks(self.tracks, faces)
            
            # Update mouth history
            for track in self.tracks:
                track_id = track['id']
                mouth_open = self.tracker.get_mouth_openness(frame, track['bbox'])
                
                if mouth_open is not None:
                    if track_id not in self.mouth_history:
                        self.mouth_history[track_id] = []
                    self.mouth_history[track_id].append(mouth_open)
                    # Keep last 10 samples
                    self.mouth_history[track_id] = self.mouth_history[track_id][-10:]
        
        # Determine active speaker
        active_track = self._get_active_speaker()
        
        if active_track:
            # Get bbox center
            x, y, w, h = active_track['bbox']
            target_x = x + w // 2
            target_y = y + h // 2
            
            # Apply EMA smoothing
            self.center_x = int(EMA_ALPHA * target_x + (1 - EMA_ALPHA) * self.center_x)
            self.center_y = int(EMA_ALPHA * target_y + (1 - EMA_ALPHA) * self.center_y)
        
        # Constrain center to valid crop region
        half_crop_w = self.crop_width // 2
        half_crop_h = self.crop_height // 2
        
        self.center_x = max(half_crop_w, min(self.video_width - half_crop_w, self.center_x))
        self.center_y = max(half_crop_h, min(self.video_height - half_crop_h, self.center_y))
        
        return self.center_x, self.center_y
    
    def _get_active_speaker(self) -> Optional[Dict]:
        """Determine which track is the active speaker"""
        if not self.tracks:
            return None
        
        best_track = None
        best_score = -1
        
        for track in self.tracks:
            track_id = track['id']
            score = 0
            
            # Mouth movement variance (if available)
            if track_id in self.mouth_history and len(self.mouth_history[track_id]) > 2:
                variance = np.var(self.mouth_history[track_id])
                score += variance * 1000  # Scale up
            
            # Face size (larger = closer = more likely active)
            _, _, w, h = track['bbox']
            area = w * h
            score += area / 1000
            
            if score > best_score:
                best_score = score
                best_track = track
        
        return best_track
    
    def get_crop_box(self) -> Tuple[int, int, int, int]:
        """Get current crop box (x, y, width, height)"""
        x = self.center_x - self.crop_width // 2
        y = self.center_y - self.crop_height // 2
        return x, y, self.crop_width, self.crop_height
    
    def close(self):
        """Cleanup resources"""
        self.tracker.close()

def reframe_video_with_tracking(
    input_path: Path,
    output_path: Path,
    output_width: int,
    output_height: int,
    start_sec: float = 0,
    duration: float = None
) -> bool:
    """
    Reframe video with face tracking
    Returns True if successful
    """
    try:
        cap = cv2.VideoCapture(str(input_path))
        
        if not cap.isOpened():
            logger.error(f"Cannot open video: {input_path}")
            return False
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame range
        start_frame = int(start_sec * fps)
        if duration:
            end_frame = int((start_sec + duration) * fps)
        else:
            end_frame = total_frames
        
        # Initialize tracker
        tracker = ActiveSpeakerTracker(video_width, video_height, output_width, output_height)
        
        # Seek to start
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Output video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (output_width, output_height))
        
        frame_idx = 0
        current_frame = start_frame
        
        logger.info(f"Reframing video: {input_path} -> {output_path}")
        
        while current_frame < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Update tracker
            center_x, center_y = tracker.update(frame, frame_idx)
            
            # Get crop box
            x, y, w, h = tracker.get_crop_box()
            
            # Crop frame
            cropped = frame[y:y+h, x:x+w]
            
            # Resize to output dimensions
            resized = cv2.resize(cropped, (output_width, output_height))
            
            # Write frame
            out.write(resized)
            
            frame_idx += 1
            current_frame += 1
            
            if frame_idx % 100 == 0:
                logger.info(f"Processed {frame_idx} frames")
        
        cap.release()
        out.release()
        tracker.close()
        
        logger.info(f"Reframing complete: {output_path}")
        return output_path.exists()
        
    except Exception as e:
        logger.error(f"Reframe error: {e}")
        return False


def reframe_video_smart(
    input_path: Path,
    output_path: Path,
    output_width: int = 1080,
    output_height: int = 1920,
    start_sec: float = 0,
    duration: float = None
) -> bool:
    """
    Smart reframe video with automatic mode detection:
    1. Analyze video to detect faces
    2. Determine mode (solo/duo_switch/duo_split) per segment
    3. Apply appropriate cropping
    
    Args:
        input_path: Path to input video
        output_path: Path to output video
        output_width: Output width (default 1080)
        output_height: Output height (default 1920)
        start_sec: Start time in seconds
        duration: Duration in seconds (None for full video)
    
    Returns:
        True if successful
    """
    try:
        cap = cv2.VideoCapture(str(input_path))
        
        if not cap.isOpened():
            logger.error(f"Cannot open video: {input_path}")
            return False
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame range
        start_frame = int(start_sec * fps)
        if duration:
            end_frame = int((start_sec + duration) * fps)
        else:
            end_frame = total_frames
        
        # Initialize components
        face_tracker = FaceTracker()
        speaker_detector = SpeakerDetector()
        cropper = SmartCropper(video_width, video_height, output_width, output_height)
        
        # Seek to start
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Output video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (output_width, output_height))
        
        frame_idx = 0
        current_frame = start_frame
        tracks = []
        
        logger.info(f"Smart reframing video: {input_path} -> {output_path}")
        
        while current_frame < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect faces periodically
            if frame_idx % FACE_DETECTION_INTERVAL == 0:
                faces = face_tracker.detect_faces(frame)
                tracks = match_tracks(tracks, faces)
                
                # Get mouth openness for all tracked faces
                mouth_data = face_tracker.get_all_mouth_openness(frame, tracks)
                
                # Update tracks with mouth openness
                for track in tracks:
                    track['mouth_openness'] = mouth_data.get(track['id'])
            
            # Detect speakers
            speaker_info = speaker_detector.update(frame, tracks)
            
            # Apply smart cropping
            cropped = cropper.process_frame(
                frame,
                tracks,
                speaker_info["speakers"],
                speaker_info["mode"]
            )
            
            # Write frame
            out.write(cropped)
            
            frame_idx += 1
            current_frame += 1
            
            if frame_idx % 100 == 0:
                logger.info(f"Processed {frame_idx} frames (mode: {speaker_info['mode']})")
        
        cap.release()
        out.release()
        face_tracker.close()
        
        logger.info(f"Smart reframing complete: {output_path}")
        return output_path.exists()
        
    except Exception as e:
        logger.error(f"Smart reframe error: {e}")
        return False

