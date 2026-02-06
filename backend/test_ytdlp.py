"""Test yt-dlp detection and download"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.downloader import check_dependencies, download_youtube
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=" * 60)
    print("Testing yt-dlp Detection")
    print("=" * 60)
    
    # Check dependencies
    deps_ok, missing, versions = check_dependencies()
    
    print(f"\n✓ Dependencies OK: {deps_ok}")
    print(f"Missing: {missing}")
    print(f"Versions: {versions}")
    
    if not deps_ok:
        print("\n❌ Dependencies missing!")
        print("Install with:")
        print("  pip install yt-dlp")
        print("  pip install ffmpeg-python  # or install ffmpeg binary")
        return
    
    print("\n✅ All dependencies found!")
    print(f"  - yt-dlp: {versions.get('yt-dlp')}")
    print(f"  - ffmpeg: {versions.get('ffmpeg')}")
    
    # Try a test download (short video)
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video, 19 seconds
    output = Path("test_download.mp4")
    
    print(f"\nTest download: {test_url}")
    print(f"Output: {output}")
    
    def progress(percent, message):
        print(f"  [{percent:3d}%] {message}")
    
    success, error = download_youtube(test_url, output, progress_callback=progress)
    
    if success:
        print(f"\n✅ Test download successful!")
        print(f"File size: {output.stat().st_size / 1024:.2f} KB")
        if output.exists():
            output.unlink()
            print("Cleaned up test file")
    else:
        print(f"\n❌ Test download failed!")
        print(f"Error: {error}")

if __name__ == "__main__":
    main()
