# --- Audit Log Table ---
def create_audit_log_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            detail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_action(user_id, action, detail=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO audit_log (user_id, action, detail) VALUES (?, ?, ?)', (user_id, action, detail))
    conn.commit()
    conn.close()

def get_audit_logs(limit=100):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
# User and License operations
import hashlib
import uuid
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email: str, password: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    password_hash = hash_password(password)
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, email, password_hash, now))
    conn.commit()
    conn.close()
    return get_user_by_email(email)

def get_user_by_email(email: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_license(user_id: str, plan: str, expires_at: str = None, usage_limit: int = None) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    key = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT INTO licenses (key, user_id, plan, expires_at, usage_limit, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (key, user_id, plan, expires_at, usage_limit, now))
    conn.commit()
    conn.close()
    return get_license_by_key(key)

def get_license_by_key(key: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM licenses WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def increment_license_usage(key: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE licenses SET usage_count = usage_count + 1 WHERE key = ?
    """, (key,))
    conn.commit()
    conn.close()
# Analytics helpers
def count_jobs() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def count_clips() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clips")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def count_renders() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM renders")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_latest_clips(limit: int = 5) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clips ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
"""SQLite database module - manual queries without ORM"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import DB_PATH

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    # Licenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            user_id TEXT,
            plan TEXT NOT NULL,
            expires_at TEXT,
            usage_limit INTEGER,
            usage_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            source_url TEXT,
            raw_path TEXT,
            normalized_path TEXT,
            s3_url TEXT,
            status TEXT DEFAULT 'queued',
            step TEXT DEFAULT '',
            progress INTEGER DEFAULT 0,
            error TEXT,
            webhook_url TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Clips table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clips (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            start_sec REAL NOT NULL,
            end_sec REAL NOT NULL,
            score REAL DEFAULT 0,
            title TEXT,
            transcript_snippet TEXT,
            thumbnail_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)
    
    # Renders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS renders (
            id TEXT PRIMARY KEY,
            clip_id TEXT NOT NULL,
            status TEXT DEFAULT 'queued',
            progress INTEGER DEFAULT 0,
            output_path TEXT,
            options_json TEXT,
            error TEXT,
            webhook_url TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (clip_id) REFERENCES clips(id)
        )
    """)
    
    conn.commit()
    
    # Migration: Add s3_url column if it doesn't exist
    try:
        cursor.execute("SELECT s3_url FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE jobs ADD COLUMN s3_url TEXT")
        conn.commit()
    
    # Migration: Add metadata_json column to clips if it doesn't exist
    try:
        cursor.execute("SELECT metadata_json FROM clips LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE clips ADD COLUMN metadata_json TEXT")
        conn.commit()
    
    # Migration: Add caption_text column to clips if it doesn't exist
    try:
        cursor.execute("SELECT caption_text FROM clips LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE clips ADD COLUMN caption_text TEXT")
        conn.commit()
    
    # Migration: Add hashtags_text column to clips if it doesn't exist
    try:
        cursor.execute("SELECT hashtags_text FROM clips LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE clips ADD COLUMN hashtags_text TEXT")
        conn.commit()
    
    conn.close()

# Job operations
def create_job(job_id: str, source_type: str, source_url: Optional[str] = None) -> Dict[str, Any]:
    """Create a new job"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT INTO jobs (id, source_type, source_url, s3_url, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (job_id, source_type, source_url, None, now, now))
    conn.commit()
    conn.close()
    return get_job(job_id)

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_jobs(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Get all jobs with pagination"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_total_jobs_count() -> int:
    """Get total count of jobs"""
    return count_jobs()

def update_job(job_id: str, **kwargs):
    """Update job fields"""
    conn = get_connection()
    cursor = conn.cursor()
    
    kwargs['updated_at'] = datetime.utcnow().isoformat()
    fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [job_id]
    
    cursor.execute(f"UPDATE jobs SET {fields} WHERE id = ?", values)
    conn.commit()
    conn.close()

# Clip operations
def create_clip(clip_id: str, job_id: str, start_sec: float, end_sec: float, 
                score: float = 0, title: str = "", transcript_snippet: str = "",
                thumbnail_path: str = "", metadata: Optional[Dict[str, Any]] = None,
                caption_text: str = "", hashtags_text: str = "") -> Dict[str, Any]:
    """Create a new clip with optional metadata, caption and hashtags"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    metadata_json = json.dumps(metadata) if metadata else None
    
    cursor.execute("""
        INSERT INTO clips (id, job_id, start_sec, end_sec, score, title, 
                          transcript_snippet, thumbnail_path, metadata_json, 
                          caption_text, hashtags_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (clip_id, job_id, start_sec, end_sec, score, title, transcript_snippet, 
          thumbnail_path, metadata_json, caption_text, hashtags_text, now))
    
    conn.commit()
    conn.close()
    return get_clip(clip_id)

def get_clip(clip_id: str) -> Optional[Dict[str, Any]]:
    """Get clip by ID with metadata parsed"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        result = dict(row)
        if result.get('metadata_json'):
            try:
                result['metadata'] = json.loads(result['metadata_json'])
            except:
                result['metadata'] = {}
        return result
    return None

def get_clips_by_job(job_id: str) -> List[Dict[str, Any]]:
    """Get all clips for a job with metadata parsed"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clips WHERE job_id = ? ORDER BY score DESC", (job_id,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for row in rows:
        result = dict(row)
        if result.get('metadata_json'):
            try:
                result['metadata'] = json.loads(result['metadata_json'])
            except:
                result['metadata'] = {}
        results.append(result)
    return results


def delete_clip(clip_id: str) -> bool:
    """
    Delete a clip from the database
    
    Args:
        clip_id: The ID of the clip to delete
    
    Returns:
        True if deleted, False if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if clip exists
    cursor.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    # Delete the clip
    cursor.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
    conn.commit()
    conn.close()
    return True


# Render operations
def create_render(render_id: str, clip_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new render"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO renders (id, clip_id, options_json, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (render_id, clip_id, json.dumps(options), now, now))
    
    conn.commit()
    conn.close()
    return get_render(render_id)

def get_render(render_id: str) -> Optional[Dict[str, Any]]:
    """Get render by ID with file validation"""
    from pathlib import Path
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM renders WHERE id = ?", (render_id,))
    row = cursor.fetchone()
    
    if row:
        result = dict(row)
        if result.get('options_json'):
            result['options'] = json.loads(result['options_json'])
        
        # Validate file exists if status is ready
        if result.get('status') == 'ready' and result.get('output_path'):
            output_path = Path(result['output_path'])
            if not output_path.exists():
                # File missing - update status to failed
                cursor.execute(
                    "UPDATE renders SET status = ?, error = ?, updated_at = ? WHERE id = ?",
                    ('failed', 'Render file was deleted or missing', datetime.utcnow().isoformat(), render_id)
                )
                conn.commit()
                result['status'] = 'failed'
                result['error'] = 'Render file was deleted or missing'
        
        conn.close()
        return result
    
    conn.close()
    return None


def get_renders_by_clip(clip_id: str) -> List[Dict[str, Any]]:
    """Get all renders for a clip"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM renders WHERE clip_id = ? ORDER BY created_at DESC", (clip_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        if item.get('options_json'):
            item['options'] = json.loads(item['options_json'])
        result.append(item)
    return result


def list_renders() -> List[Dict[str, Any]]:
    """Get all renders from database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM renders ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        if item.get('options_json'):
            item['options'] = json.loads(item['options_json'])
        result.append(item)
    return result


def update_render(render_id: str, **kwargs):
    """Update render fields"""
    conn = get_connection()
    cursor = conn.cursor()
    
    kwargs['updated_at'] = datetime.utcnow().isoformat()
    fields = ', '.join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [render_id]
    
    cursor.execute(f"UPDATE renders SET {fields} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_render(render_id: str) -> bool:
    """Delete render record from database"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM renders WHERE id = ?", (render_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
    conn.close()

# Delete operations
def delete_job(job_id: str) -> bool:
    """Delete a job and all associated clips and renders"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Delete all renders associated with clips of this job
        cursor.execute("""
            DELETE FROM renders 
            WHERE clip_id IN (SELECT id FROM clips WHERE job_id = ?)
        """, (job_id,))
        
        # Delete all clips associated with this job
        cursor.execute("DELETE FROM clips WHERE job_id = ?", (job_id,))
        
        # Delete the job itself
        cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_renders_by_job(job_id: str) -> List[Dict[str, Any]]:
    """Get all renders for a job (via clips) with file validation"""
    from pathlib import Path
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.* FROM renders r
        INNER JOIN clips c ON r.clip_id = c.id
        WHERE c.job_id = ?
    """, (job_id,))
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        item = dict(row)
        if item.get('options_json'):
            item['options'] = json.loads(item['options_json'])
        
        # Validate file exists if status is ready
        if item.get('status') == 'ready' and item.get('output_path'):
            output_path = Path(item['output_path'])
            if not output_path.exists():
                # File missing - update status to failed
                cursor.execute(
                    "UPDATE renders SET status = ?, error = ?, updated_at = ? WHERE id = ?",
                    ('failed', 'Render file was deleted or missing', datetime.utcnow().isoformat(), item['id'])
                )
                item['status'] = 'failed'
                item['error'] = 'Render file was deleted or missing'
        
        result.append(item)
    
    conn.commit()
    conn.close()
    return result
