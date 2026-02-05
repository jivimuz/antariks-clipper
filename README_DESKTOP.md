# Antariks Clipper - Desktop Application

**One-Click Install. Zero Setup. Start Creating Viral Clips!**

## 🚀 Download & Run

1. **Download** latest release: [`AntariksClipper-1.0.0.exe`](https://github.com/jivimuz/antariks-clipper/releases)
2. **Double-click** to install (one-click installer)
3. **Launch** from desktop shortcut
4. **That's it!** No Python, Node.js, or manual setup needed.

## 💻 System Requirements

- **Windows 10/11** (64-bit)
- **8GB RAM** minimum (16GB recommended)
- **2GB free disk space** (for app + temporary files)
- **Internet connection** (for YouTube download & model downloads)

## ⚡ Features

Transform long-form videos into viral short-form content automatically:

### 🎬 Video Processing
- ✅ **YouTube Download** - Paste URL, auto-download and process
- ✅ **Local Upload** - Support for MP4, MOV, AVI, MKV
- ✅ **AI Transcription** - Whisper-powered accurate transcription
- ✅ **Smart Highlights** - Automatic viral moment detection

### 🎯 Clip Generation
- ✅ **Auto-Generate Clips** - AI selects best moments (15-60 seconds)
- ✅ **Face Tracking** - Smart cropping keeps faces centered
- ✅ **9:16 Vertical Format** - Perfect for TikTok, Reels, Shorts
- ✅ **Manual Selection** - Create custom clips from timeline

### 🎨 Advanced Features
- ✅ **Preview Before Render** - See exactly what you'll get
- ✅ **Batch Rendering** - Process multiple clips at once
- ✅ **Caption Generation** - AI-powered engaging captions
- ✅ **Hashtag Suggestions** - Optimized for each platform
- ✅ **Smart Captions** - Animated text overlays (coming soon)

## 📖 Quick Start Guide

### 1. First Launch

When you first run Antariks Clipper:
- App initializes (10-30 seconds)
- Whisper AI model downloads (~150MB) - **one-time only**
- Backend starts automatically in background
- You're ready to go!

### 2. Process a YouTube Video

1. **Copy YouTube URL**
   - Any public YouTube video
   - Paste into input field

2. **Click "Process Video"**
   - Video downloads automatically
   - Transcription runs with AI
   - Highlights extracted automatically

3. **Review Generated Clips**
   - Preview each clip
   - See transcripts
   - Check face tracking

4. **Render & Download**
   - Select clips to render
   - Click "Render Selected"
   - Download finished clips

### 3. Upload Local Video

1. **Click "Upload File"**
   - Choose video from computer
   - Supports: MP4, MOV, AVI, MKV

2. **Processing Starts**
   - Transcription
   - Highlight detection
   - Clip generation

3. **Edit & Render**
   - Same as YouTube workflow
   - Full control over output

## 🎯 Use Cases

### Content Creators
- Turn podcast episodes into viral clips
- Extract best moments from livestreams
- Repurpose long YouTube videos

### Social Media Managers
- Create content for TikTok, Instagram, YouTube Shorts
- Generate multiple clips from one video
- A/B test different moments

### Agencies & Teams
- Fast turnaround for clients
- Batch process multiple videos
- Consistent vertical video output

## ⚙️ Settings & Configuration

### License Activation

Antariks Clipper requires a valid license:
1. Purchase at [https://antariks.id](https://antariks.id)
2. Enter license key in app
3. Unlimited processing

### FFmpeg Requirement

**Important**: FFmpeg must be installed for video processing:

**Option 1 - Automatic (Recommended)**:
- App will guide you on first launch
- Download link provided

**Option 2 - Manual**:
1. Download: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg\`
3. Add to PATH: `C:\ffmpeg\bin`

### Storage Location

Videos and clips are stored in:
```
%LOCALAPPDATA%\AntariksClipper\data\
```

To change storage location, edit backend configuration.

## 🔧 Troubleshooting

### App Won't Start

**Solution**: Check if port 8000 is available
```
netstat -ano | findstr :8000
```
If in use, close the conflicting app.

### Video Processing Fails

**Causes**:
- FFmpeg not installed
- Insufficient disk space
- Corrupted video file

**Solutions**:
1. Install FFmpeg (see above)
2. Free up disk space (need 2x video size)
3. Try different video

### Slow Processing

**Tips**:
- Processing time: ~1-2 minutes per 10 minutes of video
- Transcription is CPU-intensive
- Close other heavy apps
- Consider shorter videos for testing

### Backend Not Responding

**Symptoms**: API errors, loading forever

**Solutions**:
1. Restart the app
2. Check Windows Firewall (allow `antariks-backend.exe`)
3. Check antivirus (may block backend)

### Downloads Fail

**Symptoms**: YouTube download errors

**Solutions**:
1. Check internet connection
2. Verify video is public
3. Try different video
4. Check if age-restricted

## 📊 Performance Tips

### For Best Results:
- ✅ Close unnecessary apps
- ✅ Use SSD for storage location
- ✅ Videos under 2 hours work best
- ✅ Good audio quality = better transcription
- ✅ Clear speech = better highlights

### Expected Processing Times:
- **10-minute video**: ~2-3 minutes
- **30-minute video**: ~6-8 minutes
- **1-hour video**: ~12-15 minutes
- **Rendering 1 clip**: ~30-60 seconds

## 🔒 Privacy & Security

- ✅ **100% Local Processing** - No data sent to external servers
- ✅ **No Tracking** - No telemetry or analytics
- ✅ **Secure** - All processing happens on your machine
- ✅ **Your Data** - Videos stored locally, you control everything

## 🆘 Support

### Documentation
- [Build Guide](DESKTOP_BUILD_SINGLE_EXE.md) - For developers
- [GitHub](https://github.com/jivimuz/antariks-clipper) - Source code & issues

### Get Help
- **GitHub Issues**: [Report bugs](https://github.com/jivimuz/antariks-clipper/issues)
- **Email**: support@antariks.id
- **Website**: [https://antariks.id](https://antariks.id)

### Common Questions

**Q: Do I need Python or Node.js installed?**
A: No! Everything is bundled in the installer.

**Q: Can I use this offline?**
A: Yes, after initial model download. YouTube download requires internet.

**Q: How many clips can I generate?**
A: Unlimited with valid license.

**Q: What video formats are supported?**
A: MP4, MOV, AVI, MKV, and most common formats.

**Q: Can I customize clip length?**
A: Yes, manually select any portion of the video.

**Q: Is this a one-time purchase?**
A: Check [https://antariks.id](https://antariks.id) for pricing details.

## 📝 Updates

The app checks for updates automatically. When a new version is available:
1. Notification appears
2. Click to download
3. Installer updates automatically
4. Your settings and data are preserved

## 📄 License

Requires valid license key from [https://antariks.id](https://antariks.id)

Software provided as-is. See LICENSE file for details.

---

**Made with ❤️ by Antariks Team**

Transform your content. Go viral. Start today!

[Download Now](https://github.com/jivimuz/antariks-clipper/releases) | [Visit Website](https://antariks.id)
