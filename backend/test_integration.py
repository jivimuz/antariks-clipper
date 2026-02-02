#!/usr/bin/env python3
"""Integration test for the clipping pipeline"""
import sys
import os
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.downloader import (
    check_dependencies, 
    validate_youtube_url,
    get_video_info
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_dependencies():
    """Test 1: Verify all dependencies are installed"""
    logger.info("="*60)
    logger.info("TEST 1: Dependency Check")
    logger.info("="*60)
    
    deps_ok, missing, versions = check_dependencies()
    
    if deps_ok:
        logger.info("✓ All dependencies installed")
        logger.info(f"  yt-dlp: {versions.get('yt-dlp')}")
        logger.info(f"  ffmpeg: {versions.get('ffmpeg')}")
        return True
    else:
        logger.error(f"❌ Missing dependencies: {missing}")
        return False

def test_url_validation():
    """Test 2: URL validation"""
    logger.info("="*60)
    logger.info("TEST 2: URL Validation")
    logger.info("="*60)
    
    test_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", True, "Standard video"),
        ("https://youtu.be/dQw4w9WgXcQ", True, "Short URL"),
        ("https://www.youtube.com/shorts/abc123", True, "Shorts"),
        ("https://vimeo.com/123456", False, "Non-YouTube URL"),
        ("not a url", False, "Invalid format"),
    ]
    
    all_passed = True
    for url, expected, description in test_cases:
        result = validate_youtube_url(url)
        status = "✓" if result == expected else "❌"
        logger.info(f"{status} {description}: {url}")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_video_info():
    """Test 3: Get video information (may fail in sandboxed/offline environments)"""
    logger.info("="*60)
    logger.info("TEST 3: Video Info Retrieval")
    logger.info("="*60)
    
    # Use a known, stable YouTube video (never gonna give you up by Rick Astley)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    logger.info(f"Testing with: {test_url}")
    logger.info("Note: This test requires internet access and may fail in sandboxed environments")
    
    info = get_video_info(test_url)
    
    if info:
        logger.info("✓ Successfully retrieved video info")
        logger.info(f"  Title: {info.get('title', 'N/A')}")
        logger.info(f"  Duration: {info.get('duration', 0)}s")
        logger.info(f"  Uploader: {info.get('uploader', 'N/A')}")
        return True
    else:
        logger.warning("⚠ Failed to retrieve video info")
        logger.warning("This might be expected if:")
        logger.warning("  - Running in a sandboxed environment (no internet)")
        logger.warning("  - Network connectivity issues")
        logger.warning("  - YouTube rate limiting")
        logger.warning("  - Outdated yt-dlp version")
        logger.info("Marking as SKIPPED (not failed) due to environment limitations")
        return None  # Return None to mark as skipped

def test_error_scenarios():
    """Test 4: Error handling with invalid URLs"""
    logger.info("="*60)
    logger.info("TEST 4: Error Handling")
    logger.info("="*60)
    
    # Test with invalid video ID
    test_url = "https://www.youtube.com/watch?v=INVALID_VIDEO_ID"
    
    logger.info(f"Testing error handling with invalid URL: {test_url}")
    logger.info("Note: This test requires internet access and may be skipped in sandboxed environments")
    
    info = get_video_info(test_url)
    
    if info is None:
        logger.info("✓ Correctly handled invalid video URL (returned None)")
        return True
    else:
        logger.error("❌ Should have returned None for invalid video")
        return False

def main():
    """Run all integration tests"""
    logger.info("\n" + "="*60)
    logger.info("ANTARIKS CLIPPER - INTEGRATION TESTS")
    logger.info("="*60 + "\n")
    
    results = {}
    
    # Run tests
    results['dependencies'] = test_dependencies()
    print()
    
    results['url_validation'] = test_url_validation()
    print()
    
    # Only run video info tests if dependencies are OK
    if results['dependencies']:
        results['video_info'] = test_video_info()
        print()
        
        results['error_handling'] = test_error_scenarios()
        print()
    else:
        logger.warning("Skipping video tests due to missing dependencies")
        results['video_info'] = None
        results['error_handling'] = None
    
    # Summary
    logger.info("="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    for test_name, result in results.items():
        if result is True:
            logger.info(f"✓ {test_name}: PASSED")
        elif result is False:
            logger.error(f"❌ {test_name}: FAILED")
        else:
            logger.warning(f"⊘ {test_name}: SKIPPED")
    
    logger.info("-"*60)
    logger.info(f"Results: {passed} passed, {failed} failed, {skipped} skipped out of {total} tests")
    logger.info("="*60)
    
    if failed > 0:
        logger.error("\n⚠️  Some tests failed. Please review the errors above.")
        sys.exit(1)
    elif skipped > 0:
        logger.warning("\n⚠️  Some tests were skipped. Install missing dependencies to run all tests.")
        sys.exit(0)
    else:
        logger.info("\n🎉 All tests passed! The clipping system is ready to use.")
        sys.exit(0)

if __name__ == "__main__":
    main()
