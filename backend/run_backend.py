"""Backend entrypoint for packaged builds (PyInstaller)."""
import sys
import uvicorn
from app import app as fastapi_app

if __name__ == "__main__":
    # Disable uvicorn's default logging config for packaged builds
    # This prevents "AttributeError: 'NoneType' object has no attribute 'isatty'"
    # when running without a console window
    uvicorn.run(
        fastapi_app, 
        host="127.0.0.1", 
        port=3211,
        log_config=None  # Disable default logging config
    )
