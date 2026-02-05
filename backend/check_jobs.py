import db

jobs = db.get_all_jobs()
print(f'Total jobs: {len(jobs)}')
print("\nLast 5 jobs:")
for job in jobs[-5:]:
    print(f"  ID: {job['id'][:8]}")
    print(f"    Status: {job['status']}")
    print(f"    Step: {job.get('step', 'N/A')}")
    print(f"    Progress: {job.get('progress', 0)}%")
    print()
