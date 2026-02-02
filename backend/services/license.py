"""License validation service for Antariks Clipper"""
import os
import json
import uuid
import httpx
from datetime import datetime, date
from pathlib import Path
from config import DATA_DIR

# License storage path
LICENSE_FILE = DATA_DIR / "license.json"

# External validation URL
LICENSE_URL = os.getenv("LICENSE_URL", "https://management.antariks.id/api/license/validate")

def _get_product_code() -> str:
    """
    Get product code - OBFUSCATED
    TIDAK BOLEH ada plain string di source code
    """
    import base64
    # Encoded product code
    encoded = 'QU5YMjAyNjAxMjhYNU4wOTI1'
    return base64.b64decode(encoded).decode('utf-8')

def get_mac_address() -> str:
    """Get MAC address of the device"""
    mac = uuid.getnode()
    mac_str = ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
    return mac_str

def load_license() -> dict | None:
    """Load saved license from storage"""
    if LICENSE_FILE.exists():
        with open(LICENSE_FILE, 'r') as f:
            return json.load(f)
    return None

def save_license(license_key: str, owner: str, expires: str) -> None:
    """Save license to storage"""
    LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "license_key": license_key,
        "owner": owner,
        "expires": expires,
        "last_validated": datetime.utcnow().isoformat()
    }
    with open(LICENSE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def is_expired(expires_str: str) -> bool:
    """Check if license is expired"""
    try:
        expires_date = datetime.strptime(expires_str, "%Y-%m-%d").date()
        return expires_date < date.today()
    except:
        return True

async def validate_license(license_key: str | None = None) -> dict:
    """
    Validate license against external server
    
    Args:
        license_key: License key to validate. If None, use saved license.
    
    Returns:
        {
            "valid": bool,
            "owner": str (if valid),
            "expires": str (if valid),
            "error": str (if error)
        }
    """
    # Get license key
    if license_key is None:
        saved = load_license()
        if saved is None:
            return {"valid": False, "error": "No license configured"}
        license_key = saved["license_key"]
    
    # Build payload with ALL THREE FIELDS
    payload = {
        "license_key": license_key,
        "product_code": _get_product_code(),  # Obfuscated
        "account": get_mac_address()
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(LICENSE_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Check response
            if data.get("valid") is True:
                expires = data.get("expires", "")
                
                # Check if expired
                if is_expired(expires):
                    return {"valid": False, "error": "License expired"}
                
                # Save license if new
                save_license(license_key, data.get("owner", ""), expires)
                
                return {
                    "valid": True,
                    "owner": data.get("owner", ""),
                    "expires": expires
                }
            else:
                return {"valid": False, "error": "Invalid license key"}
                
    except httpx.HTTPError as e:
        return {"valid": False, "error": f"Validation failed: {str(e)}"}
    except Exception as e:
        return {"valid": False, "error": f"Error: {str(e)}"}


# Legacy functions for backward compatibility
def get_license_status() -> dict:
    """
    Get current license status (synchronous wrapper for middleware).
    
    Returns:
        Dict with license status:
        - activated: bool
        - valid: bool (if activated)
        - owner: str (if valid)
        - expires: str (if valid)
        - error: str (if not valid)
    """
    saved = load_license()
    
    if not saved:
        return {"activated": False}
    
    # Check expiration date
    expires_str = saved.get("expires", "")
    if is_expired(expires_str):
        return {
            "activated": True,
            "valid": False,
            "error": "License expired"
        }
    
    # Return cached status
    return {
        "activated": True,
        "valid": True,
        "owner": saved.get("owner", "Unknown"),
        "expires": saved.get("expires", "Unknown")
    }


def check_license_valid() -> bool:
    """
    Quick check if license is valid.
    Used by middleware.
    
    Returns:
        True if license is valid, False otherwise
    """
    status = get_license_status()
    return status.get("activated") and status.get("valid", False)
