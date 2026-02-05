import sys
import traceback

print("Step 1: Attempting to import services.transcribe...")
try:
    import services.transcribe as t
    print("Step 2: Module loaded")
    print("Step 3: Available functions:", [x for x in dir(t) if not x.startswith('_')])
    print("Step 4: Trying to get transcribe_video...")
    fn = getattr(t, 'transcribe_video', None)
    print("Step 5: Function found:", fn)
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
