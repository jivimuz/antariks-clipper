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
    
    # Jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            source_url TEXT,
            raw_path TEXT,
            normalized_path TEXT,
            status TEXT DEFAULT 'queued',
            step TEXT DEFAULT '',
            progress INTEGER DEFAULT 0,
            error TEXT,
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
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (clip_id) REFERENCES clips(id)
        )
    """)
    
    conn.commit()
    conn.close()

# Job operations
def create_job(job_id: str, source_type: str, source_url: Optional[str] = None) -> Dict[str, Any]:
    """Create a new job"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO jobs (id, source_type, source_url, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (job_id, source_type, source_url, now, now))
    
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

def get_all_jobs(limit: int = 100) -> List[Dict[str, Any]]:
    """Get all jobs"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

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
                thumbnail_path: str = "") -> Dict[str, Any]:
    """Create a new clip"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO clips (id, job_id, start_sec, end_sec, score, title, 
                          transcript_snippet, thumbnail_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (clip_id, job_id, start_sec, end_sec, score, title, transcript_snippet, 
          thumbnail_path, now))
    
    conn.commit()
    conn.close()
    return get_clip(clip_id)

def get_clip(clip_id: str) -> Optional[Dict[str, Any]]:
    """Get clip by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_clips_by_job(job_id: str) -> List[Dict[str, Any]]:
    """Get all clips for a job"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clips WHERE job_id = ? ORDER BY score DESC", (job_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

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
    """Get render by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM renders WHERE id = ?", (render_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        result = dict(row)
        if result.get('options_json'):
            result['options'] = json.loads(result['options_json'])
        return result
    return None

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
