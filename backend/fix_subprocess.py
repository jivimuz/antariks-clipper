"""Script to add hidden console flags to all subprocess calls"""
import re
from pathlib import Path

def fix_subprocess_in_file(file_path: Path):
    """Add startupinfo and creationflags to subprocess.run calls"""
    content = file_path.read_text(encoding='utf-8')
    original = content
    changes = 0
    
    # Pattern 1: Match subprocess.run with timeout but without startupinfo
    pattern1 = r'subprocess\.run\(([^)]+), capture_output=True, text=True, timeout=(\d+)\)(?!\s*,\s*startupinfo)'
    replacement1 = r'subprocess.run(\1, capture_output=True, text=True, timeout=\2, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())'
    content, count1 = re.subn(pattern1, replacement1, content)
    changes += count1
    
    # Pattern 2: Match subprocess.run without timeout and without startupinfo
    pattern2 = r'subprocess\.run\(([^)]+), capture_output=True, text=True\)(?!\s*,\s*startupinfo)(?!\s*,\s*timeout)'
    replacement2 = r'subprocess.run(\1, capture_output=True, text=True, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())'
    content, count2 = re.subn(pattern2, replacement2, content)
    changes += count2
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        print(f"✓ Fixed {changes} subprocess calls in {file_path}")
        return True
    else:
        print(f"- No changes needed in {file_path}")
        return False

# Fix all service files
service_dir = Path(__file__).parent / 'services'
files_to_fix = [
    'ffmpeg.py',
    'transcribe.py', 
    'preview.py',
    'downloader.py'
]

fixed_count = 0
for filename in files_to_fix:
    file_path = service_dir / filename
    if file_path.exists():
        if fix_subprocess_in_file(file_path):
            fixed_count += 1

print(f"\n✅ Done! Fixed {fixed_count} files.")

