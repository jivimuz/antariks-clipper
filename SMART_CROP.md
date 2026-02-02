# Smart Face Tracking Cropping System

This feature implements intelligent cropping for vertical 9:16 videos based on the number of people detected and who is speaking.

## Features

### Three Automatic Cropping Modes

#### 1. SOLO Mode (1 Person)
- Automatically activated when **1 face** is detected
- Crop follows the person's face with smooth tracking
- Uses Exponential Moving Average (EMA) for stable camera movement
- Output: Full 1080x1920 frame with face centered

```
┌─────────────┐
│             │
│    ┌───┐    │
│    │ 😊│    │
│    └───┘    │
│             │
│             │
└─────────────┘
```

#### 2. DUO SWITCH Mode (2 People, Taking Turns)
- Automatically activated when **2 faces** are detected and only one is speaking
- Instantly switches crop to whoever is currently speaking
- Uses faster EMA for more responsive switching
- No slide transitions - instant cut to active speaker
- Output: Full 1080x1920 frame focused on speaker

```
A speaking:           B speaking:
┌─────────────┐      ┌─────────────┐
│   bla bla   │      │   bla bla   │
│    ┌───┐    │      │    ┌───┐    │
│    │ A │    │  →   │    │ B │    │
│    └───┘    │      │    └───┘    │
│             │      │             │
└─────────────┘      └─────────────┘
```

#### 3. DUO SPLIT Mode (2 People, Both Speaking)
- Automatically activated when **2 faces** are detected and both are speaking simultaneously
- Vertical split screen (top-bottom layout)
- Each person cropped to their face in their respective half
- Smooth independent tracking for each half
- Output: 1080x1920 frame with two 1080x960 sections

```
┌─────────────┐
│   bla bla   │
│    ┌───┐    │
│    │ A │    │
│    └───┘    │
├─────────────┤
│   bla bla   │
│    ┌───┐    │
│    │ B │    │
│    └───┘    │
└─────────────┘
```

## How It Works

### Speaker Detection
- Uses MediaPipe Face Mesh to detect mouth landmarks
- Tracks mouth openness over time (10-frame window)
- Calculates variance of mouth movement
- High variance = speaking, low variance = not speaking
- Threshold: 5.0 (configurable)

### Mode Determination
```python
if num_faces <= 1:
    mode = "solo"
elif num_speakers >= 2 and simultaneous for 3+ frames:
    mode = "duo_split"
else:
    mode = "duo_switch"
```

### Smooth Tracking
- **SOLO Mode**: EMA alpha = 0.2 (very smooth)
- **DUO SWITCH Mode**: EMA alpha = 0.4 (more responsive)
- **DUO SPLIT Mode**: EMA alpha = 0.2 per person (smooth)

## Usage

### Frontend
1. Open a job detail page
2. Enable the **Smart Crop** toggle (purple button with Users icon)
3. Select clips to render
4. Click "Render" button

### Backend API

#### Render Single Clip
```bash
POST /api/clips/{clip_id}/render
{
  "face_tracking": false,
  "smart_crop": true,
  "captions": false,
  "watermark_text": ""
}
```

#### Render Multiple Clips
```bash
POST /api/jobs/{job_id}/render-selected?clip_ids=id1,id2,id3
{
  "face_tracking": false,
  "smart_crop": true,
  "captions": false,
  "watermark_text": ""
}
```

### Python API
```python
from services.reframe import reframe_video_smart
from pathlib import Path

success = reframe_video_smart(
    input_path=Path("input.mp4"),
    output_path=Path("output.mp4"),
    output_width=1080,
    output_height=1920,
    start_sec=0,
    duration=30
)
```

## Technical Details

### Dependencies
- **MediaPipe**: Face detection and landmark tracking
- **OpenCV**: Video processing and frame manipulation
- **NumPy**: Numerical operations for variance calculation

### New Modules
- `backend/services/speaker_detect.py`: Speaker detection logic
- `backend/services/smart_crop.py`: Smart cropping implementation
- `backend/services/face_track.py`: Enhanced with multi-face mouth tracking

### Performance
- Face detection runs every 2 frames (configurable via `FACE_DETECTION_INTERVAL`)
- Efficient face tracking using IOU-based matching
- Proximity-based landmark-to-face matching

## Configuration

### Backend Config (`backend/config.py`)
```python
FACE_DETECTION_INTERVAL = 2  # Process every N frames
EMA_ALPHA = 0.2  # Smoothing for center tracking
```

### Speaker Detection Parameters
```python
speaking_threshold = 5.0  # Minimum variance to be "speaking"
history_window = 10  # Frames to track for variance
simultaneous_threshold = 3  # Frames to confirm simultaneous speaking
```

## Limitations

- Works best with 1-2 people in frame
- For 3+ people, uses the 2 largest faces
- Requires good lighting for accurate face detection
- Speaking detection based on visual mouth movement only (no audio analysis)

## Future Enhancements

- Audio-based speaking detection for more accuracy
- Support for 3+ people with grid layouts
- Configurable speaking threshold via UI
- Preview of detected mode before rendering
- Custom layout preferences per user
