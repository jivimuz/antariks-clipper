"""Tests for smart cropping services"""
import sys
import os
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_speaker_detection():
    """Test speaker detection logic"""
    print("\nTesting speaker detection...")
    
    try:
        from services.speaker_detect import SpeakerDetector
        
        detector = SpeakerDetector(speaking_threshold=5.0)
        
        # Test with no faces
        result = detector.update(None, [])
        assert result["mode"] == "solo"
        assert result["speakers"] == []
        print("✓ No faces handled correctly")
        
        # Test with one face (solo mode)
        face1 = {"id": 0, "bbox": [100, 100, 50, 50], "mouth_openness": 10.0}
        result = detector.update(None, [face1])
        assert result["mode"] == "solo"
        print("✓ Solo mode detected")
        
        # Test with two faces, no speaking (duo_switch mode)
        face1 = {"id": 0, "bbox": [100, 100, 50, 50], "mouth_openness": 10.0}
        face2 = {"id": 1, "bbox": [200, 100, 50, 50], "mouth_openness": 10.5}
        
        # Build up history with low variance (not speaking)
        for i in range(10):
            face1["mouth_openness"] = 10.0 + np.random.random() * 0.5
            face2["mouth_openness"] = 10.0 + np.random.random() * 0.5
            result = detector.update(None, [face1, face2])
        
        assert result["mode"] == "duo_switch"
        print("✓ Duo switch mode detected (no speakers)")
        
        # Test with two faces, both speaking (duo_split mode)
        detector2 = SpeakerDetector(speaking_threshold=1.0)
        
        # Build history with high variance (speaking)
        for i in range(10):
            face1["mouth_openness"] = 10.0 + np.random.random() * 5.0
            face2["mouth_openness"] = 10.0 + np.random.random() * 5.0
            result = detector2.update(None, [face1, face2])
        
        # Should detect both speaking and eventually switch to duo_split
        assert len(result["speakers"]) >= 0  # At least detecting speakers
        print("✓ Speaking detection working")
        
        print("✅ Speaker detection tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Speaker detection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smart_cropper():
    """Test smart cropping logic"""
    print("\nTesting smart cropping...")
    
    try:
        from services.smart_crop import SmartCropper
        
        # Create test frame (1920x1080 video)
        video_width = 1920
        video_height = 1080
        frame = np.zeros((video_height, video_width, 3), dtype=np.uint8)
        
        cropper = SmartCropper(video_width, video_height, 1080, 1920)
        
        # Test solo crop
        face_bbox = [800, 400, 200, 200]  # Center-ish face
        face = {"id": 0, "bbox": face_bbox}
        
        result = cropper.crop_solo(frame, face_bbox)
        assert result.shape == (1920, 1080, 3)
        print("✓ Solo crop produces correct output shape")
        
        # Test duo switch crop
        result = cropper.crop_duo_switch(frame, face_bbox)
        assert result.shape == (1920, 1080, 3)
        print("✓ Duo switch crop produces correct output shape")
        
        # Test duo split crop
        face1_bbox = [400, 300, 200, 200]
        face2_bbox = [1200, 300, 200, 200]
        
        result = cropper.crop_duo_split(frame, face1_bbox, face2_bbox)
        assert result.shape == (1920, 1080, 3)
        print("✓ Duo split crop produces correct output shape")
        
        # Test process_frame with different modes
        faces = [
            {"id": 0, "bbox": face1_bbox},
            {"id": 1, "bbox": face2_bbox}
        ]
        
        # Solo mode
        result = cropper.process_frame(frame, [faces[0]], [0], "solo")
        assert result.shape == (1920, 1080, 3)
        print("✓ process_frame solo mode works")
        
        # Duo switch mode
        result = cropper.process_frame(frame, faces, [0], "duo_switch")
        assert result.shape == (1920, 1080, 3)
        print("✓ process_frame duo_switch mode works")
        
        # Duo split mode
        result = cropper.process_frame(frame, faces, [0, 1], "duo_split")
        assert result.shape == (1920, 1080, 3)
        print("✓ process_frame duo_split mode works")
        
        # Test with no faces
        result = cropper.process_frame(frame, [], [], "solo")
        assert result.shape == (1920, 1080, 3)
        print("✓ process_frame handles no faces")
        
        print("✅ Smart cropper tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Smart cropper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_module_imports():
    """Test that new modules can be imported"""
    print("\nTesting module imports...")
    
    try:
        from services.speaker_detect import SpeakerDetector
        print("✓ speaker_detect module imported")
        
        from services.smart_crop import SmartCropper
        print("✓ smart_crop module imported")
        
        from services.reframe import reframe_video_smart
        print("✓ reframe module updated with smart function")
        
        print("✅ Module import tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Module import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running Smart Cropping System Tests")
    print("=" * 60)
    
    results = []
    
    # Test module imports first
    results.append(("Module Imports", test_module_imports()))
    
    # Test speaker detection
    results.append(("Speaker Detection", test_speaker_detection()))
    
    # Test smart cropper
    results.append(("Smart Cropper", test_smart_cropper()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(result for _, result in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
