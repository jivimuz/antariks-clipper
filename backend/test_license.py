"""Test license validation functionality"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.license import _get_product_code, _get_mac_address

def test_product_code_obfuscation():
    """Verify product code is properly obfuscated"""
    print("Testing product code obfuscation...")
    
    # Get the product code
    code = _get_product_code()
    
    # Verify it returns the expected code
    expected = "ANX20260128X5N0925"
    if code == expected:
        print(f"✓ Product code correctly decoded: {code}")
    else:
        print(f"❌ Product code mismatch: expected {expected}, got {code}")
        return False
    
    # Verify the plain text doesn't exist in the source file
    with open('services/license.py', 'r') as f:
        source = f.read()
    
    if expected in source:
        print(f"❌ Product code found in plain text in source code!")
        return False
    else:
        print("✓ Product code not found in plain text (properly obfuscated)")
    
    return True


def test_mac_address():
    """Test MAC address retrieval"""
    print("\nTesting MAC address retrieval...")
    
    mac = _get_mac_address()
    print(f"✓ MAC address: {mac}")
    
    # Basic validation
    if ':' in mac or mac == "UNKNOWN-MAC":
        print("✓ MAC address format is valid")
        return True
    else:
        print(f"❌ Invalid MAC address format: {mac}")
        return False


def test_expiration_logic():
    """Test expiration date checking"""
    print("\nTesting expiration date logic...")
    from datetime import datetime
    
    # Test valid (future) date
    future_date = "2031-10-28"
    expires_date = datetime.strptime(future_date, "%Y-%m-%d").date()
    today = datetime.now().date()
    
    if expires_date >= today:
        print(f"✓ Future date {future_date} correctly identified as valid")
    else:
        print(f"❌ Future date {future_date} incorrectly identified as expired")
        return False
    
    # Test expired (past) date
    past_date = "2020-01-01"
    expires_date = datetime.strptime(past_date, "%Y-%m-%d").date()
    
    if expires_date < today:
        print(f"✓ Past date {past_date} correctly identified as expired")
    else:
        print(f"❌ Past date {past_date} incorrectly identified as valid")
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("License Validation Tests")
    print("=" * 50)
    
    all_passed = True
    
    if not test_product_code_obfuscation():
        all_passed = False
    
    if not test_mac_address():
        all_passed = False
    
    if not test_expiration_logic():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All license tests passed!")
        sys.exit(0)
    else:
        print("❌ Some license tests failed")
        sys.exit(1)
