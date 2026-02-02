"""Speaker detection based on mouth movement"""
import logging
import numpy as np
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class SpeakerDetector:
    """Detect who is speaking based on mouth movement variance"""
    
    def __init__(self, speaking_threshold: float = 5.0, history_window: int = 10):
        """
        Initialize speaker detector
        
        Args:
            speaking_threshold: Minimum variance to be considered "speaking"
            history_window: Number of frames to track for variance calculation
        """
        self.mouth_history = {}  # face_id -> list of mouth openness values
        self.speaking_threshold = speaking_threshold
        self.history_window = history_window
        self.simultaneous_speaking_count = 0
        self.simultaneous_threshold = 3  # Frames to confirm simultaneous speaking
    
    def update(self, frame, faces: List[Dict]) -> Dict:
        """
        Update speaker detection with new frame
        
        Args:
            frame: Current video frame
            faces: List of face tracks with 'id', 'bbox', and optionally 'mouth_openness'
        
        Returns:
            {
                "speakers": [face_id, ...],  # who is currently speaking
                "mode": "solo" | "duo_switch" | "duo_split"
            }
        """
        # Update mouth history for each face
        for face in faces:
            face_id = face.get('id')
            mouth_openness = face.get('mouth_openness')
            
            if face_id is not None and mouth_openness is not None:
                if face_id not in self.mouth_history:
                    self.mouth_history[face_id] = []
                
                self.mouth_history[face_id].append(mouth_openness)
                
                # Keep only recent history
                if len(self.mouth_history[face_id]) > self.history_window:
                    self.mouth_history[face_id].pop(0)
        
        # Determine who is speaking
        speakers = []
        for face in faces:
            face_id = face.get('id')
            if face_id is not None and self.is_speaking(face_id):
                speakers.append(face_id)
        
        # Determine mode
        mode = self.get_speaking_mode(faces, speakers)
        
        return {
            "speakers": speakers,
            "mode": mode
        }
    
    def is_speaking(self, face_id: int) -> bool:
        """
        Check if face is currently speaking based on mouth movement variance
        
        Args:
            face_id: ID of the face to check
        
        Returns:
            True if speaking, False otherwise
        """
        if face_id not in self.mouth_history:
            return False
        
        history = self.mouth_history[face_id]
        
        # Need at least 3 samples to calculate meaningful variance
        if len(history) < 3:
            return False
        
        variance = np.var(history)
        return variance > self.speaking_threshold
    
    def get_speaking_mode(self, faces: List[Dict], speakers: List[int]) -> str:
        """
        Determine cropping mode based on face count and speakers
        
        Rules:
        1. If 1 face → "solo"
        2. If 2 faces and 0-1 speaking → "duo_switch"
        3. If 2 faces and 2 speaking simultaneously → "duo_split"
        4. If 3+ faces → use largest 2 faces, apply duo logic
        
        Args:
            faces: List of detected faces
            speakers: List of face IDs that are speaking
        
        Returns:
            "solo", "duo_switch", or "duo_split"
        """
        num_faces = len(faces)
        num_speakers = len(speakers)
        
        if num_faces <= 1:
            return "solo"
        
        # For 2+ faces
        if num_speakers >= 2:
            # Both speaking - check if simultaneous or alternating
            self.simultaneous_speaking_count += 1
            
            # If both have been speaking for multiple frames, switch to split mode
            if self.simultaneous_speaking_count >= self.simultaneous_threshold:
                return "duo_split"
            else:
                return "duo_switch"
        else:
            # Reset simultaneous counter if not both speaking
            self.simultaneous_speaking_count = 0
            return "duo_switch"
    
    def get_primary_speaker(self, speakers: List[int]) -> Optional[int]:
        """
        Get the primary speaker from list of speakers
        If multiple speakers, return the one with highest mouth variance
        
        Args:
            speakers: List of speaking face IDs
        
        Returns:
            Face ID of primary speaker, or None
        """
        if not speakers:
            return None
        
        if len(speakers) == 1:
            return speakers[0]
        
        # Return speaker with highest variance
        best_speaker = None
        best_variance = -1
        
        for speaker_id in speakers:
            if speaker_id in self.mouth_history and len(self.mouth_history[speaker_id]) > 0:
                variance = np.var(self.mouth_history[speaker_id])
                if variance > best_variance:
                    best_variance = variance
                    best_speaker = speaker_id
        
        # Fallback to first speaker if no valid variance found
        return best_speaker if best_speaker is not None else speakers[0]
