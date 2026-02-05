import db
from pathlib import Path

job = db.get_all_jobs()[0]
print(f"Job ID: {job['id']}")
print(f"Source URL: {job.get('source_url', 'N/A')}")
print(f"Raw path: {job.get('raw_path', 'N/A')}")
print(f"Status: {job['status']}")
print(f"Step: {job.get('step', 'N/A')}")

# Check file size
raw_path = job.get('raw_path')
if raw_path:
    p = Path(raw_path)
    if p.exists():
        size_mb = p.stat().st_size / 1024 / 1024
        print(f"Video size: {size_mb:.1f} MB")
    else:
        print(f"Raw file does NOT exist!")

# Reset job to failed
db.update_job(job['id'], status='failed', error='Transcription timeout - restarting with timeout fix')
print(f"\nJob reset to failed status")
