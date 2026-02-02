"""
Test enhanced highlight detection features
"""
import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.highlight import (
    generate_highlights,
    calculate_dynamic_clip_count,
    score_segment,
    detect_keyword_categories
)


def test_dynamic_clip_count():
    """Test dynamic clip count calculation for different video durations"""
    print("Testing dynamic clip count calculation...")
    
    test_cases = [
        (300, 12),    # 5 min -> at least 12
        (600, 12),    # 10 min -> 12
        (1800, 12),   # 30 min -> 12
        (3600, 20),   # 60 min -> 20
        (7200, 30),   # 120 min -> 30
        (10800, 50),  # 180 min -> 50 (capped)
    ]
    
    for duration, expected_min in test_cases:
        result = calculate_dynamic_clip_count(duration)
        assert result >= expected_min, f"Duration {duration}s should generate at least {expected_min} clips, got {result}"
        print(f"  ✓ {duration/60:.0f} min video -> {result} clips")
    
    print("✓ Dynamic clip count test passed!\n")


def test_keyword_detection():
    """Test keyword category detection"""
    print("Testing keyword category detection...")
    
    test_cases = [
        ("Ini penting banget untuk kalian tahu", ['importance']),
        ("Ternyata ada rahasia yang gila", ['revelation']),
        ("Jadi intinya kita harus fokus", ['summary']),
        ("Cara terbaik adalah dengan tutorial ini", ['teaching', 'revelation']),
        ("This is important and you must know", ['importance']),
    ]
    
    for text, expected_categories in test_cases:
        categories = detect_keyword_categories(text)
        found_categories = list(categories.keys())
        
        for expected in expected_categories:
            assert expected in found_categories, f"Expected '{expected}' in categories for: {text}"
        
        print(f"  ✓ '{text[:40]}...' -> {found_categories}")
    
    print("✓ Keyword detection test passed!\n")


def test_scoring():
    """Test segment scoring with metadata"""
    print("Testing segment scoring...")
    
    # Test segment with important keywords
    text1 = "Ini penting banget yang harus kamu tahu tentang cara terbaik untuk sukses"
    score1, meta1 = score_segment(text1, 0, 30, 3600, 0, 100)
    
    assert score1 > 50, f"High-quality segment should score > 50, got {score1}"
    assert 'importance' in meta1['categories'] or 'teaching' in meta1['categories']
    print(f"  ✓ Important content scored {score1:.1f} with categories {meta1['categories']}")
    
    # Test segment with questions
    text2 = "Bagaimana cara melakukan ini dengan benar? Mengapa hal ini penting?"
    score2, meta2 = score_segment(text2, 0, 25, 3600, 50, 100)
    
    assert meta2['has_question'], "Should detect question"
    print(f"  ✓ Question content scored {score2:.1f}, has_question={meta2['has_question']}")
    
    # Test segment with low quality
    text3 = "a b c d e f g"
    score3, meta3 = score_segment(text3, 0, 20, 3600, 75, 100)
    
    assert score3 < 50, f"Low-quality segment should score < 50, got {score3}"
    print(f"  ✓ Low-quality content scored {score3:.1f}")
    
    print("✓ Scoring test passed!\n")


def test_highlight_generation_short_video():
    """Test highlight generation for a short video (10 min)"""
    print("Testing highlight generation for short video...")
    
    # Create mock transcript for 10-minute video with some interesting content
    segments = []
    for i in range(30):  # 30 segments, each ~20 seconds
        start = i * 20
        end = start + 20
        
        # Add some variety in content quality
        if i % 5 == 0:
            text = f"Ini penting banget segment {i} yang harus kamu tahu"
        elif i % 5 == 1:
            text = f"Ternyata ada rahasia menarik di segment {i}"
        elif i % 5 == 2:
            text = f"Jadi intinya pada segment {i} kita harus fokus"
        else:
            text = f"Regular content di segment {i} tanpa keyword khusus"
        
        segments.append({
            'start': start,
            'end': end,
            'text': text
        })
    
    transcript = {
        'duration': 600,  # 10 minutes
        'segments': segments
    }
    
    # Generate highlights
    highlights = generate_highlights(transcript)
    
    assert len(highlights) > 0, "Should generate at least one highlight"
    assert len(highlights) <= 15, f"Should not generate more than 15 clips for 10-min video, got {len(highlights)}"
    
    # Check that highlights have required fields
    for hl in highlights:
        assert 'start' in hl
        assert 'end' in hl
        assert 'score' in hl
        assert 'title' in hl
        assert 'snippet' in hl
        assert 'metadata' in hl
        assert 'duration' in hl
        
        # Check duration is within bounds
        duration = hl['end'] - hl['start']
        assert duration >= 15, f"Clip duration {duration}s should be >= 15s"
        assert duration <= 60, f"Clip duration {duration}s should be <= 60s"
    
    print(f"  ✓ Generated {len(highlights)} highlights")
    print(f"  ✓ Duration range: {min(h['duration'] for h in highlights):.1f}s - {max(h['duration'] for h in highlights):.1f}s")
    print(f"  ✓ Score range: {min(h['score'] for h in highlights):.1f} - {max(h['score'] for h in highlights):.1f}")
    print("✓ Short video highlight generation test passed!\n")


def test_highlight_generation_long_video():
    """Test highlight generation for a long video (2 hours)"""
    print("Testing highlight generation for long video (simulated)...")
    
    # Create mock transcript for 2-hour video
    segments = []
    for i in range(360):  # 360 segments, each ~20 seconds = 2 hours
        start = i * 20
        end = start + 20
        
        # Sprinkle interesting content throughout
        if i % 15 == 0:  # Every 5 minutes
            text = f"Ini penting segment {i} dengan informasi krusial"
        elif i % 15 == 3:
            text = f"Ternyata rahasia menarik ada di segment {i}"
        elif i % 15 == 7:
            text = f"Bagaimana cara terbaik melakukan ini di segment {i}?"
        else:
            text = f"Content segment {i}"
        
        segments.append({
            'start': start,
            'end': end,
            'text': text
        })
    
    transcript = {
        'duration': 7200,  # 2 hours
        'segments': segments
    }
    
    # Generate highlights with auto clip count
    highlights = generate_highlights(transcript, adaptive=True)
    
    assert len(highlights) >= 20, f"Should generate at least 20 clips for 2-hour video, got {len(highlights)}"
    assert len(highlights) <= 35, f"Should not generate more than 35 clips for 2-hour video, got {len(highlights)}"
    
    # Verify clips are spread throughout the video
    first_clip_start = highlights[0]['start']
    last_clip_start = highlights[-1]['start']
    coverage = (last_clip_start - first_clip_start) / 7200
    
    assert coverage > 0.5, f"Clips should cover at least 50% of video timeline, got {coverage*100:.1f}%"
    
    print(f"  ✓ Generated {len(highlights)} highlights")
    print(f"  ✓ Timeline coverage: {coverage*100:.1f}%")
    print(f"  ✓ Duration range: {min(h['duration'] for h in highlights):.1f}s - {max(h['duration'] for h in highlights):.1f}s")
    print(f"  ✓ Score range: {min(h['score'] for h in highlights):.1f} - {max(h['score'] for h in highlights):.1f}")
    
    # Check metadata
    clips_with_categories = [h for h in highlights if h['metadata'].get('categories')]
    print(f"  ✓ {len(clips_with_categories)}/{len(highlights)} clips have keyword categories")
    
    print("✓ Long video highlight generation test passed!\n")


def test_custom_clip_count():
    """Test generating highlights with custom clip count"""
    print("Testing custom clip count...")
    
    segments = []
    for i in range(60):
        start = i * 20
        end = start + 20
        text = f"Segment {i} dengan content yang menarik"
        if i % 3 == 0:
            text = f"Ini penting di segment {i}"
        segments.append({'start': start, 'end': end, 'text': text})
    
    transcript = {
        'duration': 1200,  # 20 minutes
        'segments': segments
    }
    
    # Test with explicit clip count
    for clip_count in [5, 10, 15]:
        highlights = generate_highlights(transcript, top_n=clip_count)
        
        # Allow some flexibility (might be less if not enough non-overlapping segments)
        assert len(highlights) <= clip_count, f"Should generate at most {clip_count} clips, got {len(highlights)}"
        assert len(highlights) >= min(clip_count, 5), f"Should generate at least {min(clip_count, 5)} clips"
        
        print(f"  ✓ Requested {clip_count} clips, got {len(highlights)}")
    
    print("✓ Custom clip count test passed!\n")


def main():
    """Run all tests"""
    print("="*60)
    print("ENHANCED HIGHLIGHT DETECTION TEST SUITE")
    print("="*60)
    print()
    
    try:
        test_dynamic_clip_count()
        test_keyword_detection()
        test_scoring()
        test_highlight_generation_short_video()
        test_highlight_generation_long_video()
        test_custom_clip_count()
        
        print("="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        return 0
    
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
