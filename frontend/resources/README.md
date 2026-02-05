# FFmpeg Binaries

This directory should contain FFmpeg binaries for Windows distribution.

## Windows
Download FFmpeg portable from:
- https://www.gyan.dev/ffmpeg/builds/
- Get the "essentials" build
- Extract and place these files here:
  - ffmpeg.exe
  - ffprobe.exe

## macOS and Linux
FFmpeg should be installed on the system. The application will use the system FFmpeg.

## Note
FFmpeg is required for video processing. The backend uses FFmpeg via subprocess calls.
In production, the backend should detect and use:
1. Bundled FFmpeg (Windows in resources directory)
2. System FFmpeg (macOS/Linux)
