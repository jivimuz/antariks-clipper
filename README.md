# Antariks Clipper

Auto-generate viral highlight clips from YouTube videos or manual uploads. Output vertical 9:16 format ready for Reels/TikTok.

## Features

### Core Features
- 🎬 **Multiple Input Sources**: YouTube URL or manual video upload
- 🤖 **Enhanced AI-Powered Highlights**: Advanced clip generation with smart scoring
  - **Dynamic clip detection** for long videos (2+ hours)
  - **Adaptive clip count** based on video duration (5-50 clips automatically)
  - **Variable clip duration** (15-60 seconds based on content)
  - **Intelligent keyword detection** with categories (importance, revelation, summary, teaching)
- 📝 **Transcription**: Faster-whisper for accurate speech-to-text
- 🎯 **Face Tracking**: Active speaker detection and auto-reframe (optional)
- 📱 **Vertical Output**: 1080x1920 (9:16) format for social media
- 💬 **Captions**: Burn-in subtitle support (optional)

### Advanced Features
- 🔄 **Regenerate Highlights**: Customize clip count and regenerate anytime
- 🎚️ **Filter & Sort**: Filter by score, sort by score/duration/timeline
- ✅ **Batch Selection**: Select multiple clips for batch rendering
- 📊 **Rich Metadata**: Each clip includes keyword categories and content analysis
- 📋 **Preview Interface**: Preview clips before rendering
- 📱 **Social Media Ready**: Auto-generated captions and hashtags for TikTok, Instagram Reels, Facebook Shorts
  - **Smart Captions**: Context-aware captions with emojis based on content category
  - **Auto Hashtags**: Default tags (#fyp #viral #antariksclipper) plus content-specific tags
  - **One-Click Copy**: Easy copy-to-clipboard for captions and hashtags
- 🔐 **License Management**: Smart license expiry handling
  - **Expiry Warning**: Toast notification when license is expiring soon (< 3 days)
  - **Auto-Logout**: Automatic logout when license expires with notification
  - **Real-time Checking**: License validation on every page load
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
4. View generated highlight clips (automatically generates 5-50 clips based on video length)
5. Use filters and sorting to find the best clips:
   - **Filter by score**: Use the slider to show only high-scoring clips
   - **Sort options**: By score, duration, or timeline position
6. Select clips for rendering:
   - Click checkboxes to select individual clips
   - Use "Select All" to select all visible clips
   - Click "Render N Clips" to batch render selected clips
7. Preview clips before rendering (click any clip to preview)
8. **View auto-generated captions and hashtags** in the preview panel:
   - 📝 **Caption**: Context-aware text with emojis ready for social media
   - 🏷️ **Hashtags**: Auto-generated tags optimized for reach (#fyp #viral #antariksclipper + content-specific)
   - 📋 **One-click copy**: Click copy buttons to copy caption or hashtags to clipboard
9. Render clips with optional face tracking, smart crop, or captions
10. Download vertical 9:16 videos ready for social media
11. Copy the caption and hashtags when posting to TikTok, Instagram Reels, or Facebook Shorts

### Social Media Caption & Hashtags

Each clip automatically includes:

- **Smart Caption**: 
  - Contextual text based on clip content
  - Emoji indicators (⚠️ Important, 💡 Key Point, 📚 Tutorial, 📌 Summary)
  - Call-to-action to boost engagement
  - Ready for TikTok, Instagram Reels, Facebook Shorts

- **Auto Hashtags**:
  - Default tags: `#fyp #viral #antariksclipper`
  - Category-based tags (teaching → `#tutorial #howto #learn`)
  - Topic keywords extracted from clip title
  - Platform-optimized tags: `#reels #shorts #contentcreator`
  - Up to 15 hashtags to maximize reach without spam

**Example Output**:
```
Caption:
⚠️ Important Tutorial: How to Build APIs

This is a crucial tip that every developer needs to know

💬 What do you think? Comment below!

Hashtags:
#fyp #viral #antariksclipper #important #musttknow #tips #tutorial #build #apis #reels #shorts #contentcreator
```

### Advanced Usage

#### Regenerate Highlights
If the auto-generated clips aren't perfect, you can regenerate them:
1. Click "Regenerate Highlights" button
2. Optionally specify custom clip count (or leave empty for auto)
3. System will delete old clips and generate new ones

#### Batch Create Custom Clips
For manual control, use the "Batch Create Clips" section:
1. Enter start/end times manually
2. Add multiple rows for multiple clips
3. Save all clips at once

### License Management

Antariks Clipper includes intelligent license management to ensure seamless user experience:

#### Expiry Notifications
- **Early Warning**: When your license is expiring soon (less than 3 days), you'll see a warning toast notification on every page load
- **Clear Information**: The notification shows exactly how many days remain (e.g., "Lisensi Anda akan berakhir 2 hari lagi")
- **Non-intrusive**: The notification doesn't block your workflow if the license is still valid

#### Auto-Logout on Expiry
- **Automatic**: When your license expires, the system automatically logs you out
- **Clear Message**: A toast notification appears: "Lisensi Anda telah berakhir" (Your license has expired)
- **Redirect to Login**: You're automatically redirected to the login page
- **Data Protection**: This ensures expired users cannot access the system

#### How It Works
1. **On Page Load**: Every time you navigate or load a page, the system checks your license status
2. **Backend Validation**: The license is validated against the external license server
3. **Smart Detection**: The system calculates days remaining and determines if action is needed
4. **Responsive**: All checks happen in the background without blocking the UI

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

## Enhanced Highlight Detection Algorithm

The system uses an advanced multi-factor scoring algorithm to identify the best clips:

### Scoring Factors (100 points max)

1. **Hook Keywords (35 points)** - Weighted by category:
   - **Importance**: "ini penting", "kuncinya", "harus tahu", "important", "crucial"
   - **Revelation**: "gila", "ternyata", "rahasia", "secret", "amazing", "shocking"
   - **Summary**: "jadi intinya", "kesimpulannya", "in conclusion", "to summarize"
   - **Teaching**: "cara", "tutorial", "how to", "step by step", "pro tip"

2. **Content Quality (25 points)**:
   - Vocabulary diversity (unique word ratio)
   - Optimal word count (50-150 words sweet spot)
   - Question detection (engagement indicator)

3. **Duration Flexibility (25 points)**:
   - Sweet spot: 20-45 seconds (25 points)
   - Good range: 15-60 seconds (20 points)
   - Dynamically adjusts to content, not fixed 35 seconds

4. **Position Diversity (15 points)**:
   - Favors content from different parts of the video
   - Strong beginning/ending segments (memorable moments)
   - Ensures clips span the entire video timeline

### Adaptive Algorithm for Long Videos

- **Dynamic clip count**: Automatically scales from 5 to 50 clips based on video duration
- **Efficient processing**: Uses adaptive stepping (3x faster) for videos > 1 hour
- **Non-overlapping**: Maintains minimum 10-second gap between clips
- **Timeline coverage**: Ensures clips are distributed throughout the video

### Testing

Run the comprehensive test suite:
```bash
cd backend
python test_highlight_enhanced.py
```

Tests include:
- Dynamic clip count calculation
- Keyword detection and categorization
- Scoring algorithm validation
- Short video (10 min) highlight generation
- Long video (2+ hours) highlight generation with adaptive algorithm
- Custom clip count parameters

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
- `POST /api/jobs/{job_id}/retry` - Retry failed job
- `DELETE /api/jobs/{job_id}` - Delete job and all associated data
- `POST /api/jobs/{job_id}/clips` - Batch create custom clips
- **`POST /api/jobs/{job_id}/regenerate-highlights`** - ✨ NEW: Regenerate highlight clips with custom parameters

### Clips
- **`DELETE /api/clips/{clip_id}`** - ✨ NEW: Delete individual clip
- `GET /api/clips/{clip_id}/preview` - Preview clip stream
- `GET /api/clips/{clip_id}/preview-frame` - Get preview thumbnail

**Clip Response (includes caption & hashtags)**:
```json
{
  "id": "clip-uuid",
  "job_id": "job-uuid",
  "start_sec": 10.5,
  "end_sec": 45.2,
  "score": 85.3,
  "title": "Important Tutorial",
  "transcript_snippet": "This is the clip content...",
  "caption_text": "⚠️ Important Tutorial\n\nThis is the clip content...\n\n💬 What do you think?",
  "hashtags_text": "#fyp #viral #antariksclipper #important #tutorial #reels #shorts"
}
```

### Renders
- `POST /api/clips/{clip_id}/render` - Create render job
- `GET /api/renders/{render_id}` - Get render status
- `GET /api/renders/{render_id}/download` - Download video
- `POST /api/renders/{render_id}/retry` - Retry failed render

### Assets
- `GET /api/thumbnails/{clip_id}` - Get clip thumbnail

### Regenerate Highlights API

**Endpoint**: `POST /api/jobs/{job_id}/regenerate-highlights`

**Request Body**:
```json
{
  "clip_count": 20,      // Optional: number of clips (null = auto-calculate)
  "adaptive": true       // Use adaptive algorithm for long videos
}
```

**Response**:
```json
{
  "success": true,
  "deleted": 12,         // Number of old clips deleted
  "created": 20,         // Number of new clips created
  "clips": [...]         // Array of new clips with metadata
}
```

## Processing Pipeline

1. **Acquire**: Download (YouTube) or save upload
2. **Transcribe**: Generate transcript with word-level timestamps (directly from raw video)
3. **Generate Highlights**: Enhanced scoring algorithm:
   - **Hook keywords** with 4 categories (importance, revelation, summary, teaching)
   - **Content quality** analysis (word density, vocabulary diversity, questions)
   - **Dynamic duration** (15-60 seconds based on content, not fixed)
   - **Position diversity** (distributes clips throughout video)
   - **Adaptive clip count** (5-50 clips based on video duration)
4. **Create Thumbnails**: Extract mid-frame for each clip
5. **Ready for Preview**: Clips available for selection and preview
6. **Render** (on demand): Create vertical 9:16 output with optional:
   - Face tracking (active speaker detection)
   - Smart crop (multi-person framing)
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
