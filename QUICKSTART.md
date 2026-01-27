# Quick Start Guide - Antariks Clipper

This guide will help you get Antariks Clipper up and running in 5 minutes.

## Prerequisites Check

Before starting, ensure you have:

1. **Python 3.8 or higher**
   ```bash
   python3 --version
   ```

2. **Node.js 18 or higher**
   ```bash
   node --version
   ```

3. **FFmpeg installed**
   ```bash
   ffmpeg -version
   ```

If FFmpeg is not installed:
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **Windows**: Download from https://ffmpeg.org/download.html and add to PATH

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/jivimuz/antariks-clipper.git
cd antariks-clipper
```

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: First time setup will download Whisper model (~150MB for base model). This is normal.

### 3. Setup Frontend

Open a new terminal window:

```bash
cd frontend

# Install dependencies
npm install
```

## Running the Application

You need two terminal windows/tabs:

### Terminal 1: Backend
```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uvicorn app:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

You should see:
```
  ▲ Next.js 16.1.5
  - Local:        http://localhost:3000
```

## Using the Application

1. **Open your browser** to http://localhost:3000

2. **Choose input method**:
   - **YouTube**: Click "YouTube URL" tab, paste a YouTube video URL
   - **Upload**: Click "Upload Video" tab, select a video file from your computer

3. **Generate highlights**: Click "Generate Highlights"

4. **View progress**: You'll be redirected to the job detail page where you can see:
   - Processing progress (0-100%)
   - Current step (acquire, normalize, transcribe, etc.)
   - Real-time updates every 2 seconds

5. **View clips**: Once processing is complete (status: ready), you'll see:
   - Grid of highlight clips with thumbnails
   - Duration and timestamp for each clip
   - Transcript snippet preview

6. **Render clips**: For each clip, choose:
   - **Render (Simple)**: Fast center crop, no face tracking
   - **Render (Face Tracking)**: Auto-reframe to follow active speaker (slower)
   - **Render (Captions)**: Burn in subtitles from transcript

7. **Download**: Once rendering is complete, click "Download" to get your vertical 9:16 video

## Example Workflow

### YouTube Video
```
1. Paste URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
2. Click "Generate Highlights"
3. Wait 3-5 minutes for processing
4. View 12 auto-generated highlight clips
5. Render your favorites with face tracking
6. Download and upload to Instagram Reels/TikTok
```

### Uploaded Video
```
1. Click "Upload Video" tab
2. Select your video file (MP4, AVI, MOV, etc.)
3. Click "Generate Highlights"
4. Wait 3-5 minutes for processing
5. View auto-generated clips
6. Render and download
```

## What Happens During Processing?

1. **Acquire (10-20%)**: Download or save video
2. **Normalize (20-40%)**: Convert to standard format (H.264/AAC)
3. **Transcribe (40-60%)**: Generate transcript using Whisper AI
4. **Generate Highlights (60-80%)**: Analyze transcript, score segments, select top clips
5. **Create Clips (80-100%)**: Generate thumbnails for each highlight

**Total time**: ~3-6 minutes for a 10-minute video

## Troubleshooting

### Backend won't start
**Error**: `ModuleNotFoundError: No module named 'fastapi'`
- **Solution**: Make sure virtual environment is activated and dependencies are installed:
  ```bash
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

### Frontend won't start
**Error**: `Cannot find module 'next'`
- **Solution**: Install dependencies:
  ```bash
  npm install
  ```

### "FFmpeg not found" error
- **Solution**: Install FFmpeg and make sure it's in your system PATH
- **Verify**: `ffmpeg -version` should work in terminal

### Processing stuck at "Transcribe"
- This is normal! Transcription can take 1-3 minutes for a 10-minute video
- Using the "base" Whisper model is fastest
- Consider upgrading to "small" or "medium" for better accuracy (but slower)

### Face tracking is very slow
- Face tracking requires processing every frame
- For a 30-second clip, expect 60-120 seconds rendering time
- Use simple render for faster results
- Face tracking works best for podcasts/interviews with talking heads

### Can't connect to backend
- Make sure backend is running on http://localhost:8000
- Check browser console for errors
- Verify CORS settings allow localhost:3000

## Tips for Best Results

### Input Video
- **Length**: 5-30 minutes works best (longer videos = more processing time)
- **Type**: Podcasts, interviews, tutorials, reviews work great
- **Audio**: Clear speech is essential for good transcription
- **Language**: Currently optimized for Indonesian and English

### Highlight Generation
- Automatically finds segments with hook keywords
- Prefers clips around 30-35 seconds (ideal for Reels/TikTok)
- Removes overlapping clips
- Scores based on keyword density and word variety

### Rendering Options
- **Simple**: Best for landscape videos, fast rendering
- **Face Tracking**: Best for podcasts/interviews, follows speaker
- **Captions**: Adds burned-in subtitles, good for silent viewing

## Next Steps

- **Customize**: Edit `backend/.env` to change clip count, duration, etc.
- **View all jobs**: Visit http://localhost:3000/jobs to see all your processing jobs
- **API docs**: Visit http://localhost:8000/docs for interactive API documentation
- **Architecture**: Read `ARCHITECTURE.md` for technical details

## Getting Help

- **Check logs**: Backend terminal shows detailed processing logs
- **API errors**: Backend returns detailed error messages
- **Frontend issues**: Check browser developer console (F12)
- **Issues**: Report bugs at https://github.com/jivimuz/antariks-clipper/issues

Enjoy creating viral clips! 🎬✨
