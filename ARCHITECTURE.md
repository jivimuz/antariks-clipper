# Antariks Clipper - Architecture & Implementation Details

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                   │
│  ┌───────────┐  ┌───────────┐  ┌─────────────────────────┐ │
│  │   Home    │  │   Jobs    │  │   Job Detail + Clips    │ │
│  │  (Input)  │  │  (List)   │  │  (Grid + Render)        │ │
│  └─────┬─────┘  └─────┬─────┘  └───────────┬─────────────┘ │
│        │              │                     │                │
│        └──────────────┴─────────────────────┘                │
│                       │ HTTP/REST                            │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    API Endpoints                      │   │
│  │  /api/jobs, /api/clips, /api/renders, /api/thumbnails│   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐   │
│  │         ThreadPoolExecutor (Background Jobs)         │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐   │
│  │                Service Layer                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│   │
│  │  │Download  │ │ FFmpeg   │ │Transcribe│ │Highlight ││   │
│  │  │          │ │          │ │          │ │          ││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘│   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│   │
│  │  │FaceTrack │ │ Reframe  │ │  Render  │ │  Jobs    ││   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘│   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐   │
│  │                 SQLite Database                       │   │
│  │         (jobs, clips, renders tables)                 │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 External Dependencies                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  FFmpeg  │ │ yt-dlp   │ │ Whisper  │ │  MediaPipe   │   │
│  │  (CLI)   │ │          │ │  Model   │ │ (Face Det.)  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Processing Pipeline

### Job Creation Flow
```
User Input (YouTube URL or Upload)
    │
    ▼
POST /api/jobs
    │
    ├─> Create job record (status: queued)
    │
    └─> Submit to ThreadPoolExecutor
            │
            ▼
        process_job()
```

### Job Processing Pipeline
```
1. ACQUIRE (10-20%)
   ├─ YouTube: yt-dlp download → data/raw/{job_id}.mp4
   └─ Upload: Save file → data/raw/{job_id}_upload.ext
   
2. NORMALIZE (20-40%)
   └─ FFmpeg: Convert to H.264/AAC → data/normalized/{job_id}.mp4
   
3. TRANSCRIBE (40-60%)
   └─ faster-whisper: Generate transcript → data/transcripts/{job_id}.json
   
4. GENERATE HIGHLIGHTS (60-80%)
   ├─ Analyze transcript segments
   ├─ Score based on:
   │  ├─ Hook keywords (30 points)
   │  ├─ Word density (30 points)
   │  └─ Duration preference (40 points)
   ├─ Remove overlaps
   └─ Select top N clips
   
5. CREATE CLIPS (80-100%)
   ├─ For each highlight:
   │  ├─ Create clip record
   │  └─ Generate thumbnail → data/thumbnails/{clip_id}.jpg
   └─ Set job status: ready
```

### Render Flow
```
User clicks "Render" on clip
    │
    ▼
POST /api/clips/{clip_id}/render
    │
    ├─> Create render record (status: queued)
    │
    └─> Submit to ThreadPoolExecutor
            │
            ▼
        process_render()
            │
            ▼
    ┌───────────────────────────────┐
    │  Face Tracking Enabled?       │
    └───────┬───────────────────────┘
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
  YES               NO
    │                │
    ├─ Extract segment
    ├─ Process frames:
    │  ├─ Detect faces (MediaPipe)
    │  ├─ Track identities (IOU)
    │  ├─ Detect active speaker:
    │  │  ├─ Mouth openness variance
    │  │  └─ Face size
    │  ├─ Calculate crop center (EMA)
    │  └─ Crop & resize to 1080x1920
    ├─ Extract audio
    └─ Mux video + audio
                     │
                     ├─ Extract segment
                     ├─ Center crop to 9:16
                     └─ Scale to 1080x1920
                     │
    ┌────────────────┴────────────────┐
    │   Captions Enabled?             │
    └─────────┬───────────────────────┘
              │
      ┌───────┴────────┐
      │                │
      ▼                ▼
     YES               NO
      │                │
      ├─ Generate SRT  │
      ├─ Burn subtitles│
      └─ Final output  └─> Final output
              │
              ▼
    data/renders/{render_id}.mp4
              │
              ▼
    Set render status: ready
```

## Database Schema

### jobs
```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,        -- "youtube" | "upload"
    source_url TEXT,                   -- YouTube URL (if applicable)
    raw_path TEXT,                     -- Path to raw video
    normalized_path TEXT,              -- Path to normalized video
    status TEXT DEFAULT 'queued',      -- "queued" | "processing" | "ready" | "failed"
    step TEXT DEFAULT '',              -- Current processing step
    progress INTEGER DEFAULT 0,        -- 0-100
    error TEXT,                        -- Error message if failed
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### clips
```sql
CREATE TABLE clips (
    id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    start_sec REAL NOT NULL,           -- Start time in seconds
    end_sec REAL NOT NULL,             -- End time in seconds
    score REAL DEFAULT 0,              -- Highlight score
    title TEXT,                        -- "Highlight 1", "Highlight 2", etc.
    transcript_snippet TEXT,           -- Preview text
    thumbnail_path TEXT,               -- Path to thumbnail image
    created_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

### renders
```sql
CREATE TABLE renders (
    id TEXT PRIMARY KEY,
    clip_id TEXT NOT NULL,
    status TEXT DEFAULT 'queued',      -- "queued" | "processing" | "ready" | "failed"
    progress INTEGER DEFAULT 0,        -- 0-100
    output_path TEXT,                  -- Path to rendered video
    options_json TEXT,                 -- JSON: {face_tracking, captions}
    error TEXT,                        -- Error message if failed
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (clip_id) REFERENCES clips(id)
);
```

## Highlight Scoring Algorithm

```python
def score_segment(text, start, end, duration):
    score = 0.0
    
    # 1. Hook keywords (up to 30 points)
    keyword_matches = count_keywords(text)
    score += min(keyword_matches * 10, 30)
    
    # 2. Word density (up to 30 points)
    unique_ratio = unique_words / total_words
    score += unique_ratio * 30
    
    # 3. Duration preference (up to 40 points)
    clip_duration = end - start
    duration_diff = abs(clip_duration - IDEAL_DURATION)
    score += 40 * (1 - duration_diff / max_diff)
    
    return score
```

**Hook Keywords (Indonesian + English):**
- Indonesian: "ini penting", "gila", "ternyata", "jadi intinya", "kuncinya", "serius", "yang paling", "rahasia", "trik", "tips", "cara terbaik", "harus tahu"
- English: "important", "secret", "amazing", "incredible", "shocking", "must know", "pro tip", "game changer", "breakthrough", "revelation"

## Face Tracking & Active Speaker Detection

### Process:
1. **Detect Faces**: MediaPipe Face Detection every N frames
2. **Track Identities**: IOU matching between frames
3. **Detect Active Speaker**:
   - Primary: Mouth openness variance (Face Mesh)
   - Fallback: Face size (larger = closer = likely speaking)
4. **Calculate Crop Center**: EMA smoothing (α=0.2)
5. **Constrain**: Ensure crop stays within video bounds
6. **Crop & Resize**: Extract 9:16 region, scale to 1080x1920

### EMA Smoothing:
```python
center_x = α * target_x + (1 - α) * prev_center_x
center_y = α * target_y + (1 - α) * prev_center_y
```

## Configuration

### Environment Variables (.env)
```
MAX_WORKERS=2              # Thread pool size
DEFAULT_CLIP_COUNT=12      # Number of highlights to generate
MIN_CLIP_DURATION=15       # Minimum clip length (seconds)
MAX_CLIP_DURATION=60       # Maximum clip length (seconds)
IDEAL_CLIP_DURATION=35     # Target clip length (seconds)
WHISPER_MODEL=base         # Whisper model size (base|small|medium|large)
```

### Constants
```python
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
FACE_DETECTION_INTERVAL = 2  # Process every N frames
EMA_ALPHA = 0.2              # Smoothing factor for tracking
```

## API Examples

### Create YouTube Job
```bash
curl -X POST http://localhost:8000/api/jobs \
  -F "source_type=youtube" \
  -F "youtube_url=https://www.youtube.com/watch?v=..."
```

### Create Upload Job
```bash
curl -X POST http://localhost:8000/api/jobs \
  -F "source_type=upload" \
  -F "file=@video.mp4"
```

### Get Job Status
```bash
curl http://localhost:8000/api/jobs/{job_id}
```

### Get Job Clips
```bash
curl http://localhost:8000/api/jobs/{job_id}/clips
```

### Render Clip
```bash
curl -X POST http://localhost:8000/api/clips/{clip_id}/render \
  -H "Content-Type: application/json" \
  -d '{"face_tracking": true, "captions": false}'
```

### Download Render
```bash
curl -O http://localhost:8000/api/renders/{render_id}/download
```

## Performance Considerations

### Processing Time Estimates (for 10-minute video):
- Download (YouTube): 30-60 seconds
- Normalize: 60-120 seconds
- Transcribe (base model): 60-180 seconds
- Generate Highlights: <5 seconds
- Create Thumbnails: <10 seconds
- **Total**: ~3-6 minutes

### Render Time (per clip, ~30 seconds):
- Simple crop: 10-20 seconds
- Face tracking: 60-120 seconds
- With captions: +10-20 seconds

### Optimization Tips:
1. Use smaller Whisper model (base) for faster transcription
2. Disable face tracking for non-talking-head content
3. Process multiple jobs in parallel (increase MAX_WORKERS)
4. Pre-normalize videos before uploading

## Deployment Notes

### System Requirements:
- Python 3.8+
- Node.js 18+
- FFmpeg (installed on system)
- ~2GB RAM minimum
- ~5GB disk space for models and processing

### Production Checklist:
- [ ] Configure MAX_WORKERS based on CPU cores
- [ ] Set up disk space monitoring for data/
- [ ] Configure logging rotation
- [ ] Add health check endpoints
- [ ] Implement cleanup for old jobs/renders
- [ ] Add authentication/authorization
- [ ] Rate limiting for API endpoints
- [ ] Setup HTTPS/SSL
- [ ] Configure CORS for production domain

## Troubleshooting

### Common Issues:

**"FFmpeg not found"**
- Install FFmpeg and add to system PATH
- Verify: `ffmpeg -version`

**"No module named 'faster_whisper'"**
- Activate virtual environment
- Run: `pip install -r requirements.txt`

**"Download failed"**
- Check internet connection
- Verify YouTube URL is valid
- yt-dlp may need update: `pip install -U yt-dlp`

**"Face tracking very slow"**
- Normal for first run (model download)
- Consider using GPU if available
- Use face tracking only for podcasts/interviews

**"Frontend can't connect to backend"**
- Ensure backend is running on port 8000
- Check CORS settings in app.py
- Verify API URL in frontend code
