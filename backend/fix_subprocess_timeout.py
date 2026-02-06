"""Script to fix ALL remaining subprocess calls with variable timeout"""
import re
from pathlib import Path

def fix_subprocess_variable_timeout(file_path: Path):
    """Fix subprocess.run calls that use variable timeout"""
    content = file_path.read_text(encoding='utf-8')
    original = content
    
    # Pattern untuk match subprocess.run dengan timeout=variable (bukan angka literal)
    pattern = r'subprocess\.run\(([^)]+), capture_output=True, text=True, timeout=timeout\)(?!.*startupinfo)'
    replacement = r'subprocess.run(\1, capture_output=True, text=True, timeout=timeout, startupinfo=get_subprocess_startup_info(), creationflags=get_subprocess_creation_flags())'
    
    content = re.sub(pattern, replacement, content)
    
    if content != original:
        file_path.write_text(content, encoding='utf-8')
        count = len(re.findall(pattern, original))
        print(f"✓ Fixed {count} subprocess calls with variable timeout in {file_path.name}")
        return True
    return False

# Fix ffmpeg.py
ffmpeg_file = Path(__file__).parent / 'services' / 'ffmpeg.py'
if ffmpeg_file.exists():
    fix_subprocess_variable_timeout(ffmpeg_file)

print("\n✅ Done!")
