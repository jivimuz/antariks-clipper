# Antariks Clipper - Single Executable Architecture

## Visual Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ANTARIKS CLIPPER SINGLE EXE                           ║
║                          (AntariksClipper-1.0.0.exe)                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────┐
│                            BUILD PROCESS                                     │
└──────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────┐
  │ build-all.bat   │  ← User runs this
  └────────┬────────┘
           │
           ├── [1/3] BACKEND BUILD ────────────────────────────┐
           │                                                    │
           │   backend/build.bat                               │
           │   ↓                                                │
           │   PyInstaller + build-backend.spec                │
           │   ↓                                                │
           │   ✓ antariks-backend.exe                          │
           │   ✓ _internal/ (Python dependencies)             │
           │   └─> Output: backend/dist/antariks-backend/      │
           │                                                    │
           ├── [2/3] FRONTEND BUILD ──────────────────────────┤
           │                                                    │
           │   npm run build:frontend                          │
           │   ↓                                                │
           │   Next.js static export                           │
           │   ↓                                                │
           │   ✓ index.html, _next/, assets/                   │
           │   └─> Output: frontend/out/                       │
           │                                                    │
           └── [3/3] ELECTRON PACKAGE ────────────────────────┤
                                                                │
               npm run build:electron                          │
               ↓                                                │
               Electron Builder + NSIS                         │
               ↓                                                │
               ✓ AntariksClipper-1.0.0.exe (NSIS Installer)   │
               └─> Output: frontend/dist/                      │
                                                                │
                                                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                        INSTALLED APPLICATION                                 │
└──────────────────────────────────────────────────────────────────────────────┘

Installation Path: %LOCALAPPDATA%\Programs\antariks-clipper\

AntariksClipper.exe (Electron)
├── resources/
│   ├── app.asar                          ← ASAR archive (compressed)
│   │   ├── out/                          ← Next.js static HTML/CSS/JS
│   │   │   ├── index.html
│   │   │   ├── _next/
│   │   │   └── assets/
│   │   ├── electron/                     ← Electron main process
│   │   │   ├── main.js
│   │   │   ├── backend-launcher.js
│   │   │   └── preload.js
│   │   ├── node_modules/                 ← Node dependencies
│   │   └── package.json
│   │
│   └── backend/                          ← Backend executable bundle
│       ├── antariks-backend.exe          ← PyInstaller exe
│       └── _internal/                    ← Python dependencies
│           ├── python310.dll
│           ├── fastapi/
│           ├── whisper/
│           ├── cv2/
│           └── ... (all Python deps)
│
├── AntariksClipper.exe                   ← Main Electron executable
├── ffmpeg.dll, libGLESv2.dll, ...        ← Electron dependencies
└── ... (other Electron runtime files)

┌──────────────────────────────────────────────────────────────────────────────┐
│                           RUNTIME FLOW                                       │
└──────────────────────────────────────────────────────────────────────────────┘

User: Double-clicks AntariksClipper.exe
  │
  ▼
┌─────────────────────────────────────────┐
│  ELECTRON MAIN PROCESS                  │
│  (electron/main.js)                     │
└─────────────────────────────────────────┘
  │
  ├── 1. Initialize Electron
  │   └─> Create app instance
  │
  ├── 2. Start Backend ─────────────────────────────┐
  │   │                                              │
  │   └─> BackendLauncher.start()                   │
  │       ├─ Detect production mode                 │
  │       ├─ Get backend path:                      │
  │       │  resources/backend/antariks-backend.exe │
  │       ├─ Spawn backend process                  │
  │       └─ Wait for health check                  │
  │           │                                      │
  │           └─> GET http://127.0.0.1:8000/health  │
  │               ├─ Retry 30 times (1s interval)   │
  │               └─ ✓ Backend ready!               │
  │                                                  │
  ├── 3. Create Window ──────────────────────────────┤
  │   │                                              │
  │   └─> BrowserWindow                             │
  │       ├─ Size: 1280x800                         │
  │       ├─ Load: file:///.../out/index.html       │
  │       └─ Show when ready                        │
  │                                                  │
  └── 4. Application Running ───────────────────────┘
       │
       ├─> Frontend (React/Next.js)
       │   ├─ Load static HTML from app.asar
       │   ├─ Execute JavaScript
       │   └─> Make API calls
       │       │
       │       └─> http://127.0.0.1:8000/api/*
       │           │
       │           ▼
       └─> Backend (FastAPI)
           ├─ Listen on 127.0.0.1:8000
           ├─ Process video uploads
           ├─ Run Whisper transcription
           ├─ Generate clips
           ├─ Render videos
           └─> Return responses to frontend

┌──────────────────────────────────────────────────────────────────────────────┐
│                          SHUTDOWN FLOW                                       │
└──────────────────────────────────────────────────────────────────────────────┘

User: Closes window
  │
  ▼
Electron: 'before-quit' event
  │
  ├─> BackendLauncher.stop()
  │   ├─ Send SIGTERM to backend process
  │   └─> Backend receives signal
  │       ├─ Signal handler catches SIGTERM
  │       ├─ Cleanup resources
  │       └─ Exit gracefully (code 0)
  │
  └─> app.exit(0)
      ├─ Close all windows
      ├─ Terminate Electron
      └─ ✓ No zombie processes!

┌──────────────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW DIAGRAM                                     │
└──────────────────────────────────────────────────────────────────────────────┘

   USER ACTIONS                    FRONTEND                      BACKEND
   ────────────                    ────────                      ───────
        │                              │                             │
   [Upload Video] ────────────────> [Upload Form]                   │
        │                              │                             │
        │                              └──> POST /api/jobs           │
        │                              │    (multipart/form-data)    │
        │                              │                             │
        │                              │  <────────────────────────  │
        │                              │    {job_id: "...", status}  │
        │                              │                             │
        │                         [Job Status]                       │
        │                              │                             │
        │                              └──> GET /api/jobs/{id}       │
        │                              │                             │
        │                              │  <────────────────────────  │
        │                              │    {status: "processing"}   │
        │                              │                             │
        │                         [Polling...]                       │
        │                              │                             │
        │                              │  ┌───────────────────────┐ │
        │                              │  │ Backend Processing:   │ │
        │                              │  │ - Transcription       │ │
        │                              │  │ - Highlight detection │ │
        │                              │  │ - Clip generation     │ │
        │                              │  └───────────────────────┘ │
        │                              │                             │
        │                              └──> GET /api/jobs/{id}       │
        │                              │                             │
        │                              │  <────────────────────────  │
        │                              │    {status: "ready"}        │
        │                              │                             │
        │                         [Show Clips]                       │
        │                              │                             │
   [Render Clip] ─────────────────> [Render Button]                 │
        │                              │                             │
        │                              └──> POST /api/clips/{id}/render
        │                              │    {face_tracking: true}    │
        │                              │                             │
        │                              │  ┌───────────────────────┐ │
        │                              │  │ FFmpeg Processing:    │ │
        │                              │  │ - Crop to 9:16        │ │
        │                              │  │ - Face tracking       │ │
        │                              │  │ - Export MP4          │ │
        │                              │  └───────────────────────┘ │
        │                              │                             │
        │                              │  <────────────────────────  │
        │                              │    {render_id: "...", ...}  │
        │                              │                             │
   [Download] ──────────────────────> [Download Link]               │
        │                              │                             │
        │                              └──> GET /api/renders/{id}/download
        │                              │                             │
        │                              │  <────────────────────────  │
        │   ┌────────────────────────  │    (video/mp4 stream)       │
        │   │                          │                             │
        ▼   ▼                          │                             │
   [Video Saved]                      │                             │

┌──────────────────────────────────────────────────────────────────────────────┐
│                        SECURITY ARCHITECTURE                                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND (Sandboxed)                                                       │
│  ├─ nodeIntegration: false        ← No direct Node.js access               │
│  ├─ contextIsolation: true        ← Isolated context                       │
│  ├─ sandbox: true                 ← Browser sandbox                        │
│  └─> Can only access backend via HTTP API                                  │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           │ HTTP Requests (CORS allowed)
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BACKEND (Localhost Only)                                                   │
│  ├─ Bind: 127.0.0.1:8000          ← Not exposed to network                │
│  ├─ CORS: Allow all origins       ← Desktop app (safe)                    │
│  └─> Only accessible from same machine                                     │
└─────────────────────────────────────────────────────────────────────────────┘
           │
           │ File System Access
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FILE SYSTEM                                                                │
│  ├─ User Videos: %LOCALAPPDATA%\AntariksClipper\data\                     │
│  ├─ Temp Files: System temp directory                                     │
│  └─> All files local, no cloud uploads                                     │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                            END OF ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════
```

## Key Design Principles

1. **Single Executable**: Everything embedded in one NSIS installer
2. **Zero Dependencies**: No Python or Node.js required on target machine
3. **Auto Lifecycle**: Backend starts and stops automatically
4. **Local Processing**: No data sent to external servers
5. **Desktop Security**: Electron sandbox + localhost-only backend
6. **Clean Shutdown**: Proper signal handling prevents zombie processes
7. **Professional UX**: One-click installer with shortcuts
8. **Static Frontend**: Fast loading, no server required
9. **Embedded Backend**: PyInstaller bundle as Electron resource
10. **Single Instance**: Lock prevents multiple app instances

## File Size Breakdown

```
Total: ~500-800 MB
├─ Electron Runtime: ~150 MB
├─ Python Backend: ~200-400 MB
│  ├─ Python interpreter: ~30 MB
│  ├─ FastAPI + deps: ~50 MB
│  ├─ Whisper models: ~150 MB (downloaded on first run)
│  ├─ OpenCV + MediaPipe: ~100 MB
│  └─ Other deps: ~50 MB
└─ Frontend Assets: ~50 MB
```

## Technologies Used

- **Electron 28** - Desktop app framework
- **Next.js 16** - Static HTML generation
- **PyInstaller 6** - Python bundling
- **FastAPI** - Backend API
- **Whisper AI** - Transcription
- **FFmpeg** - Video processing
- **NSIS** - Windows installer

---

*Visual architecture diagram for Antariks Clipper single executable implementation*
