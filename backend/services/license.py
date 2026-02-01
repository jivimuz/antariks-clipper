"""License validation service for Antariks Clipper"""
import os
import json
import base64
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
import uuid
import requests

logger = logging.getLogger(__name__)

# License storage path
LICENSE_DATA_PATH = Path(__file__).parent.parent / "data" / "license.json"

# License validation URL (configurable via env)
LICENSE_URL = os.getenv("LICENSE_URL", "https://management.antariks.id/api/license/validate")


def _get_product_code() -> str:
    """
    Get obfuscated product code.
    Product code is split and joined to avoid plain text in source.
    """
    # Obfuscated: ANX20260128X5N0925
    parts = ['ANX', '2026', '0128', 'X5N', '0925']
    return ''.join(parts)


def _get_mac_address() -> str:
    """
    Get MAC address of the device.
    Returns the first non-localhost MAC address found.
    """
    try:
        # Get the MAC address using uuid.getnode()
        mac = uuid.getnode()
        # Convert to standard MAC format
        mac_str = ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
        return mac_str
    except Exception as e:
        logger.error(f"Failed to get MAC address: {e}")
        return "UNKNOWN-MAC"


def _load_license_data() -> Optional[Dict]:
    """Load license data from storage file"""
    try:
        if LICENSE_DATA_PATH.exists():
            with open(LICENSE_DATA_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load license data: {e}")
    return None


def _save_license_data(data: Dict) -> bool:
    """Save license data to storage file"""
    try:
        # Ensure data directory exists
        LICENSE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        with open(LICENSE_DATA_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save license data: {e}")
        return False


def validate_license_with_server(license_key: str) -> Dict:
    """
    Validate license key with remote server.
    
    Args:
        license_key: The license key to validate
        
    Returns:
        Dict with validation result:
        - valid: bool
        - owner: str (if valid)
        - expires: str (if valid)
        - error: str (if error occurred)
    """
    try:
        product_code = _get_product_code()
        mac_address = _get_mac_address()
        
        payload = {
            "license_key": license_key,
            "product_code": product_code,
            "account": mac_address
        }
        
        logger.info(f"Validating license with server: {LICENSE_URL}")
        response = requests.post(
            LICENSE_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("valid"):
                return {
                    "valid": True,
                    "owner": data.get("owner", "Unknown"),
                    "expires": data.get("expires", "Unknown")
                }
            else:
                return {
                    "valid": False,
                    "error": "Invalid license key"
                }
        else:
            logger.error(f"License validation failed: HTTP {response.status_code}")
            return {
                "valid": False,
                "error": f"License validation failed: HTTP {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        logger.error("License validation timeout")
        return {
            "valid": False,
            "error": "License validation failed: Request timeout"
        }
    except requests.exceptions.ConnectionError:
        logger.error("License validation connection error")
        return {
            "valid": False,
            "error": "License validation failed: Connection error"
        }
    except Exception as e:
        logger.error(f"License validation error: {e}")
        return {
            "valid": False,
            "error": f"License validation failed: {str(e)}"
        }


def activate_license(license_key: str) -> Dict:
    """
    Activate a license key.
    Validates with server and saves if valid.
    
    Returns:
        Dict with activation result
    """
    # Validate with server
    result = validate_license_with_server(license_key)
    
    if result.get("valid"):
        # Save license data
        license_data = {
            "license_key": license_key,
            "owner": result.get("owner"),
            "expires": result.get("expires"),
            "last_validated": datetime.now().isoformat(),
            "activated_at": datetime.now().isoformat()
        }
        
        if _save_license_data(license_data):
            logger.info(f"License activated successfully for {result.get('owner')}")
            return {
                "success": True,
                "owner": result.get("owner"),
                "expires": result.get("expires")
            }
        else:
            return {
                "success": False,
                "error": "Failed to save license data"
            }
    else:
        return {
            "success": False,
            "error": result.get("error", "Invalid license key")
        }


def get_license_status() -> Dict:
    """
    Get current license status.
    Checks cache and re-validates if needed.
    
    Returns:
        Dict with license status:
        - activated: bool
        - valid: bool (if activated)
        - owner: str (if valid)
        - expires: str (if valid)
        - needs_validation: bool (if cache expired)
    """
    license_data = _load_license_data()
    
    if not license_data:
        return {"activated": False}
    
    # Check if cache is expired (24 hours)
    try:
        last_validated = datetime.fromisoformat(license_data.get("last_validated", ""))
        cache_age = datetime.now() - last_validated
        
        # Re-validate if cache is older than 24 hours
        if cache_age > timedelta(hours=24):
            logger.info("License cache expired, re-validating...")
            result = validate_license_with_server(license_data["license_key"])
            
            if result.get("valid"):
                # Update cache
                license_data["owner"] = result.get("owner")
                license_data["expires"] = result.get("expires")
                license_data["last_validated"] = datetime.now().isoformat()
                _save_license_data(license_data)
            else:
                # Validation failed
                return {
                    "activated": True,
                    "valid": False,
                    "error": result.get("error", "License validation failed")
                }
    except Exception as e:
        logger.error(f"Error checking license cache: {e}")
    
    # Return cached status
    return {
        "activated": True,
        "valid": True,
        "owner": license_data.get("owner", "Unknown"),
        "expires": license_data.get("expires", "Unknown")
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
