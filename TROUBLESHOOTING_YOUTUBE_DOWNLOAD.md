# Troubleshooting Guide: YouTube Download Issues

## Overview
This guide helps diagnose and fix common issues with YouTube video downloads in Antariks Clipper.

## Quick Diagnostics

### 1. Check Dependencies
```bash
cd backend
python3 -c "from services.downloader import check_dependencies; ok, missing, versions = check_dependencies(); print(f'OK: {ok}, Missing: {missing}, Versions: {versions}')"
```

### 2. Check yt-dlp Version
```bash
yt-dlp --version
# Should be 2026.1.31 or newer
```

### 3. Update yt-dlp
```bash
pip install --upgrade yt-dlp
# or
pip3 install --upgrade --user yt-dlp
```

## Common Issues and Solutions

### Issue 1: "The downloaded file is empty (0 bytes)"

**Possible Causes:**
1. **Network interruption** - Download was interrupted
2. **Region restriction** - Video blocked in your country
3. **DRM protection** - Video has Digital Rights Management
4. **API quota exceeded** - YouTube API rate limit hit
5. **Format unavailable** - No suitable video format available
6. **Bot detection** - YouTube detected automated access

**Solutions:**
1. **Check video availability manually** in your browser
2. **Update yt-dlp**: `pip install --upgrade yt-dlp`
3. **Try with cookies** (for age-restricted/member-only content):
   ```bash
   # Export cookies from browser using a browser extension
   # Then use: --cookies cookies.txt
   ```
4. **Wait and retry** - If rate limited, wait 5-10 minutes
5. **Check logs** - Look for specific error messages in console
6. **Try different video** - Verify the issue is with this specific video

### Issue 2: "HTTP 403 Forbidden"

**Possible Causes:**
- Region restrictions
- Age restrictions
- Temporary YouTube blocks
- Bot detection
- IP-based restrictions

**Solutions:**
1. **Update yt-dlp immediately**: `pip install --upgrade yt-dlp`
2. **Use cookies for authentication**:
   - Install browser extension: "Get cookies.txt LOCALLY"
   - Export YouTube cookies to `cookies.txt`
   - Provide cookies file to downloader
3. **Try different player client** - The fallback methods will try this automatically
4. **Wait 10-30 minutes** - May be temporary rate limiting
5. **Use VPN** if region-blocked

### Issue 3: "HTTP 429 Too Many Requests"

**Cause:** YouTube API rate limiting / quota exceeded

**Solutions:**
1. **Wait 5-10 minutes** before retrying
2. **Reduce concurrent downloads** - Don't run multiple downloads simultaneously
3. **Update yt-dlp**: `pip install --upgrade yt-dlp`
4. **Use cookies** for higher quotas (authenticated users get better limits)

### Issue 4: "Video is region-blocked"

**Cause:** Content not available in your country

**Solutions:**
1. **Use VPN** to access from different region
2. **Check if video is available** in your browser
3. **No technical workaround** - This is YouTube's restriction

### Issue 5: "Video is DRM-protected"

**Cause:** Video has Digital Rights Management (cannot be downloaded)

**Solutions:**
- **No solution** - DRM-protected content (movies, premium content) cannot be legally downloaded
- Verify in browser if video has a lock icon or premium badge

### Issue 6: "Age-restricted content"

**Cause:** Video requires sign-in to confirm age

**Solutions:**
1. **Use cookies from authenticated browser session**:
   ```bash
   # Export cookies from browser while logged into YouTube
   # Save to cookies.txt
   # Use --cookies option
   ```
2. **Update yt-dlp**: Newer versions handle this better

### Issue 7: "Live streams cannot be downloaded"

**Cause:** Attempting to download ongoing live stream

**Solutions:**
1. **Wait for stream to end** - Live streams can only be downloaded after they finish
2. **Check if archived** - Some streams become available as VODs after ending

### Issue 8: "Duration mismatch / Incomplete download"

**Cause:** Download stopped before completion or file corrupted

**Solutions:**
1. **Check network stability**
2. **Increase timeout** - For very long videos (3+ hours)
3. **Check available disk space**
4. **Retry download** - May have been temporary network issue

## Detailed Error Messages

The downloader now provides detailed error messages with specific causes:

### Empty File Error
```
Downloaded file is empty (0 bytes). 
Possible causes:
1. Network interruption during download
2. Region restriction or DRM protection
3. YouTube API quota exceeded
4. Invalid video format or stream unavailable
```

### Validation Errors
- **"File too small"** - Incomplete download or corrupted file
- **"No video stream"** - File corrupted or not a valid video
- **"Duration mismatch"** - File incomplete or partially downloaded

## Testing Specific Video

To test with the specific video mentioned in the issue (https://www.youtube.com/watch?v=NEcbdGkJgcA):

```bash
cd backend
source .venv/bin/activate  # If using virtual environment
python test_youtube_download.py
```

This will:
1. Check dependencies
2. Fetch video information
3. Download the video
4. Validate the downloaded file
5. Report results with timing

## Advanced Debugging

### Enable Verbose Logging

Edit `backend/services/downloader.py` and set logging level:
```python
logger.setLevel(logging.DEBUG)
```

### Manual Download Test

```bash
# Test yt-dlp directly
yt-dlp -v \
  -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best' \
  --merge-output-format mp4 \
  -o '/tmp/test_video.%(ext)s' \
  'https://www.youtube.com/watch?v=NEcbdGkJgcA'
```

### Check Video Info

```bash
yt-dlp --dump-json --no-download 'https://www.youtube.com/watch?v=VIDEO_ID' | python -m json.tool
```

### Test with Different Player Clients

```bash
# Android client
yt-dlp --extractor-args 'youtube:player_client=android' URL

# iOS client
yt-dlp --extractor-args 'youtube:player_client=ios' URL

# TV client
yt-dlp --extractor-args 'youtube:player_client=tv' URL
```

## Fallback Strategies

The downloader automatically tries multiple fallback strategies if the main download fails:

1. **Android client** with best format
2. **iOS client** with standard quality (720p)
3. **Web embedded client**
4. **Android embedded client**
5. **TV client** (smart TV interface)
6. **Mobile web** with lower quality
7. **Generic best available** (no client preference)

Each strategy is tried sequentially until one succeeds.

## System Requirements

### Minimum Requirements
- Python 3.8+
- ffmpeg (system-wide installation)
- yt-dlp (latest version)
- 1GB RAM minimum
- 10GB free disk space (for processing)

### Recommended Requirements
- Python 3.10+
- ffmpeg 4.4+
- yt-dlp 2026.1.31+
- 4GB RAM
- 50GB free disk space

### Disk Space for Long Videos

| Video Duration | Estimated Size | Processing Space |
|---------------|----------------|------------------|
| 1 hour        | ~500MB-1GB     | 2-3GB           |
| 3 hours       | ~1.5-3GB       | 6-9GB           |
| 6 hours       | ~3-6GB         | 12-18GB         |

## Network Requirements

- **Stable internet connection** required
- **Download speed**: Minimum 5 Mbps recommended
- **Latency**: Lower is better (< 100ms ideal)
- **No proxy/VPN issues**: Some VPNs may be blocked by YouTube

## FAQ

### Q: Why does my download keep failing after 50%?
**A:** This could be:
- Network instability - Check your connection
- Disk space - Ensure you have enough free space
- YouTube throttling - Wait and retry later

### Q: Can I download 4K videos?
**A:** Yes, if available. The downloader will try to get the best quality available.

### Q: How long should a download take?
**A:** Depends on:
- Video length
- Video quality
- Internet speed
- Server load

Typical times:
- 5 min video: 30s - 2 min
- 1 hour video: 5-15 min
- 3+ hour video: 20-60 min

### Q: Why are some videos not downloadable?
**A:** Some videos cannot be downloaded due to:
- DRM protection (movies, premium content)
- Region restrictions
- Age restrictions without authentication
- Private/unlisted videos you don't have access to
- Content removed or made unavailable

### Q: How do I use cookies for authentication?
**A:**
1. Install browser extension: "Get cookies.txt LOCALLY" (Chrome/Firefox)
2. Visit YouTube and log in
3. Use extension to export cookies to `cookies.txt`
4. Provide path to cookies file in download options
5. Keep cookies file secure (it contains authentication tokens)

## Getting Help

If issues persist after trying these solutions:

1. **Check logs** - Look at console output for specific errors
2. **Update everything**:
   ```bash
   pip install --upgrade yt-dlp
   sudo apt-get update && sudo apt-get upgrade ffmpeg  # Linux
   brew upgrade ffmpeg  # macOS
   ```
3. **Test with different video** - Verify if issue is video-specific
4. **Check YouTube status** - Sometimes YouTube itself has issues
5. **Review error messages** - The enhanced error messages now provide specific causes

## References

- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp#readme)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [YouTube API Status](https://www.google.com/appsstatus/dashboard/)

## Recent Enhancements

### January 2026 Updates
- ✅ Enhanced error detection (DRM, quota, bot detection)
- ✅ 7 fallback download strategies
- ✅ Pre-download diagnostics
- ✅ Enhanced file validation with duration checking
- ✅ Detailed logging with specific error causes
- ✅ Updated to yt-dlp 2026.1.31
