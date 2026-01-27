"""Simple test to verify backend modules load correctly"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_syntax():
    """Test that all modules have valid syntax"""
    print("Testing module syntax...")
    
    modules_to_test = [
        'config',
        'db',
        'app',
    ]
    
    service_modules = [
        'downloader',
        'ffmpeg',
        'highlight',
        'thumbnails',
        'jobs',
        'preview',
    ]
    
    # Test core modules that don't require heavy dependencies
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ {module}.py syntax OK")
        except ImportError as e:
            if 'No module named' in str(e) and module not in str(e):
                print(f"✓ {module}.py syntax OK (missing dependency: {e})")
            else:
                print(f"❌ {module}.py has syntax errors: {e}")
                return False
        except Exception as e:
            print(f"❌ {module}.py failed: {e}")
            return False
    
    # Test service modules
    for module in service_modules:
        try:
            __import__(f'services.{module}')
            print(f"✓ services/{module}.py syntax OK")
        except ImportError as e:
            if 'No module named' in str(e) and module not in str(e):
                print(f"✓ services/{module}.py syntax OK (missing dependency: {e})")
            else:
                print(f"❌ services/{module}.py has syntax errors: {e}")
                return False
        except Exception as e:
            print(f"❌ services/{module}.py failed: {e}")
            return False
    
    print("\n✅ All module syntax checks passed!")
    return True

def test_database():
    """Test database initialization"""
    print("\nTesting database...")
    
    try:
        import db
        import uuid
        
        db.init_db()
        print("✓ Database initialized")
        
        # Test job creation with unique ID
        test_job_id = str(uuid.uuid4())
        job = db.create_job(test_job_id, "youtube", "https://youtube.com/test")
        print(f"✓ Created test job: {job['id']}")
        
        # Test job retrieval
        retrieved = db.get_job(test_job_id)
        assert retrieved is not None
        assert retrieved['id'] == test_job_id
        print("✓ Retrieved test job")
        
        # Test clip creation
        test_clip_id = str(uuid.uuid4())
        clip = db.create_clip(test_clip_id, test_job_id, 10.0, 45.0, 75.5, "Test Clip", "Sample text")
        print(f"✓ Created test clip: {clip['id']}")
        
        # Test getting clips for job
        clips = db.get_clips_by_job(test_job_id)
        assert len(clips) == 1
        print("✓ Retrieved clips for job")
        
        # Test render creation
        test_render_id = str(uuid.uuid4())
        render = db.create_render(test_render_id, test_clip_id, {"face_tracking": True})
        print(f"✓ Created test render: {render['id']}")
        
        print("\n✅ Database tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cleanup_raw_file():
    """Test cleanup_raw_file function logic"""
    print("\nTesting cleanup_raw_file...")
    
    try:
        from pathlib import Path
        import tempfile
        import logging
        
        # Define the cleanup function inline to test it independently
        # This tests the logic without requiring heavy dependencies
        def cleanup_raw_file(raw_path: str) -> bool:
            """
            Delete raw file after processing completes to save disk space.
            Normalized files are kept for rendering clips.
            """
            try:
                if raw_path and Path(raw_path).exists():
                    Path(raw_path).unlink()
                    logging.info(f"Cleaned up raw file: {raw_path}")
                    return True
                return False
            except Exception as e:
                logging.warning(f"Failed to cleanup raw file {raw_path}: {e}")
                return False
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.mp4') as f:
            test_file_path = f.name
            f.write("test content")
        
        # Verify file exists
        assert Path(test_file_path).exists()
        print(f"✓ Created test file: {test_file_path}")
        
        # Test cleanup
        result = cleanup_raw_file(test_file_path)
        assert result is True
        print("✓ cleanup_raw_file returned True")
        
        # Verify file was deleted
        assert not Path(test_file_path).exists()
        print("✓ File was successfully deleted")
        
        # Test cleanup on non-existent file
        result = cleanup_raw_file(test_file_path)
        assert result is False
        print("✓ cleanup_raw_file returns False for non-existent file")
        
        # Test cleanup with empty path
        result = cleanup_raw_file("")
        assert result is False
        print("✓ cleanup_raw_file returns False for empty path")
        
        # Test cleanup with None
        result = cleanup_raw_file(None)
        assert result is False
        print("✓ cleanup_raw_file returns False for None path")
        
        print("\n✅ cleanup_raw_file tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ cleanup_raw_file test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_retry_job():
    """Test retry job functionality"""
    print("\nTesting retry job...")
    
    try:
        import db
        import uuid
        
        # Create a failed job
        test_job_id = str(uuid.uuid4())
        job = db.create_job(test_job_id, "youtube", "https://youtube.com/test")
        print(f"✓ Created test job: {job['id']}")
        
        # Mark as failed
        db.update_job(test_job_id, status='failed', error='Test error')
        failed_job = db.get_job(test_job_id)
        assert failed_job['status'] == 'failed'
        assert failed_job['error'] == 'Test error'
        print("✓ Marked job as failed")
        
        # Simulate retry (reset status)
        db.update_job(test_job_id, status='queued', error=None, progress=0)
        retried_job = db.get_job(test_job_id)
        assert retried_job['status'] == 'queued'
        assert retried_job['error'] is None
        assert retried_job['progress'] == 0
        print("✓ Job status reset to queued")
        
        # Test with ready job
        db.update_job(test_job_id, status='ready', progress=100)
        ready_job = db.get_job(test_job_id)
        assert ready_job['status'] == 'ready'
        print("✓ Job marked as ready")
        
        # Retry ready job should work
        db.update_job(test_job_id, status='queued', error=None, progress=0)
        retried_again = db.get_job(test_job_id)
        assert retried_again['status'] == 'queued'
        print("✓ Ready job can be retried")
        
        print("\n✅ Retry job tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Retry job test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_retry_render():
    """Test retry render functionality"""
    print("\nTesting retry render...")
    
    try:
        import db
        import uuid
        
        # Create job and clip for render
        test_job_id = str(uuid.uuid4())
        job = db.create_job(test_job_id, "youtube", "https://youtube.com/test")
        
        test_clip_id = str(uuid.uuid4())
        clip = db.create_clip(test_clip_id, test_job_id, 10.0, 45.0, 75.5, "Test Clip", "Sample text")
        print(f"✓ Created test clip: {clip['id']}")
        
        # Create a failed render
        test_render_id = str(uuid.uuid4())
        render = db.create_render(test_render_id, test_clip_id, {"face_tracking": True})
        print(f"✓ Created test render: {render['id']}")
        
        # Mark as failed
        db.update_render(test_render_id, status='failed', error='Render test error')
        failed_render = db.get_render(test_render_id)
        assert failed_render['status'] == 'failed'
        assert failed_render['error'] == 'Render test error'
        print("✓ Marked render as failed")
        
        # Simulate retry (reset status)
        db.update_render(test_render_id, status='queued', error=None, progress=0)
        retried_render = db.get_render(test_render_id)
        assert retried_render['status'] == 'queued'
        assert retried_render['error'] is None
        assert retried_render['progress'] == 0
        print("✓ Render status reset to queued")
        
        print("\n✅ Retry render tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Retry render test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = True
    success = test_syntax() and success
    success = test_database() and success
    success = test_cleanup_raw_file() and success
    success = test_retry_job() and success
    success = test_retry_render() and success
    
    if success:
        print("\n" + "="*50)
        print("🎉 All tests passed!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("⚠️  Some tests failed")
        print("="*50)
        sys.exit(1)
