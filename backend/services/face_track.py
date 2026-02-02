"""Face detection and tracking using MediaPipe"""
import logging
import cv2
import mediapipe as mp
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FaceTracker:
    """Face detection and tracking"""
    
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,  # Full range model
            min_detection_confidence=0.5
        )
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=5,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces in frame
        Returns list of {bbox: [x, y, w, h], confidence}
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)
        
        faces = []
        if results.detections:
            h, w, _ = frame.shape
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                faces.append({
                    'bbox': [x, y, width, height],
                    'confidence': detection.score[0]
                })
        
        return faces
    
    def get_mouth_openness(self, frame: np.ndarray, face_bbox: List[int]) -> Optional[float]:
        """
        Estimate mouth openness using face mesh
        Returns variance measure (higher = more movement/speaking)
        """
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                # Get first face mesh
                landmarks = results.multi_face_landmarks[0]
                h, w, _ = frame.shape
                
                # Upper lip and lower lip landmarks
                upper_lip = landmarks.landmark[13]
                lower_lip = landmarks.landmark[14]
                
                # Calculate vertical distance
                upper_y = upper_lip.y * h
                lower_y = lower_lip.y * h
                openness = abs(lower_y - upper_y)
                
                return openness
            
            return None
        except Exception as e:
            logger.debug(f"Mouth openness error: {e}")
            return None
    
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
        
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks and faces:
                h, w, _ = frame.shape
                
                # Match face landmarks to tracked faces by proximity
                for landmarks in results.multi_face_landmarks:
                    # Get mouth landmarks
                    upper_lip = landmarks.landmark[13]
                    lower_lip = landmarks.landmark[14]
                    
                    # Calculate vertical distance
                    upper_y = upper_lip.y * h
                    lower_y = lower_lip.y * h
                    openness = abs(lower_y - upper_y)
                    
                    # Match to closest face by checking face center proximity
                    mouth_center_x = (upper_lip.x + lower_lip.x) / 2 * w
                    mouth_center_y = (upper_lip.y + lower_lip.y) / 2 * h
                    
                    best_match_id = None
                    best_distance = float('inf')
                    
                    for face in faces:
                        fx, fy, fw, fh = face['bbox']
                        face_center_x = fx + fw // 2
                        face_center_y = fy + fh // 2
                        
                        distance = ((mouth_center_x - face_center_x) ** 2 + 
                                   (mouth_center_y - face_center_y) ** 2) ** 0.5
                        
                        if distance < best_distance:
                            best_distance = distance
                            best_match_id = face['id']
                    
                    if best_match_id is not None:
                        mouth_data[best_match_id] = openness
        
        except Exception as e:
            logger.debug(f"All mouth openness error: {e}")
        
        return mouth_data
    
    def close(self):
        """Cleanup resources"""
        self.face_detection.close()
        self.face_mesh.close()

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
