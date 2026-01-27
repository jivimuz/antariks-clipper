"""Configuration for Antariks Clipper Backend"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
NORMALIZED_DIR = DATA_DIR / "normalized"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
THUMBNAILS_DIR = DATA_DIR / "thumbnails"
RENDERS_DIR = DATA_DIR / "renders"

# Database
DB_PATH = DATA_DIR / "clipper.db"

# Processing
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "2"))
DEFAULT_CLIP_COUNT = int(os.getenv("DEFAULT_CLIP_COUNT", "12"))
MIN_CLIP_DURATION = float(os.getenv("MIN_CLIP_DURATION", "15"))
MAX_CLIP_DURATION = float(os.getenv("MAX_CLIP_DURATION", "60"))
IDEAL_CLIP_DURATION = float(os.getenv("IDEAL_CLIP_DURATION", "35"))

# Whisper
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# Video output
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920

# Face tracking
FACE_DETECTION_INTERVAL = 2  # Process every N frames
EMA_ALPHA = 0.2  # Smoothing for center tracking

# Ensure directories exist
for directory in [DATA_DIR, RAW_DIR, NORMALIZED_DIR, TRANSCRIPTS_DIR, THUMBNAILS_DIR, RENDERS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
