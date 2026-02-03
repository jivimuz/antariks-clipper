"""
Test script for license expiry notification feature
This script tests various license expiry scenarios
"""
import json
from datetime import date, timedelta
from pathlib import Path
from services.license import (
    get_days_until_expiry,
    is_expiring_soon,
    is_expired,
    save_license,
    load_license,
    get_license_status,
    LICENSE_FILE
)

def test_license_expiry_scenarios():
    """Test different license expiry scenarios"""
    print("=" * 60)
    print("TESTING LICENSE EXPIRY SCENARIOS")
    print("=" * 60)
    print()
    
    # Backup existing license if any
    backup_file = None
    if LICENSE_FILE.exists():
        backup_file = LICENSE_FILE.parent / "license_backup.json"
        import shutil
        shutil.copy(LICENSE_FILE, backup_file)
        print(f"✓ Backed up existing license to {backup_file}")
        print()
    
    try:
        # Test 1: License expires in 5 days (should not show warning)
        print("Test 1: License expires in 5 days")
        print("-" * 60)
        expires_5_days = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
        save_license("TEST-KEY-5DAYS", "Test User", expires_5_days)
        status = get_license_status()
        print(f"  Expires: {expires_5_days}")
        print(f"  Days remaining: {status.get('daysRemaining')}")
        print(f"  Valid: {status.get('valid')}")
        print(f"  Expiring soon: {status.get('expiringSoon')}")
        assert status.get('valid') == True, "License should be valid"
        assert status.get('expiringSoon') == False, "Should not be expiring soon"
        print("  ✅ PASS: No warning expected")
        print()
        
        # Test 2: License expires in 2 days (should show warning)
        print("Test 2: License expires in 2 days")
        print("-" * 60)
        expires_2_days = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
        save_license("TEST-KEY-2DAYS", "Test User", expires_2_days)
        status = get_license_status()
        print(f"  Expires: {expires_2_days}")
        print(f"  Days remaining: {status.get('daysRemaining')}")
        print(f"  Valid: {status.get('valid')}")
        print(f"  Expiring soon: {status.get('expiringSoon')}")
        assert status.get('valid') == True, "License should be valid"
        assert status.get('expiringSoon') == True, "Should be expiring soon"
        print("  ⚠️  WARNING EXPECTED: 'Lisensi Anda akan berakhir 2 hari lagi'")
        print("  ✅ PASS: Warning should be shown")
        print()
        
        # Test 3: License expires tomorrow (should show warning)
        print("Test 3: License expires tomorrow")
        print("-" * 60)
        expires_tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        save_license("TEST-KEY-TOMORROW", "Test User", expires_tomorrow)
        status = get_license_status()
        print(f"  Expires: {expires_tomorrow}")
        print(f"  Days remaining: {status.get('daysRemaining')}")
        print(f"  Valid: {status.get('valid')}")
        print(f"  Expiring soon: {status.get('expiringSoon')}")
        assert status.get('valid') == True, "License should be valid"
        assert status.get('expiringSoon') == True, "Should be expiring soon"
        print("  ⚠️  WARNING EXPECTED: 'Lisensi Anda akan berakhir besok'")
        print("  ✅ PASS: Warning should be shown")
        print()
        
        # Test 4: License expires today (should show warning)
        print("Test 4: License expires today")
        print("-" * 60)
        expires_today = date.today().strftime("%Y-%m-%d")
        save_license("TEST-KEY-TODAY", "Test User", expires_today)
        status = get_license_status()
        print(f"  Expires: {expires_today}")
        print(f"  Days remaining: {status.get('daysRemaining')}")
        print(f"  Valid: {status.get('valid')}")
        print(f"  Expiring soon: {status.get('expiringSoon')}")
        assert status.get('valid') == True, "License should be valid (expires at end of day)"
        assert status.get('expiringSoon') == True, "Should be expiring soon"
        print("  ⚠️  WARNING EXPECTED: 'Lisensi Anda akan berakhir hari ini'")
        print("  ✅ PASS: Warning should be shown")
        print()
        
        # Test 5: License expired yesterday (should trigger auto-logout)
        print("Test 5: License expired yesterday")
        print("-" * 60)
        expires_yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        save_license("TEST-KEY-EXPIRED", "Test User", expires_yesterday)
        status = get_license_status()
        print(f"  Expires: {expires_yesterday}")
        print(f"  Days remaining: {status.get('daysRemaining')}")
        print(f"  Valid: {status.get('valid')}")
        print(f"  Has error: {'error' in status}")
        if 'error' in status:
            print(f"  Error: {status.get('error')}")
        assert status.get('valid') == False, "License should be invalid"
        assert status.get('error') == "License expired", "Should have expired error"
        print("  🚪 AUTO-LOGOUT EXPECTED: 'Lisensi Anda telah berakhir'")
        print("  ✅ PASS: Auto-logout should occur")
        print()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✅")
        print("=" * 60)
        
    finally:
        # Restore backup if exists
        if backup_file and backup_file.exists():
            import shutil
            shutil.copy(backup_file, LICENSE_FILE)
            backup_file.unlink()
            print()
            print(f"✓ Restored original license from backup")
        elif LICENSE_FILE.exists():
            LICENSE_FILE.unlink()
            print()
            print(f"✓ Cleaned up test license file")

if __name__ == "__main__":
    test_license_expiry_scenarios()
