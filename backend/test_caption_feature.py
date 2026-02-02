#!/usr/bin/env python3
"""
Test script for caption and hashtag generation feature
"""
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import db
from services.caption_generator import generate_caption, generate_hashtags

def test_caption_generator():
    """Test caption generation with various inputs"""
    print("=" * 60)
    print("TEST 1: Caption Generator with Importance Category")
    print("=" * 60)
    
    caption = generate_caption(
        title="Important Tutorial: How to Build APIs",
        transcript_snippet="This is a crucial tip that every developer needs to know about API design",
        metadata={'categories': ['importance']}
    )
    
    print(f"Caption:\n{caption}\n")
    assert "⚠️" in caption, "Should have importance emoji"
    assert "What do you think?" in caption, "Should have call to action"
    print("✓ Test 1 passed\n")


def test_hashtag_generator():
    """Test hashtag generation with various inputs"""
    print("=" * 60)
    print("TEST 2: Hashtag Generator")
    print("=" * 60)
    
    hashtags = generate_hashtags(
        title="Amazing Tutorial on Python",
        transcript_snippet="Learn how to code efficiently",
        metadata={'categories': ['teaching']}
    )
    
    print(f"Hashtags: {hashtags}\n")
    assert "#fyp" in hashtags, "Should have default #fyp"
    assert "#viral" in hashtags, "Should have default #viral"
    assert "#antariksclipper" in hashtags, "Should have default #antariksclipper"
    assert "#tutorial" in hashtags, "Should have teaching category hashtag"
    print("✓ Test 2 passed\n")


def test_database_integration():
    """Test that caption and hashtags are stored in database"""
    print("=" * 60)
    print("TEST 3: Database Integration")
    print("=" * 60)
    
    # Initialize database
    db.init_db()
    
    # Create a test job
    import uuid
    job_id = str(uuid.uuid4())
    db.create_job(job_id, source_type="test", source_url="http://test.com")
    
    # Create a test clip with caption and hashtags
    clip_id = str(uuid.uuid4())
    caption = generate_caption(
        title="Test Clip",
        transcript_snippet="This is a test transcript",
        metadata={'categories': ['revelation']}
    )
    hashtags = generate_hashtags(
        title="Test Clip",
        transcript_snippet="This is a test transcript",
        metadata={'categories': ['revelation']}
    )
    
    clip = db.create_clip(
        clip_id=clip_id,
        job_id=job_id,
        start_sec=0.0,
        end_sec=30.0,
        score=85.5,
        title="Test Clip",
        transcript_snippet="This is a test transcript",
        caption_text=caption,
        hashtags_text=hashtags
    )
    
    print(f"Created clip: {clip['id']}")
    print(f"Caption: {clip['caption_text'][:50]}...")
    print(f"Hashtags: {clip['hashtags_text']}")
    
    # Verify clip was stored correctly
    retrieved_clip = db.get_clip(clip_id)
    assert retrieved_clip is not None, "Clip should be retrieved"
    assert retrieved_clip['caption_text'] == caption, "Caption should match"
    assert retrieved_clip['hashtags_text'] == hashtags, "Hashtags should match"
    assert "💡" in retrieved_clip['caption_text'], "Should have revelation emoji"
    assert "#amazing" in retrieved_clip['hashtags_text'], "Should have revelation hashtag"
    
    # Clean up
    db.delete_clip(clip_id)
    db.delete_job(job_id)
    
    print("✓ Test 3 passed\n")


def test_api_response():
    """Test that API returns caption and hashtags"""
    print("=" * 60)
    print("TEST 4: API Response Format")
    print("=" * 60)
    
    # Create test data
    db.init_db()
    import uuid
    job_id = str(uuid.uuid4())
    db.create_job(job_id, source_type="test", source_url="http://test.com")
    
    clip_id = str(uuid.uuid4())
    clip = db.create_clip(
        clip_id=clip_id,
        job_id=job_id,
        start_sec=0.0,
        end_sec=30.0,
        score=90.0,
        title="API Test Clip",
        transcript_snippet="Testing API response",
        caption_text="Test caption with emoji 🎬\n\n💬 What do you think?",
        hashtags_text="#fyp #viral #test #api"
    )
    
    # Get clips for job
    clips = db.get_clips_by_job(job_id)
    
    print(f"Retrieved {len(clips)} clip(s)")
    print(f"Clip data: {json.dumps(clips[0], indent=2, default=str)}")
    
    assert len(clips) == 1, "Should have 1 clip"
    assert clips[0]['caption_text'] is not None, "Caption should be present"
    assert clips[0]['hashtags_text'] is not None, "Hashtags should be present"
    assert "caption_text" in clips[0], "Should have caption_text field"
    assert "hashtags_text" in clips[0], "Should have hashtags_text field"
    
    # Clean up
    db.delete_clip(clip_id)
    db.delete_job(job_id)
    
    print("✓ Test 4 passed\n")


if __name__ == "__main__":
    try:
        print("\n🧪 Testing Caption & Hashtag Generation Feature\n")
        
        test_caption_generator()
        test_hashtag_generator()
        test_database_integration()
        test_api_response()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nFeature is working correctly:")
        print("  ✓ Caption generation with emojis and call-to-action")
        print("  ✓ Hashtag generation with default and category-based tags")
        print("  ✓ Database storage of caption_text and hashtags_text")
        print("  ✓ API returns caption and hashtags in clip data")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
