# Features & Capabilities

## Core Features

### 🎬 Video Input
- **YouTube Download**: Paste any YouTube URL to automatically download and process
- **Manual Upload**: Upload videos directly from your computer
- **Supported Formats**: MP4, AVI, MOV, MKV, and more (via FFmpeg)
- **No Size Limit**: Process videos of any length (processing time scales accordingly)

### 🤖 AI-Powered Highlights
- **Automatic Detection**: Identifies the most engaging moments in your video
- **Smart Scoring**: Uses multi-factor algorithm:
  - Hook keywords (Indonesian + English)
  - Word density and variety
  - Optimal duration preferences
- **Customizable**: Configure clip count, min/max duration via environment variables
- **Default Output**: Top 12 highlights per video

### 📝 Transcription
- **Whisper AI**: Powered by OpenAI's Whisper model (faster-whisper implementation)
- **Word-Level Timestamps**: Precise timing for each spoken word
- **Multiple Languages**: Optimized for Indonesian and English
- **Model Options**: Choose from base, small, medium, or large models
- **Offline Processing**: No API calls or external services required

### 🎯 Face Tracking & Reframing
- **Active Speaker Detection**: Automatically identifies who is speaking
- **MediaPipe Integration**: High-quality face detection
- **Smooth Tracking**: EMA smoothing prevents jittery camera movements
- **Multi-Face Support**: Tracks up to 5 faces simultaneously
- **Smart Centering**: Auto-crops to keep active speaker in frame
- **Mouth Openness Detection**: Uses facial landmarks to detect speech

### 📱 Vertical Video Output
- **9:16 Aspect Ratio**: Perfect for Instagram Reels, TikTok, YouTube Shorts
- **1080x1920 Resolution**: High-quality output ready for social media
- **Center Crop**: Intelligent framing for non-tracking renders
- **Face-Tracked Crop**: Dynamic reframing following the speaker
- **Audio Preservation**: Maintains original audio quality

### 💬 Captions/Subtitles
- **Auto-Generated**: Created from transcription
- **Burned-In**: Embedded directly into video (no separate SRT file needed)
- **Customizable Style**: Edit subtitle appearance in code
- **Synchronized**: Perfectly timed with speech
- **Optional**: Enable/disable per render

## Technical Features

### 🚀 Simple Architecture
- **No Docker**: Direct Python and Node.js installation
- **No Redis/Celery**: ThreadPoolExecutor for background jobs
- **No Complex Queue**: Simple in-memory job processing
- **SQLite Database**: No database server required
- **File-Based Storage**: All outputs stored locally

### ⚡ Performance
- **Parallel Processing**: Multiple workers for concurrent jobs
- **Optimized Pipeline**: Efficient step-by-step processing
- **Progress Tracking**: Real-time updates on job status
- **Smart Caching**: Reuses normalized videos for multiple renders
- **Background Jobs**: Non-blocking API for responsive UI

### 🔒 Security & Privacy
- **Local Processing**: All data stays on your machine
- **No Cloud Services**: No third-party API calls
- **No User Tracking**: No analytics or telemetry
- **Secure Storage**: Files stored in local data directory
- **CORS Protection**: Configurable allowed origins

### 📊 Job Management
- **Job Queue**: Sequential processing of video jobs
- **Status Tracking**: Monitor progress from 0-100%
- **Error Handling**: Detailed error messages for failures
- **Job History**: View all past jobs and their status
- **Clip Library**: Browse all generated clips per job

### 🎨 User Interface
- **Modern Design**: Clean, responsive Tailwind CSS styling
- **Real-Time Updates**: Auto-polling for job/render status
- **Thumbnail Previews**: Visual preview of each clip
- **Mobile Responsive**: Works on desktop, tablet, and mobile
- **Dark Mode Support**: Automatic theme switching
- **Interactive API Docs**: Built-in Swagger UI at /docs

## API Features

### RESTful Endpoints
- `POST /api/jobs` - Create new processing job
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{id}` - Get job details
- `GET /api/jobs/{id}/clips` - Get clips for job
- `POST /api/clips/{id}/render` - Create render
- `GET /api/renders/{id}` - Get render status
- `GET /api/renders/{id}/download` - Download video
- `GET /api/thumbnails/{id}` - Get clip thumbnail

### API Documentation
- **Swagger UI**: Interactive API testing at /docs
- **ReDoc**: Alternative docs at /redoc
- **OpenAPI Schema**: Machine-readable specification
- **Type Safety**: Pydantic models for request/response

## Customization Options

### Configuration (.env)
```bash
# Worker threads for parallel processing
MAX_WORKERS=2

# Highlight generation
DEFAULT_CLIP_COUNT=12      # Number of clips to generate
MIN_CLIP_DURATION=15       # Minimum clip length (seconds)
MAX_CLIP_DURATION=60       # Maximum clip length (seconds)
IDEAL_CLIP_DURATION=35     # Target clip length (seconds)

# Whisper model (base|small|medium|large)
WHISPER_MODEL=base
```

### Render Options
- **Face Tracking**: Enable/disable active speaker tracking
- **Captions**: Enable/disable burned-in subtitles
- **Quality**: Configurable video bitrate and encoding
- **Speed**: Choose between quality and processing time

### Scoring Algorithm
Customize hook keywords in `backend/services/highlight.py`:
```python
HOOK_KEYWORDS = [
    "ini penting", "gila", "ternyata",
    # Add your own keywords here
]
```

## Limitations & Constraints

### Current Limitations
- **Single Language Model**: Best for Indonesian/English (configurable)
- **Sequential Jobs**: One video processed at a time (parallel renders supported)
- **CPU Processing**: No GPU acceleration (yet)
- **Local Storage**: All files stored on server disk
- **No Authentication**: Open API (add auth for production)

### System Requirements
- **Minimum**:
  - 2 CPU cores
  - 4GB RAM
  - 5GB disk space (models + processing)
- **Recommended**:
  - 4+ CPU cores
  - 8GB+ RAM
  - 20GB+ disk space

### Processing Time
- **10-minute video**: ~3-6 minutes
- **Simple render (30s clip)**: ~10-20 seconds
- **Face tracking render (30s clip)**: ~60-120 seconds
- **With captions**: +10-20 seconds

## Future Enhancements (Potential)

### Could Be Added
- ✨ GPU acceleration for faster processing
- 🌍 Additional language support
- 🎵 Background music addition
- 🎨 Customizable subtitle styles via UI
- 📊 Analytics and metrics
- 🔐 User authentication
- ☁️ Cloud storage integration
- 📧 Email notifications on completion
- 🎬 Video preview in browser
- ⚙️ Advanced editing features
- 🤝 Batch processing
- 📱 Mobile app

## Use Cases

### Perfect For
- 📺 **Podcast Highlights**: Extract best moments from long-form content
- 🎓 **Educational Content**: Create bite-sized learning clips
- 🎤 **Interview Clips**: Share key quotes and insights
- 🎮 **Gaming Montages**: Highlight epic moments
- 📈 **Marketing**: Repurpose webinars into social content
- 🎪 **Event Recaps**: Create shareable moments from recordings

### Industries
- Content Creators
- Digital Marketers
- Educational Institutions
- Media Companies
- Influencers & Bloggers
- Corporate Communications

## Technology Stack

### Backend
- **FastAPI** - High-performance async web framework
- **SQLite** - Lightweight embedded database
- **yt-dlp** - Robust YouTube downloader
- **faster-whisper** - Optimized Whisper implementation
- **OpenCV** - Computer vision processing
- **MediaPipe** - ML-powered face detection
- **FFmpeg** - Industry-standard media processing

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **React Hooks** - Modern React patterns

## Comparison with Alternatives

### Why Antariks Clipper?

| Feature | Antariks Clipper | Cloud Services | Desktop Apps |
|---------|------------------|----------------|--------------|
| **Cost** | Free | $20-100/month | $50-300 one-time |
| **Privacy** | 100% local | Cloud storage | Local |
| **Setup** | 5 minutes | Instant | 10-30 minutes |
| **Customization** | Full source code | Limited | None |
| **API** | Full REST API | Varies | None |
| **Offline** | Yes | No | Yes |
| **Face Tracking** | Yes | Some | Rare |
| **Auto Highlights** | Yes | Some | Manual |
| **Vertical Format** | Built-in | Yes | Usually |
| **Dependencies** | Python, Node, FFmpeg | Browser | None |

### Key Differentiators
1. **Free & Open Source**: No subscription fees
2. **Privacy First**: No data leaves your machine
3. **Fully Customizable**: Modify any part of the system
4. **AI-Powered**: Smart highlight detection
5. **Simple Setup**: No Docker or complex infrastructure

## Getting Started

Ready to create viral clips? Check out:
- 📖 [Quick Start Guide](QUICKSTART.md) - 5-minute setup
- 🏗️ [Architecture](ARCHITECTURE.md) - Technical details
- 📚 [README](README.md) - Overview and installation

## License

MIT License - Free to use, modify, and distribute.
