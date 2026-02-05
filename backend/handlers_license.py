"""License-related route handlers"""
import logging
from fastapi import HTTPException, Response
import json

from services.license import validate_license, get_license_status
from schemas import LicenseValidateRequest

logger = logging.getLogger(__name__)


async def handle_license_validation(payload: LicenseValidateRequest = None) -> dict:
    """
    Validate license and return validation result.
    
    Args:
        payload: License validation request payload
        
    Returns:
        Validation result with status, owner, expiry, and error if any
    """
    try:
        license_key = payload.license_key if payload and payload.license_key else None
        result = await validate_license(license_key)

        if not result.get("valid"):
            return result

        logger.info(f"License valid for {result.get('owner')}")
        return result

    except Exception as e:
        logger.error(f"License validation error: {e}")
        return {
            "valid": False,
            "error": f"License validation failed: {str(e)}"
        }


def get_license_middleware_response() -> tuple[bool, Response]:
    """
    Check license validity for API access.
    
    Returns:
        Tuple of (should_continue, response)
    """
    try:
        status = get_license_status()
        logger.debug(f"License check: activated={status.get('activated')}, valid={status.get('valid')}")

        if not status.get("activated"):
            response = Response(
                content=json.dumps({"detail": "License not activated. Please activate your license first."}),
                status_code=401,
                media_type="application/json"
            )
            return False, response

        if not status.get("valid"):
            response = Response(
                content=json.dumps({"detail": status.get("error", "License is invalid or expired")}),
                status_code=403,
                media_type="application/json"
            )
            return False, response

        return True, None

    except Exception as e:
        logger.error(f"License check error: {e}")
        response = Response(
            content=json.dumps({"detail": "License validation error"}),
            status_code=500,
            media_type="application/json"
        )
        return False, response
