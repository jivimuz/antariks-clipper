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
4. **JavaScript Runtime** (for YouTube downloads) - yt-dlp requires a JS runtime:
   - **Option 1 - Deno (recommended)**:
     - Windows: `irm https://deno.land/install.ps1 | iex`
     - macOS/Linux: `curl -fsSL https://deno.land/install.sh | sh`
   - **Option 2 - Node.js**: Download from https://nodejs.org/

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

## Troubleshooting

### YouTube Download Issues

#### Error: "Video is unavailable or has been removed"
- The video may have been deleted, made private, or removed by the uploader
- Verify the URL is correct and the video is publicly accessible
- Try a different video to confirm the system is working

#### Error: "Video is blocked in your region"
- The video has geographical restrictions
- Consider using a VPN or try a different video
- Some videos may be permanently restricted in certain regions

#### Error: "Video is age-restricted and requires authentication"
- The video requires sign-in to view
- You can provide a cookies.txt file from your browser session:
  1. Install a browser extension like "Get cookies.txt"
  2. Export cookies from YouTube while logged in
  3. Place the file in the backend directory
  4. The system will automatically use it for downloads

#### Error: "Access forbidden" or HTTP 403
This can have several causes:

1. **Update yt-dlp** (YouTube changes frequently):
   ```bash
   pip install --upgrade yt-dlp
   ```

2. **Install JavaScript runtime** (required for YouTube extraction):
   ```bash
   # Option 1: Deno (recommended)
   # Windows PowerShell:
   irm https://deno.land/install.ps1 | iex
   # macOS/Linux:
   curl -fsSL https://deno.land/install.sh | sh
   
   # Option 2: Install Node.js from https://nodejs.org/
   ```

3. **Verify ffmpeg is installed**:
   ```bash
   ffmpeg -version
   ```

4. **Restart the backend** after installing dependencies

5. **Wait and retry** - Sometimes YouTube temporarily blocks too many requests

#### Error: "Too many requests"
- YouTube has rate-limited your IP address
- Wait 10-15 minutes before trying again
- Reduce the frequency of download requests

#### Error: "Network error" or "Connection timeout"
- Check your internet connection
- The video server may be temporarily unavailable
- The system will automatically retry with exponential backoff
- Try again in a few minutes

### Video Processing Errors

#### Transcription Failed
- Ensure the video has an audio track
- Supported languages: English, Indonesian (primary), and many others
- Videos without speech cannot generate highlights
- Check that the audio format is supported (MP3, AAC, WAV)

#### No Highlights Generated
- Video needs sufficient spoken content (minimum ~30 seconds)
- Speech must be clear and detectable
- Try adjusting the video's audio levels if very quiet
- Silent videos or music-only videos won't generate highlights

#### Render Failed
- Ensure the raw video file still exists
- Check available disk space
- Try with simpler options (disable face tracking/smart crop)
- Check the logs for specific FFmpeg errors

### General Issues

#### Missing Dependencies
If you see errors about missing `ffmpeg` or `yt-dlp`:

```bash
# Install ffmpeg
# Ubuntu/Debian:
sudo apt-get update && sudo apt-get install -y ffmpeg

# macOS:
brew install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html and add to PATH

# Install yt-dlp
pip install --upgrade yt-dlp
```

#### Whisper Model Download
First run will download the Whisper model (~150MB). If it fails:
- Check internet connection
- Ensure enough disk space
- The model will be cached for future use

#### Jobs Stuck in Processing
- Check the backend logs for specific errors
- The job may have failed silently - check the error field
- You can retry the job from the UI
- Ensure all dependencies are installed correctly

### Getting More Information

#### Enable Debug Logging
To see detailed logs:
1. Edit `backend/app.py`
2. Change logging level to DEBUG:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```
3. Restart the backend
4. Check logs for detailed processing information

#### Check Logs
- Backend logs show detailed processing steps
- Each major operation is logged with ✓ (success) or ❌ (error)
- Look for ERROR or WARNING level messages
- File paths and sizes are logged for debugging

## License

MIT
