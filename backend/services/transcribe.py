"""Transcription service using faster-whisper"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, List
from faster_whisper import WhisperModel
from config import WHISPER_MODEL

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_model = None

def get_model():
    """Get or create Whisper model instance"""
    global _model
    if _model is None:
        logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model

def transcribe_video(video_path: Path, output_json_path: Path) -> bool:
    """Transcribe video and save results as JSON"""
    try:
        model = get_model()
        logger.info(f"Transcribing: {video_path}")
        
        segments, info = model.transcribe(str(video_path), beam_size=5, language="id")
        
        # Convert segments to list with word-level timestamps if available
        result = {
            "language": info.language,
            "duration": info.duration,
            "segments": []
        }
        
        for segment in segments:
            seg_data = {
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "words": []
            }
            
            # Add word-level timestamps if available
            if hasattr(segment, 'words') and segment.words:
                for word in segment.words:
                    seg_data["words"].append({
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability
                    })
            
            result["segments"].append(seg_data)
        
        # Save to JSON
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Transcription saved: {output_json_path}")
        return True
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return False

def load_transcript(json_path: Path) -> Dict[str, Any]:
    """Load transcript from JSON file"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Load transcript error: {e}")
        return {}
