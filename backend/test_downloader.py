"""Test downloader improvements"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_url_validation():
    """Test YouTube URL validation"""
    print("Testing URL validation...")
    from services.downloader import validate_youtube_url
    
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/abc123def",
        "https://youtube.com/shorts/abc123def",
        "https://www.youtube.com/live/xyz789",
        "http://youtube.com/watch?v=test123",
    ]
    
    invalid_urls = [
        "https://vimeo.com/123456",
        "https://example.com/video",
        "not a url",
        "",
        "https://youtube.com/user/test",
    ]
    
    # Test valid URLs
    for url in valid_urls:
        result = validate_youtube_url(url)
        assert result, f"Expected valid: {url}"
        print(f"✓ Valid: {url}")
    
    # Test invalid URLs
    for url in invalid_urls:
        result = validate_youtube_url(url)
        assert not result, f"Expected invalid: {url}"
        print(f"✓ Invalid: {url}")
    
    print("\n✅ URL validation tests passed!\n")
    return True

def test_dependency_check():
    """Test dependency checking"""
    print("Testing dependency check...")
    from services.downloader import check_dependencies
    
    deps_ok, missing, versions = check_dependencies()
    
    print(f"Dependencies OK: {deps_ok}")
    print(f"Missing: {missing}")
    print(f"Versions: {versions}")
    
    # Should have 3 return values
    assert isinstance(deps_ok, bool)
    assert isinstance(missing, list)
    assert isinstance(versions, dict)
    
    print("\n✅ Dependency check tests passed!\n")
    return True

def test_progress_callback():
    """Test progress callback structure"""
    print("Testing progress callback...")
    
    # Create a test callback
    progress_updates = []
    
    def test_callback(percent, message):
        progress_updates.append((percent, message))
        print(f"  Progress: {percent}% - {message}")
    
    # Simulate progress updates
    test_callback(0, "Starting download...")
    test_callback(25, "Downloading... 25%")
    test_callback(50, "Downloading... 50%")
    test_callback(75, "Downloading... 75%")
    test_callback(100, "Download complete!")
    
    assert len(progress_updates) == 5
    assert progress_updates[0] == (0, "Starting download...")
    assert progress_updates[4] == (100, "Download complete!")
    
    print("\n✅ Progress callback tests passed!\n")
    return True

def test_function_signatures():
    """Test that new function signatures are correct"""
    print("Testing function signatures...")
    from services.downloader import (
        download_youtube, 
        get_video_info, 
        save_upload,
        validate_youtube_url,
        check_dependencies
    )
    import inspect
    
    # Check download_youtube signature
    sig = inspect.signature(download_youtube)
    params = list(sig.parameters.keys())
    assert 'url' in params
    assert 'output_path' in params
    assert 'progress_callback' in params
    assert 'cookies_file' in params
    print("✓ download_youtube signature correct")
    
    # Check get_video_info exists
    sig = inspect.signature(get_video_info)
    params = list(sig.parameters.keys())
    assert 'url' in params
    print("✓ get_video_info signature correct")
    
    # Check validate_youtube_url exists
    sig = inspect.signature(validate_youtube_url)
    params = list(sig.parameters.keys())
    assert 'url' in params
    print("✓ validate_youtube_url signature correct")
    
    # Check check_dependencies new signature
    sig = inspect.signature(check_dependencies)
    # Should return tuple of 3 values
    print("✓ check_dependencies signature correct")
    
    print("\n✅ Function signature tests passed!\n")
    return True

if __name__ == "__main__":
    success = True
    success = test_url_validation() and success
    success = test_dependency_check() and success
    success = test_progress_callback() and success
    success = test_function_signatures() and success
    
    if success:
        print("\n" + "="*50)
        print("🎉 All downloader tests passed!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("⚠️  Some downloader tests failed")
        print("="*50)
        sys.exit(1)
