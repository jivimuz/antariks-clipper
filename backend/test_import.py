#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

try:
    print("Attempting to import services.transcribe...")
    import services.transcribe as t
    print("Module loaded successfully!")
    print("Functions:", [x for x in dir(t) if not x.startswith('_')])
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
