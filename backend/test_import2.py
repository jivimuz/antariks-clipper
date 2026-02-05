#!/usr/bin/env python
import sys
import logging
logging.basicConfig(level=logging.DEBUG)

sys.path.insert(0, '.')

# Import line by line to see which one fails
print("1. Importing logging...")
import logging
print("2. Importing json...")
import json
print("3. Importing subprocess...")
import subprocess
print("4. Importing tempfile...")
import tempfile
print("5. Importing Path...")
from pathlib import Path
print("6. Importing Dict, Any, List...")
from typing import Dict, Any, List
print("7. Importing WhisperModel...")
from faster_whisper import WhisperModel
print("8. Importing WHISPER_MODEL...")
from config import WHISPER_MODEL
print("9. Importing get_audio_info...")
from services.ffmpeg import get_audio_info

print("10. Now importing services.transcribe...")
import services.transcribe as t
print("11. Module loaded!")
print("Functions:", [x for x in dir(t) if not x.startswith('_')])
