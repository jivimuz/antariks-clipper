"""Smart cropping based on face count and speaking detection"""
import logging
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class SmartCropper:
    """Smart cropping based on face count and speaking detection"""
    
    def __init__(self, video_width: int, video_height: int, 
                 output_width: int = 1080, output_height: int = 1920):
        """
        Initialize smart cropper
        
        Args:
            video_width: Width of input video
            video_height: Height of input video
            output_width: Width of output (default 1080 for 9:16)
            output_height: Height of output (default 1920 for 9:16)
        """
        self.video_width = video_width
        self.video_height = video_height
        self.output_width = output_width
        self.output_height = output_height
        
        # Calculate crop dimensions for 9:16 aspect ratio
        target_aspect = output_width / output_height
        desired_crop_width = int(video_height * target_aspect)
        
        # Ensure crop width doesn't exceed video width
        self.crop_width = min(desired_crop_width, video_width)
        self.crop_height = video_height
        
        # Smooth tracking with EMA (Exponential Moving Average)
        self.center_x = video_width // 2
        self.center_y = video_height // 2
        self.ema_alpha = 0.2  # Smoothing factor
        
        # For duo split mode - track each person's crop separately
        self.split_center_a = (video_width // 2, video_height // 2)
        self.split_center_b = (video_width // 2, video_height // 2)
    
    def crop_solo(self, frame: np.ndarray, face_bbox: List[int]) -> np.ndarray:
        """
        Crop for single person - follow the face with smooth tracking
        
        Args:
            frame: Input video frame
            face_bbox: [x, y, width, height] of face
        
        Returns:
            Cropped and resized frame
        """
        x, y, w, h = face_bbox
        
        # Calculate target center (face center)
        target_x = x + w // 2
        target_y = y + h // 2
        
        # Apply EMA smoothing
        self.center_x = int(self.ema_alpha * target_x + (1 - self.ema_alpha) * self.center_x)
        self.center_y = int(self.ema_alpha * target_y + (1 - self.ema_alpha) * self.center_y)
        
        # Get crop box
        crop_x, crop_y, crop_w, crop_h = self._get_constrained_crop_box(
            self.center_x, self.center_y
        )
        
        # Crop and resize
        cropped = frame[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        resized = cv2.resize(cropped, (self.output_width, self.output_height))
        
        return resized
    
    def crop_duo_switch(self, frame: np.ndarray, speaker_face_bbox: List[int]) -> np.ndarray:
        """
        Crop for duo - instant switch to speaker (NO slide transition)
        This is similar to solo mode but may switch between faces instantly
        
        Args:
            frame: Input video frame
            speaker_face_bbox: [x, y, width, height] of speaking face
        
        Returns:
            Cropped and resized frame focused on speaker
        """
        # Use solo crop logic but with slightly faster EMA for more responsive switching
        x, y, w, h = speaker_face_bbox
        
        # Calculate target center (speaker face center)
        target_x = x + w // 2
        target_y = y + h // 2
        
        # Use faster EMA for more instant switching (higher alpha)
        alpha = 0.4  # More responsive than solo mode
        self.center_x = int(alpha * target_x + (1 - alpha) * self.center_x)
        self.center_y = int(alpha * target_y + (1 - alpha) * self.center_y)
        
        # Get crop box
        crop_x, crop_y, crop_w, crop_h = self._get_constrained_crop_box(
            self.center_x, self.center_y
        )
        
        # Crop and resize
        cropped = frame[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        resized = cv2.resize(cropped, (self.output_width, self.output_height))
        
        return resized
    
    def crop_duo_split(self, frame: np.ndarray, 
                       face_a_bbox: List[int], face_b_bbox: List[int]) -> np.ndarray:
        """
        Crop for duo speaking together - split screen vertical
        Top half: Person A cropped to face
        Bottom half: Person B cropped to face
        
        Args:
            frame: Input video frame
            face_a_bbox: [x, y, width, height] of first face
            face_b_bbox: [x, y, width, height] of second face
        
        Returns:
            Split screen frame with both people
        """
        # Each split is half height
        split_output_height = self.output_height // 2
        
        # Process face A (top half)
        x_a, y_a, w_a, h_a = face_a_bbox
        target_x_a = x_a + w_a // 2
        target_y_a = y_a + h_a // 2
        
        # Apply EMA smoothing for face A
        prev_x_a, prev_y_a = self.split_center_a
        center_x_a = int(self.ema_alpha * target_x_a + (1 - self.ema_alpha) * prev_x_a)
        center_y_a = int(self.ema_alpha * target_y_a + (1 - self.ema_alpha) * prev_y_a)
        self.split_center_a = (center_x_a, center_y_a)
        
        # Process face B (bottom half)
        x_b, y_b, w_b, h_b = face_b_bbox
        target_x_b = x_b + w_b // 2
        target_y_b = y_b + h_b // 2
        
        # Apply EMA smoothing for face B
        prev_x_b, prev_y_b = self.split_center_b
        center_x_b = int(self.ema_alpha * target_x_b + (1 - self.ema_alpha) * prev_x_b)
        center_y_b = int(self.ema_alpha * target_y_b + (1 - self.ema_alpha) * prev_y_b)
        self.split_center_b = (center_x_b, center_y_b)
        
        # Crop face A
        crop_a = self._crop_face_for_split(frame, center_x_a, center_y_a)
        crop_a_resized = cv2.resize(crop_a, (self.output_width, split_output_height))
        
        # Crop face B
        crop_b = self._crop_face_for_split(frame, center_x_b, center_y_b)
        crop_b_resized = cv2.resize(crop_b, (self.output_width, split_output_height))
        
        # Stack vertically
        result = np.vstack([crop_a_resized, crop_b_resized])
        
        return result
    
    def _crop_face_for_split(self, frame: np.ndarray, center_x: int, center_y: int) -> np.ndarray:
        """
        Crop a region around a face for split screen mode
        
        Args:
            frame: Input frame
            center_x: X coordinate of face center
            center_y: Y coordinate of face center
        
        Returns:
            Cropped region
        """
        crop_x, crop_y, crop_w, crop_h = self._get_constrained_crop_box(center_x, center_y)
        return frame[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
    
    def _get_constrained_crop_box(self, center_x: int, center_y: int) -> Tuple[int, int, int, int]:
        """
        Get crop box constrained to frame boundaries
        
        Args:
            center_x: Desired center X coordinate
            center_y: Desired center Y coordinate
        
        Returns:
            (x, y, width, height) of crop box
        """
        half_crop_w = self.crop_width // 2
        half_crop_h = self.crop_height // 2
        
        # Constrain center to valid crop region
        center_x = max(half_crop_w, min(self.video_width - half_crop_w, center_x))
        center_y = max(half_crop_h, min(self.video_height - half_crop_h, center_y))
        
        # Calculate crop box
        crop_x = center_x - half_crop_w
        crop_y = center_y - half_crop_h
        
        return crop_x, crop_y, self.crop_width, self.crop_height
    
    def process_frame(self, frame: np.ndarray, faces: List[Dict], 
                      speakers: List[int], mode: str) -> np.ndarray:
        """
        Process single frame with appropriate cropping mode
        
        Args:
            frame: Input video frame
            faces: List of face tracks with 'id' and 'bbox'
            speakers: List of speaking face IDs
            mode: "solo", "duo_switch", or "duo_split"
        
        Returns:
            Processed frame
        """
        if not faces:
            # No faces - return center crop
            crop_x, crop_y, crop_w, crop_h = self._get_constrained_crop_box(
                self.video_width // 2, self.video_height // 2
            )
            cropped = frame[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
            return cv2.resize(cropped, (self.output_width, self.output_height))
        
        if mode == "solo":
            # Use first face
            return self.crop_solo(frame, faces[0]['bbox'])
        
        elif mode == "duo_switch":
            # Find speaker face or use first face
            speaker_face = self._get_speaker_face(faces, speakers)
            if speaker_face:
                return self.crop_duo_switch(frame, speaker_face['bbox'])
            else:
                return self.crop_solo(frame, faces[0]['bbox'])
        
        elif mode == "duo_split":
            # Need at least 2 faces for split mode
            if len(faces) >= 2:
                return self.crop_duo_split(frame, faces[0]['bbox'], faces[1]['bbox'])
            else:
                # Fall back to solo
                return self.crop_solo(frame, faces[0]['bbox'])
        
        else:
            logger.warning(f"Unknown mode: {mode}, defaulting to solo")
            return self.crop_solo(frame, faces[0]['bbox'])
    
    def _get_speaker_face(self, faces: List[Dict], speakers: List[int]) -> Optional[Dict]:
        """
        Get the face of the primary speaker
        
        Args:
            faces: List of face tracks
            speakers: List of speaking face IDs
        
        Returns:
            Face dict of speaker, or None
        """
        if not speakers:
            # No speakers, use first/largest face
            return faces[0] if faces else None
        
        # Find face matching primary speaker
        for face in faces:
            if face.get('id') in speakers:
                return face
        
        # Fallback to first face
        return faces[0] if faces else None
