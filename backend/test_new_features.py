"""
Test script for new features:
- Pagination
- Delete job functionality
"""
import sys
import unittest
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import db
from config import RAW_DIR, TRANSCRIPTS_DIR, THUMBNAILS_DIR, RENDERS_DIR

class TestPagination(unittest.TestCase):
    """Test pagination functionality"""
    
    def test_get_all_jobs_with_pagination(self):
        """Test that pagination parameters work correctly"""
        # Create a few test jobs
        job_ids = []
        for i in range(5):
            job_id = f"test-pagination-{i}"
            db.create_job(job_id, "upload", None)
            job_ids.append(job_id)
        
        try:
            # Test limit
            jobs = db.get_all_jobs(limit=2, offset=0)
            self.assertTrue(len(jobs) <= 2, "Limit should restrict results")
            
            # Test offset
            jobs_page1 = db.get_all_jobs(limit=2, offset=0)
            jobs_page2 = db.get_all_jobs(limit=2, offset=2)
            
            # Pages should have different jobs
            if len(jobs_page1) > 0 and len(jobs_page2) > 0:
                self.assertNotEqual(
                    jobs_page1[0]['id'], 
                    jobs_page2[0]['id'],
                    "Different pages should have different jobs"
                )
            
            # Test total count
            total = db.get_total_jobs_count()
            self.assertIsInstance(total, int)
            self.assertGreaterEqual(total, 5, "Should have at least 5 jobs")
            
            print("✓ Pagination tests passed")
            
        finally:
            # Cleanup
            for job_id in job_ids:
                try:
                    db.delete_job(job_id)
                except:
                    pass

class TestDeleteJob(unittest.TestCase):
    """Test job deletion functionality"""
    
    def test_delete_job_removes_all_data(self):
        """Test that deleting a job removes all associated data"""
        job_id = "test-delete-job"
        
        # Create job
        db.create_job(job_id, "youtube", "https://www.youtube.com/watch?v=test")
        
        # Create a clip
        clip_id = "test-clip"
        db.create_clip(clip_id, job_id, 0.0, 10.0, 50.0, "Test Clip", "Test snippet")
        
        # Create a render
        render_id = "test-render"
        db.create_render(render_id, clip_id, {"face_tracking": False})
        
        # Verify everything exists
        self.assertIsNotNone(db.get_job(job_id))
        self.assertIsNotNone(db.get_clip(clip_id))
        self.assertIsNotNone(db.get_render(render_id))
        
        # Delete job
        result = db.delete_job(job_id)
        self.assertTrue(result, "Delete should return True")
        
        # Verify everything is deleted
        self.assertIsNone(db.get_job(job_id))
        self.assertIsNone(db.get_clip(clip_id))
        self.assertIsNone(db.get_render(render_id))
        
        print("✓ Delete job tests passed")
    
    def test_get_renders_by_job(self):
        """Test getting all renders for a job"""
        job_id = "test-renders-by-job"
        
        try:
            # Create job
            db.create_job(job_id, "upload", None)
            
            # Create clips
            clip_id1 = "test-clip-1"
            clip_id2 = "test-clip-2"
            db.create_clip(clip_id1, job_id, 0.0, 10.0)
            db.create_clip(clip_id2, job_id, 10.0, 20.0)
            
            # Create renders
            render_id1 = "test-render-1"
            render_id2 = "test-render-2"
            db.create_render(render_id1, clip_id1, {"face_tracking": True})
            db.create_render(render_id2, clip_id2, {"captions": True})
            
            # Get renders by job
            renders = db.get_renders_by_job(job_id)
            
            self.assertEqual(len(renders), 2, "Should have 2 renders")
            self.assertTrue(any(r['id'] == render_id1 for r in renders))
            self.assertTrue(any(r['id'] == render_id2 for r in renders))
            
            print("✓ Get renders by job tests passed")
            
        finally:
            # Cleanup
            db.delete_job(job_id)

def run_tests():
    """Run all tests"""
    print("="*60)
    print("Running New Features Tests")
    print("="*60)
    
    # Initialize database
    db.init_db()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestPagination))
    suite.addTests(loader.loadTestsFromTestCase(TestDeleteJob))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("✓ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("="*60)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
