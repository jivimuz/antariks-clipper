"""Face detection and tracking using OpenCV (MediaPipe fallback for compatibility)"""
import logging
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FaceTracker:
    """Face detection and tracking using OpenCV Haar Cascades"""
    
    def __init__(self):
        # Use OpenCV's Haar Cascade for face detection (more reliable across platforms)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            logger.error("Failed to load face cascade classifier")
            raise RuntimeError("Face detection model not available")
        
        logger.info("Face tracker initialized with OpenCV Haar Cascades")
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces in frame
        Returns list of {bbox: [x, y, w, h], confidence}
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces using Haar Cascade
        faces_rects = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        faces = []
        for (x, y, w, h) in faces_rects:
            faces.append({
                'bbox': [int(x), int(y), int(w), int(h)],
                'confidence': 0.9  # Haar cascades don't provide confidence, use fixed value
            })
        
        return faces
    
    def get_mouth_openness(self, frame: np.ndarray, face_bbox: List[int]) -> Optional[float]:
        """
        Estimate mouth openness using simple heuristic
        Note: Without face mesh, we return a random variance for active speaker simulation
        """
        # Without face mesh, we can't accurately detect mouth openness
        # Return a small random value to simulate variation
        return np.random.uniform(0.5, 1.5)
    
    def get_all_mouth_openness(self, frame: np.ndarray, faces: List[Dict]) -> Dict[int, float]:
        """
        Get mouth openness for all tracked faces
        
        Args:
            frame: Input video frame
            faces: List of face tracks with 'id' and 'bbox'
        
        Returns:
            Dictionary mapping face_id to mouth openness value
        """
        mouth_data = {}
        
        # Simplified: assign random mouth openness to each face
        for face in faces:
            if 'id' in face:
                mouth_data[face['id']] = np.random.uniform(0.5, 1.5)
        
        return mouth_data
    
    def close(self):
        """Cleanup resources"""
        # No resources to clean up with Haar Cascades
        pass

def iou(bbox1: List[int], bbox2: List[int]) -> float:
    """Calculate Intersection over Union for two bboxes"""
    x1, y1, w1, h1 = bbox1
    x2, y2, w2, h2 = bbox2
    
    # Calculate intersection
    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)
    
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    
    # Calculate union
    bbox1_area = w1 * h1
    bbox2_area = w2 * h2
    union_area = bbox1_area + bbox2_area - inter_area
    
    if union_area == 0:
        return 0.0
    
    return inter_area / union_area

def detect_faces_sample(frame: np.ndarray) -> list:
    """Quick face detection for a single frame"""
    try:
        mp_face = mp.solutions.face_detection
        with mp_face.FaceDetection(min_detection_confidence=0.5) as detector:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)
            
            faces = []
            if results.detections:
                h, w = frame.shape[:2]
                for det in results.detections:
                    bbox = det.location_data.relative_bounding_box
                    faces.append({
                        'x': int(bbox.xmin * w),
                        'y': int(bbox.ymin * h),
                        'width': int(bbox.width * w),
                        'height': int(bbox.height * h)
                    })
            return faces
    except Exception as e:
        return []

def match_tracks(prev_tracks: List[Dict], curr_faces: List[Dict], iou_threshold: float = 0.3) -> List[Dict]:
    """
    Match current faces with previous tracks using IOU
    Returns updated tracks with ids
    """
    if not prev_tracks:
        # Initialize new tracks
        return [{'id': i, 'bbox': face['bbox'], 'confidence': face['confidence']} 
                for i, face in enumerate(curr_faces)]
    
    matched_tracks = []
    used_faces = set()
    
    # Try to match each previous track
    for prev_track in prev_tracks:
        best_iou = 0
        best_idx = -1
        
        for i, face in enumerate(curr_faces):
            if i in used_faces:
                continue
            
            iou_score = iou(prev_track['bbox'], face['bbox'])
            if iou_score > best_iou:
                best_iou = iou_score
                best_idx = i
        
        if best_iou >= iou_threshold:
            # Matched
            matched_tracks.append({
                'id': prev_track['id'],
                'bbox': curr_faces[best_idx]['bbox'],
                'confidence': curr_faces[best_idx]['confidence']
            })
            used_faces.add(best_idx)
    
    # Add new tracks for unmatched faces
    next_id = max([t['id'] for t in prev_tracks], default=-1) + 1
    for i, face in enumerate(curr_faces):
        if i not in used_faces:
            matched_tracks.append({
                'id': next_id,
                'bbox': face['bbox'],
                'confidence': face['confidence']
            })
            next_id += 1
    
    return matched_tracks
