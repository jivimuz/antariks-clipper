"""Transcription service using faster-whisper"""
import logging
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from utils import get_subprocess_startup_info, get_subprocess_creation_flags

# Try importing faster-whisper, provide fallback if not available
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    WhisperModel = None
    
from config import WHISPER_MODEL
from services.ffmpeg import get_audio_info

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_model = None

def get_model():
    """Get or create Whisper model instance"""
    global _model
    
    if not FASTER_WHISPER_AVAILABLE:
        raise ImportError(
            "faster-whisper is not installed. "
            "Please install it: pip install faster-whisper"
        )
    
    if _model is None:
        logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model

def _transcribe_path(model: WhisperModel, input_path: Path, output_json_path: Path) -> bool:
    """Transcribe input path and save results as JSON."""
    try:
        logger.info(f"_transcribe_path: Attempting Whisper transcription on {input_path}")
        logger.info(f"_transcribe_path: File exists: {input_path.exists()}, Size: {input_path.stat().st_size if input_path.exists() else 'N/A'}")
        
        # Use beam_size=1 for speed (faster than default 5)
        # language="id" for Indonesian
        segments, info = model.transcribe(
            str(input_path), 
            beam_size=1,  # Reduce from 5 to 1 for faster transcription (CPU optimization)
            language="id"
        )

        # Convert segments to list with word-level timestamps if available
        # NOTE: Convert to list immediately since generators are single-use
        segments_list = list(segments)
        logger.info(f"_transcribe_path: Whisper finished, processing {len(segments_list)} segments")
        
        if not segments_list:
            logger.warning(f"_transcribe_path: Whisper returned 0 segments!")
        
        result = {
            "language": info.language,
            "duration": info.duration,
            "segments": []
        }

        for segment in segments_list:
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

        logger.info(f"✓ Transcription saved: {output_json_path} ({len(result['segments'])} segments)")
        return True
    
    except Exception as e:
        logger.error(f"_transcribe_path exception: {type(e).__name__}: {e}", exc_info=True)
        raise


def _extract_audio_wav(video_path: Path, output_path: Path) -> bool:
    """Extract audio to 16kHz mono WAV for robust transcription."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Extracting audio to WAV (16kHz mono PCM): {output_path}")
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_path),
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            str(output_path)
        ]
        # Increase timeout to 30 minutes for large files
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())
        if result.returncode != 0:
            logger.error(f"Extract audio failed: {result.stderr}")
            return False
        
        if output_path.exists():
            size_mb = output_path.stat().st_size / 1024 / 1024
            logger.info(f"Audio WAV extracted successfully: {size_mb:.1f} MB")
            return True
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Audio extraction timeout (>30 minutes)")
        return False
    except Exception as e:
        logger.error(f"Audio extraction exception: {e}")
        return False


def transcribe_video(video_path: Path, output_json_path: Path) -> bool:
    """Transcribe video and save results as JSON"""
    try:
        model = get_model()
        logger.info(f"Transcribing: {video_path}")
        
        video_size_mb = video_path.stat().st_size / 1024 / 1024
        logger.info(f"Video file size: {video_size_mb:.1f} MB")
        
        # Estimate transcription time (very rough: ~1 minute per 50MB on CPU int8)
        estimated_minutes = max(2, int(video_size_mb / 50))
        logger.info(f"Estimated transcription time: ~{estimated_minutes} minutes (CPU int8 is slow!)")

        audio_info = get_audio_info(video_path)
        if not audio_info:
            logger.warning("⚠️ No audio stream detected by ffprobe, attempting transcription anyway (may fail if truly no audio)")
        else:
            logger.info(f"✓ Audio detected: {audio_info}")

        # First try direct transcription
        logger.info("Attempting direct transcription...")
        try:
            logger.info("Whisper model transcribing (this may take several minutes for large videos)...")
            return _transcribe_path(model, video_path, output_json_path)
        except Exception as e:
            logger.warning(f"Direct transcription failed ({type(e).__name__}): {e}")
            logger.info("Trying WAV extraction fallback...")

        # Fallback: extract audio to WAV and transcribe
        logger.info("Starting WAV extraction fallback...")
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "audio.wav"
            logger.info(f"Extracting audio to temporary WAV...")
            if not _extract_audio_wav(video_path, wav_path):
                logger.error("❌ Audio extraction failed - video may not have an audio stream")
                return False
            
            # Check if WAV was created with actual content
            if not wav_path.exists():
                logger.error("❌ WAV file was not created during extraction")
                return False
            
            wav_size = wav_path.stat().st_size
            logger.info(f"WAV file created: {wav_size / 1024 / 1024:.1f} MB")
            
            if wav_size < 100000:  # Less than 100KB is suspicious
                logger.error("❌ WAV file is too small - likely contains no audio data")
                return False
            
            logger.info(f"Transcribing from WAV file...")
            logger.info(f"Whisper model transcribing (this may take several minutes)...")
            result = _transcribe_path(model, wav_path, output_json_path)
            if result:
                logger.info(f"✓ Transcription successful via WAV fallback")
            else:
                logger.error(f"❌ WAV transcription also failed")
            return result

    except Exception as e:
        logger.error(f"Transcription error: {type(e).__name__}: {e}", exc_info=True)
        return False

def transcribe(video_path: Path, output_json_path: Path) -> bool:
    """Alias for transcribe_video for backward compatibility"""
    return transcribe_video(video_path, output_json_path)

def load_transcript(json_path: Path) -> Dict[str, Any]:
    """Load transcript from JSON file"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Load transcript error: {e}")
        return {}
