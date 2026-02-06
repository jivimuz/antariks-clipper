# Antariks Clipper - Backend

Backend API untuk Antariks Clipper menggunakan FastAPI.

## Requirements

- Python 3.8+
- FFmpeg (harus diinstall di sistem)
- JavaScript Runtime untuk YouTube download (pilih salah satu):
  - Deno (recommended): https://deno.land/
  - Node.js: https://nodejs.org/

## Installation

1. Install FFmpeg:
   - **Windows**: Download dari https://ffmpeg.org/download.html dan tambahkan ke PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg` atau `sudo yum install ffmpeg`

2. Create virtual environment:

```bash
python -m venv .venv
```

3. Activate virtual environment:
   - **Windows**: `.venv\Scripts\activate`
   - **macOS/Linux**: `source .venv/bin/activate`

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. (Optional) Copy `.env.example` to `.env` and configure if needed

## Running

```bash
uvicorn app:app --reload --port 3211
```

API akan tersedia di http://localhost:3211

## API Documentation

Setelah server berjalan, buka:

- Swagger UI: http://localhost:3211/docs
- ReDoc: http://localhost:3211/redoc

## Endpoints

### Jobs

- `POST /api/jobs` - Create job (YouTube or upload)
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{job_id}` - Get job details
- `GET /api/jobs/{job_id}/clips` - Get job clips

### Clips & Renders

- `POST /api/clips/{clip_id}/render` - Create render
- `GET /api/renders/{render_id}` - Get render status
- `GET /api/renders/{render_id}/download` - Download rendered video
- `GET /api/thumbnails/{clip_id}` - Get clip thumbnail

## Data Storage

All data is stored in `backend/data/`:

- `raw/` - Downloaded/uploaded videos
- `normalized/` - Normalized videos
- `transcripts/` - Transcription JSON files
- `thumbnails/` - Clip thumbnails
- `renders/` - Rendered vertical videos
- `clipper.db` - SQLite database

## Notes

- First run will download Whisper model (~150MB for base model)
- Processing is done in background using ThreadPoolExecutor
- No external job queue required (Redis, Celery, etc.)
