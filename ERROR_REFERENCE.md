# Error Reference Guide

This document provides a comprehensive reference for all error messages you might encounter in Antariks Clipper, along with their causes and solutions.

## YouTube Download Errors

### Video Availability Errors

#### "Video is unavailable or has been removed"
**Cause:** The video no longer exists, has been deleted, or made private by the uploader.

**Solutions:**
- Verify the URL is correct
- Check if the video is accessible in your browser
- Try a different video
- Contact the video owner if it was made private

#### "Video is private and cannot be accessed"
**Cause:** The video owner has set it to private, requiring specific permission to view.

**Solutions:**
- Request access from the video owner
- Use a different, public video
- If you have access, export cookies from your browser and provide a cookies.txt file

### Access Restriction Errors

#### "Video is blocked in your region"
**Cause:** The video has geographical restrictions and is not available in your location.

**Solutions:**
- Use a VPN to access from a different region
- Try a different video
- Contact the uploader about region restrictions

#### "Video is age-restricted and requires authentication"
**Cause:** The video requires YouTube sign-in to verify age.

**Solutions:**
1. Export cookies from your browser:
   - Install browser extension "Get cookies.txt"
   - Log in to YouTube
   - Export cookies to cookies.txt
   - Place file in backend directory
2. The system will automatically use cookies for authentication
3. Try a non-age-restricted video

#### "Video contains copyrighted content and cannot be downloaded"
**Cause:** The video has been flagged for copyright violations.

**Solutions:**
- This cannot be bypassed
- Use a different video
- Contact the original uploader

### Network and Server Errors

#### "Access forbidden" or "HTTP Error 403"
**Cause:** Multiple possible causes:
- Outdated yt-dlp version
- YouTube API changes
- Missing JavaScript runtime
- Temporary IP blocking

**Solutions:**
1. Update yt-dlp:
   ```bash
   pip install --upgrade yt-dlp
   ```

2. Install a JavaScript runtime (Node.js or Deno)

3. Wait 10-15 minutes if rate-limited

4. Restart the backend server

5. Check the logs for specific error details

#### "HTTP Error 404"
**Cause:** Video not found at the specified URL.

**Solutions:**
- Verify the URL is correct
- The video may have been deleted
- Check for typos in the URL

#### "Too many requests" or "HTTP Error 429"
**Cause:** YouTube rate limiting due to too many requests from your IP.

**Solutions:**
- Wait 10-15 minutes before retrying
- Reduce the frequency of requests
- If persistent, your IP may be temporarily blocked for several hours

#### "Network error occurred. Please check your connection"
**Cause:** Network connectivity issues.

**Solutions:**
- Check your internet connection
- Verify DNS is working
- Try accessing youtube.com in a browser
- Check firewall settings
- The system will automatically retry

#### "Download timed out"
**Cause:** The download took too long, possibly due to slow connection or large file.

**Solutions:**
- Check your internet speed
- Try a shorter video first
- The system will automatically retry with exponential backoff
- Check if YouTube servers are having issues

### Format and Compatibility Errors

#### "Video format is not supported"
**Cause:** The video format cannot be processed or downloaded.

**Solutions:**
- Update yt-dlp to the latest version
- Check if ffmpeg is installed and up to date
- Try a different video
- Report the issue with the video URL

#### "Live streams cannot be downloaded yet"
**Cause:** The video is currently a live stream.

**Solutions:**
- Wait until the stream ends and becomes a regular video
- YouTube usually makes streams available as videos after they end

### System Errors

#### "Missing dependencies: ffmpeg, yt-dlp"
**Cause:** Required system dependencies are not installed.

**Solutions:**
```bash
# Install ffmpeg
# Ubuntu/Debian:
sudo apt-get install -y ffmpeg

# macOS:
brew install ffmpeg

# Install yt-dlp
pip install yt-dlp
```

#### "Download completed but output file not found"
**Cause:** Download succeeded but file was not created where expected.

**Solutions:**
- Check disk space
- Verify write permissions on data directory
- Check the logs for file system errors
- Ensure the path is correct

## Job Processing Errors

### Transcription Errors

#### "Transcription failed - video may not have audio or audio format is not supported"
**Cause:** The video has no audio track or the audio format is incompatible.

**Solutions:**
- Verify the video has audio
- Play the video locally to confirm audio works
- Check audio codec compatibility
- Try re-encoding the video with standard audio (AAC)

#### "No transcript data found - transcription may have failed"
**Cause:** Transcription completed but produced no usable data.

**Solutions:**
- Check if the video has clear, audible speech
- Ensure sufficient audio volume
- Try a video with clearer audio
- Check Whisper model is downloaded correctly

### Highlight Generation Errors

#### "No highlights generated - video may not have enough spoken content"
**Cause:** The transcript didn't contain enough speech for highlight generation.

**Solutions:**
- Ensure video has at least 30 seconds of speech
- Check that speech is clear and detectable
- Avoid music-only or silent videos
- Try a video with more dialogue

### File System Errors

#### "Upload file not found or path not set"
**Cause:** The uploaded video file is missing or the path is incorrect.

**Solutions:**
- Re-upload the video
- Check disk space
- Verify file wasn't deleted or moved
- Check file permissions

#### "Raw video file not found"
**Cause:** The source video file is no longer available.

**Solutions:**
- The file may have been cleaned up after processing
- Re-process the job from the beginning
- Check if disk cleanup ran unexpectedly

## Render Errors

### Render Processing Errors

#### "Render failed - check logs for details"
**Cause:** Generic render failure, specific cause in logs.

**Solutions:**
- Check backend logs for FFmpeg errors
- Verify source video is still available
- Try with simpler render options (no face tracking/smart crop)
- Check disk space
- Ensure ffmpeg is properly installed

#### "Render completed but output file not found"
**Cause:** Render process reported success but file wasn't created.

**Solutions:**
- Check disk space
- Verify write permissions
- Look for file system errors in logs
- Check output directory exists

### Resource Errors

#### "Job video not found or raw_path not set"
**Cause:** The source video for rendering is missing or path is invalid.

**Solutions:**
- Re-process the original job
- Check if the raw video still exists
- Verify the job completed successfully

## General Errors

### Unexpected Errors

#### "Unexpected error during [operation]"
**Cause:** An unhandled exception occurred.

**Solutions:**
1. Check the full error message and stack trace in logs
2. Enable debug logging:
   ```python
   # In backend/app.py
   logging.basicConfig(level=logging.DEBUG)
   ```
3. Restart the backend
4. Try the operation again
5. Report the issue with full logs if it persists

### System Health

#### "License not activated" or "License expired"
**Cause:** License validation issues.

**Solutions:**
- Activate your license key via the /license endpoint
- Verify license key is correct
- Check license expiration date
- Contact support for license renewal

## Log Indicators

When reviewing logs, look for these indicators:

- `✓` - Successful operation
- `❌` - Failed operation
- `⚠` - Warning (operation continued but something was suboptimal)
- `INFO` - General information
- `WARNING` - Potential issues
- `ERROR` - Errors that stopped processing
- `DEBUG` - Detailed debugging information

## Getting Help

If you encounter an error not listed here:

1. **Check the logs** - Most errors have detailed explanations
2. **Enable debug logging** - Get more detailed information
3. **Update dependencies** - Ensure yt-dlp and ffmpeg are up to date
4. **Try a different video** - Rule out video-specific issues
5. **Report the issue** - Include:
   - Full error message
   - Video URL (if applicable)
   - Relevant log excerpts
   - System information (OS, Python version, etc.)

## Prevention Tips

### Before Processing
- Verify videos are public and accessible
- Check you have sufficient disk space
- Ensure all dependencies are installed and updated
- Test with a short, simple video first

### During Processing
- Monitor logs for warnings
- Check progress updates regularly
- Don't interrupt processes mid-stream

### Maintenance
- Regularly update yt-dlp (YouTube changes frequently)
- Keep system dependencies updated
- Clean up old processed files to free disk space
- Monitor backend logs for recurring issues
