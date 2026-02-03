"""Test job deletion restrictions"""
import httpx
import uuid
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_job_deletion_restrictions():
    """Test that jobs can only be deleted when status is 'ready'"""
    print("\n=== Testing Job Deletion Restrictions ===\n")
    
    try:
        import db
        
        # Initialize database
        db.init_db()
        
        # Test 1: Try to delete a job with status 'processing'
        print("Test 1: Attempting to delete a job with status 'processing'...")
        job_id_processing = str(uuid.uuid4())
        db.create_job(job_id_processing, source_type='youtube', source_url='https://youtube.com/test')
        db.update_job(job_id_processing, status='processing')
        
        response = httpx.delete(f"{BASE_URL}/api/jobs/{job_id_processing}")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Cannot delete job with status 'processing'" in response.json()['detail']
        print("✓ Correctly prevented deletion of processing job")
        
        # Test 2: Try to delete a job with status 'queued'
        print("\nTest 2: Attempting to delete a job with status 'queued'...")
        job_id_queued = str(uuid.uuid4())
        db.create_job(job_id_queued, source_type='youtube', source_url='https://youtube.com/test')
        # Status defaults to 'queued'
        
        response = httpx.delete(f"{BASE_URL}/api/jobs/{job_id_queued}")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Cannot delete job with status 'queued'" in response.json()['detail']
        print("✓ Correctly prevented deletion of queued job")
        
        # Test 3: Try to delete a job with status 'failed'
        print("\nTest 3: Attempting to delete a job with status 'failed'...")
        job_id_failed = str(uuid.uuid4())
        db.create_job(job_id_failed, source_type='youtube', source_url='https://youtube.com/test')
        db.update_job(job_id_failed, status='failed', error='Test error')
        
        response = httpx.delete(f"{BASE_URL}/api/jobs/{job_id_failed}")
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Cannot delete job with status 'failed'" in response.json()['detail']
        print("✓ Correctly prevented deletion of failed job")
        
        # Test 4: Delete a job with status 'ready' (should succeed)
        print("\nTest 4: Attempting to delete a job with status 'ready'...")
        job_id_ready = str(uuid.uuid4())
        db.create_job(job_id_ready, source_type='youtube', source_url='https://youtube.com/test')
        db.update_job(job_id_ready, status='ready')
        
        response = httpx.delete(f"{BASE_URL}/api/jobs/{job_id_ready}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.json()['message'] == 'Job deleted successfully'
        print("✓ Successfully deleted ready job")
        
        # Verify the job was actually deleted
        job = db.get_job(job_id_ready)
        assert job is None, "Job should have been deleted from database"
        print("✓ Verified job was deleted from database")
        
        # Clean up test jobs (except the ready one which was already deleted)
        for job_id in [job_id_processing, job_id_queued, job_id_failed]:
            try:
                db.delete_job(job_id)
            except:
                pass
        
        print("\n=== All deletion restriction tests passed! ===\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Starting job deletion restriction tests...")
    print("Make sure the backend server is running on http://127.0.0.1:8000")
    print("You can start it with: uvicorn app:app --reload --port 8000")
    input("\nPress Enter to continue...")
    
    success = test_job_deletion_restrictions()
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Tests failed!")
        exit(1)
