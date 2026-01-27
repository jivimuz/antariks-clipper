# Antariks Clipper

Auto-generate viral highlight clips from YouTube videos or manual uploads. Output vertical 9:16 format ready for Reels/TikTok.

## Features

- 🎬 **Multiple Input Sources**: YouTube URL or manual video upload
- 🤖 **AI-Powered Highlights**: Automatic clip generation with smart scoring
- 📝 **Transcription**: Faster-whisper for accurate speech-to-text
- 🎯 **Face Tracking**: Active speaker detection and auto-reframe (optional)
- 📱 **Vertical Output**: 1080x1920 (9:16) format for social media
- 💬 **Captions**: Burn-in subtitle support (optional)
- 🚀 **Simple Setup**: No Docker, Redis, or complex dependencies

## Quick Start

### Prerequisites

1. **Python 3.8+** (for backend)
2. **Node.js 18+** (for frontend)
3. **FFmpeg** - Must be installed on your system:
   - **Windows**: Download from https://ffmpeg.org/download.html and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg` (Ubuntu/Debian) or `sudo yum install ffmpeg` (CentOS/RHEL)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app:app --reload --port 8000
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at http://localhost:3000

### Usage

1. Open http://localhost:3000
2. Choose YouTube URL or Upload video
3. Submit and wait for processing
4. View generated highlight clips
5. Render clips with optional face tracking or captions
6. Download vertical 9:16 videos ready for social media

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLite** - Simple database (no ORM)
- **yt-dlp** - YouTube video download
- **faster-whisper** - Speech-to-text transcription
- **OpenCV + MediaPipe** - Face detection and tracking
- **FFmpeg** - Video processing via subprocess
- **ThreadPoolExecutor** - Background job processing (no external queue)

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling

## Project Structure

```
/
├── backend/
│   ├── app.py              # FastAPI application
│   ├── db.py               # SQLite database operations
│   ├── config.py           # Configuration
│   ├── services/           # Business logic modules
│   │   ├── downloader.py   # YouTube/upload handling
│   │   ├── ffmpeg.py       # Video processing utilities
│   │   ├── transcribe.py   # Whisper transcription
│   │   ├── highlight.py    # Clip generation & scoring
│   │   ├── thumbnails.py   # Thumbnail extraction
│   │   ├── face_track.py   # MediaPipe face detection
│   │   ├── reframe.py      # Active speaker tracking
│   │   ├── render.py       # Vertical video rendering
│   │   └── jobs.py         # Background job processing
│   ├── data/               # Generated files (gitignored)
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── app/
│   │   ├── page.tsx        # Home page (input)
│   │   ├── jobs/
│   │   │   ├── page.tsx    # Jobs list
│   │   │   └── [id]/page.tsx  # Job detail with clips
│   │   └── ...
│   ├── package.json
│   └── README.md
└── README.md               # This file
```

## API Endpoints

### Jobs
- `POST /api/jobs` - Create job (YouTube or upload)
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{job_id}` - Get job details
- `GET /api/jobs/{job_id}/clips` - Get job clips

### Renders
- `POST /api/clips/{clip_id}/render` - Create render job
- `GET /api/renders/{render_id}` - Get render status
- `GET /api/renders/{render_id}/download` - Download video

### Assets
- `GET /api/thumbnails/{clip_id}` - Get clip thumbnail

## Processing Pipeline

1. **Acquire**: Download (YouTube) or save upload
2. **Normalize**: Convert to standard format (H.264/AAC)
3. **Transcribe**: Generate transcript with word-level timestamps
4. **Generate Highlights**: Score segments based on:
   - Hook keywords (Indonesian + English)
   - Word density (unique words ratio)
   - Duration preference (ideal ~35 seconds)
5. **Create Thumbnails**: Extract mid-frame for each clip
6. **Render**: Create vertical 9:16 output with optional:
   - Face tracking (active speaker detection)
   - Captions (burned-in subtitles)

## Notes

- First run downloads Whisper model (~150MB for base model)
- Processing time depends on video length and options
- Face tracking is slower but provides better framing for podcasts
- All data stored locally in `backend/data/`
- No external services or API keys required

## License

MIT
