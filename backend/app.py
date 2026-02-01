"""FastAPI application for Antariks Clipper"""
import logging
import os
import uuid
import json
import secrets
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional, List, Dict

import stripe

import db
from db import log_action

from fastapi import (
    FastAPI, HTTPException, UploadFile, File, Form, Response,
    Request, Body, Header
)
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import RAW_DIR
from services.cloud import upload_file_to_s3
from services.jobs import submit_job, submit_render
from services.preview import generate_preview_stream, get_preview_frame
from services.license import activate_license, get_license_status, check_license_valid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Init DB
db.init_db()

# Create app (INI WAJIB ADA DI ATAS SEBELUM ROUTES)
app = FastAPI(title="Antariks Clipper API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint to verify API is running"""
    return {
        "status": "healthy",
        "service": "Antariks Clipper API",
        "version": "1.0.0"
    }


# ==================== LICENSE ENDPOINTS ====================

class LicenseActivateRequest(BaseModel):
    license_key: str

@app.post("/api/license/activate")
def license_activate(payload: LicenseActivateRequest):
    """
    Activate a license key.
    Validates with server and saves if valid.
    """
    try:
        result = activate_license(payload.license_key)
        if result.get("success"):
            logger.info(f"License activated for {result.get('owner')}")
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Invalid license key"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"License activation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/license/status")
def license_status():
    """
    Get current license status.
    Returns activation status and validity.
    """
    try:
        status = get_license_status()
        return status
    except Exception as e:
        logger.error(f"License status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# License middleware - checks license on protected endpoints
@app.middleware("http")
async def license_middleware(request: Request, call_next):
    """
    Middleware to check license validity for all API endpoints.
    Excludes license endpoints and health check.
    """
    # Skip license check for these paths
    excluded_paths = [
        "/health",
        "/api/license/activate",
        "/api/license/status",
        "/docs",
        "/redoc",
        "/openapi.json"
    ]
    
    # Check if path should be protected
    if request.url.path not in excluded_paths and request.url.path.startswith("/api/"):
        try:
            status = get_license_status()
            
            if not status.get("activated"):
                return Response(
                    content=json.dumps({"detail": "License not activated"}),
                    status_code=401,
                    media_type="application/json"
                )
            
            if not status.get("valid", False):
                return Response(
                    content=json.dumps({
                        "detail": status.get("error", "License is not valid")
                    }),
                    status_code=403,
                    media_type="application/json"
                )
        except Exception as e:
            logger.error(f"License middleware error: {e}")
            return Response(
                content=json.dumps({"detail": "License validation error"}),
                status_code=500,
                media_type="application/json"
            )
    
    response = await call_next(request)
    return response


# Password reset request and reset endpoints
import secrets
password_reset_tokens: Dict[str, str] = {}

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PaymentSessionRequest(BaseModel):
    plan: str
    email: str

# Payment: Create Stripe Checkout session
@app.post("/api/payment/create-session")
def create_payment_session(payload: PaymentSessionRequest):
    """Create a Stripe checkout session for license purchase"""
    try:
        # This is a placeholder - configure with real Stripe credentials
        # stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        logger.info(f"Payment session requested for {payload.email} - plan: {payload.plan}")
        
        # For demo purposes, return a mock session
        return {
            "session_id": f"mock_session_{secrets.token_hex(16)}",
            "url": "https://checkout.stripe.com/demo",
            "message": "Payment integration requires Stripe configuration"
        }
    except Exception as e:
        logger.error(f"Payment session creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin: List all users endpoint
@app.get("/api/admin/users")
def admin_get_users():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, created_at, is_admin FROM users")
    rows = cursor.fetchall()
    conn.close()
    users = []
    for row in rows:
        users.append({
            "id": row[0],
            "email": row[1],
            "created_at": row[2] if len(row) > 2 else None,
            "is_admin": bool(row[3]) if len(row) > 3 else False
        })
    return {"users": users}

# --- Email Utility ---
def send_email(to_email, subject, body):
    # DEMO: Configure your SMTP server here
    SMTP_SERVER = "smtp.example.com"
    SMTP_PORT = 587
    SMTP_USER = "your@email.com"
    SMTP_PASS = "yourpassword"
    from_email = SMTP_USER
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(from_email, [to_email], msg.as_string())
    except Exception as e:
        print(f"Email send failed: {e}")

@app.post("/api/password-reset/request")
def password_reset_request(payload: PasswordResetRequest):
    user = db.get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    token = secrets.token_urlsafe(24)
    password_reset_tokens[token] = user["email"]
    # Send token via email
    send_email(
        to_email=payload.email,
        subject="Your Password Reset Token",
        body=f"Your password reset token is: {token}\nIf you did not request this, please ignore."
    )
    return {"message": "Password reset token sent to your email."}

@app.post("/api/password-reset/confirm")
def password_reset_confirm(payload: PasswordResetConfirm):
    email = password_reset_tokens.get(payload.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from db import hash_password
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hash_password(payload.new_password), email))
    conn.commit()
    conn.close()
    del password_reset_tokens[payload.token]
    return {"message": "Password reset successful"}
# User: View licenses and usage
@app.get("/api/user/licenses")
def user_licenses(email: str):
    """Get all licenses and usage for a user (SaaS dashboard)"""
    user = db.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM licenses WHERE user_id = ?", (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [{k: row[k] for k in row.keys()} for row in rows]
# Admin: Deactivate/Activate License endpoint
class LicenseStatusRequest(BaseModel):
    key: str
    is_active: bool

@app.post("/api/admin/set-license-status")
def admin_set_license_status(payload: LicenseStatusRequest):
    """Admin: Deactivate or activate a license key (SaaS)"""
    lic = db.get_license_by_key(payload.key)
    if not lic:
        raise HTTPException(status_code=404, detail="License not found")
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE licenses SET is_active = ? WHERE key = ?", (1 if payload.is_active else 0, payload.key))
    conn.commit()
    conn.close()
    return {"key": payload.key, "is_active": payload.is_active}
# Admin: Create License endpoint
class LicenseCreateRequest(BaseModel):
    user_email: str
    plan: str
    expires_at: Optional[str] = None
    usage_limit: Optional[int] = None

@app.post("/api/admin/create-license")
def admin_create_license(payload: LicenseCreateRequest):
    """Admin: Create a license for a user (SaaS)"""
    user = db.get_user_by_email(payload.user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    lic = db.create_license(user_id=user["id"], plan=payload.plan, expires_at=payload.expires_at, usage_limit=payload.usage_limit)
    log_action(user["id"], "create_license", f"License created: {lic['key']}")
    return {"key": lic["key"], "plan": lic["plan"], "expires_at": lic["expires_at"], "usage_limit": lic["usage_limit"]}
# Login model
class UserLogin(BaseModel):
    email: str
    password: str

import secrets

@app.post("/api/login")
def login_user(payload: UserLogin):
    """User login (SaaS)"""
    user = db.get_user_by_email(payload.email)
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    from db import hash_password
    if user["password_hash"] != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Generate a simple session token (for demo; use JWT in production)
    token = secrets.token_hex(24)
    log_action(user["id"], "login", f"User {user['email']} logged in")
    # In production, store token in DB or use JWT
    return {"token": token, "user_id": user["id"], "email": user["email"]}
from fastapi import Body
# === AUTOMATION ENDPOINT ===
class AutomateRequest(BaseModel):
    source_type: str
    youtube_url: Optional[str] = None
    file_url: Optional[str] = None
    clips: Optional[list] = None  # List of {start_sec, end_sec, title}
    render_options: Optional[dict] = None  # face_tracking, captions, watermark_text
    webhook_url: Optional[str] = None

@app.post("/api/automate")
async def automate(
    payload: AutomateRequest = Body(...)
):
    """
    Automate: create job, create clips, render batch, and register webhook in one call.
    - source_type: 'youtube' or 'upload'
    - youtube_url or file_url (file_url: public URL to video file)
    - clips: list of {start_sec, end_sec, title}
    - render_options: dict for batch render
    - webhook_url: optional, for job/render status
    """
    import requests
    try:
        # 1. Create job
        job_id = str(uuid.uuid4())
        if payload.source_type == 'youtube':
            job = db.create_job(job_id, source_type='youtube', source_url=payload.youtube_url)
            submit_job(job_id)
        elif payload.source_type == 'upload':
            # Download file_url to RAW_DIR
            if not payload.file_url:
                raise HTTPException(status_code=400, detail='file_url required for upload')
            file_ext = Path(payload.file_url).suffix or '.mp4'
            raw_path = RAW_DIR / f"{job_id}_upload{file_ext}"
            r = requests.get(payload.file_url, stream=True)
            with open(raw_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            job = db.create_job(job_id, source_type='upload')
            db.update_job(job_id, raw_path=str(raw_path))
            submit_job(job_id)
        else:
            raise HTTPException(status_code=400, detail='Invalid source_type')

        # 2. Register webhook if provided
        if payload.webhook_url:
            db.update_job(job_id, webhook_url=payload.webhook_url)

        # 3. Wait until job.status == 'ready' (simple polling, max 60s)
        import time
        for _ in range(60):
            job = db.get_job(job_id)
            if job and job.get('status') == 'ready':
                break
            time.sleep(1)
        else:
            raise HTTPException(status_code=504, detail='Job not ready after 60s')

        # 4. Create clips if provided
        created_clips = []
        if payload.clips:
            for clip in payload.clips:
                clip_id = str(uuid.uuid4())
                db.create_clip(
                    clip_id=clip_id,
                    job_id=job_id,
                    start_sec=clip['start_sec'],
                    end_sec=clip['end_sec'],
                    score=clip.get('score', 0),
                    title=clip.get('title', ''),
                    transcript_snippet=clip.get('transcript_snippet', ''),
                    thumbnail_path=""
                )
                created_clips.append(clip_id)

        # 5. Render all clips (batch) if render_options provided
        render_ids = []
        if payload.render_options and created_clips:
            for clip_id in created_clips:
                render_id = str(uuid.uuid4())
                db.create_render(
                    render_id=render_id,
                    clip_id=clip_id,
                    options=payload.render_options
                )
                submit_render(render_id)
                render_ids.append(render_id)

        return {
            "job_id": job_id,
            "created_clips": created_clips,
            "render_ids": render_ids,
            "status": "queued"
        }
    except Exception as e:
        logger.error(f"Automate error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
# Analytics endpoint
@app.get("/api/analytics")
def get_analytics():
    """Simple analytics: total jobs, clips, renders, latest jobs/clips"""
    try:
        total_jobs = db.count_jobs()
        total_clips = db.count_clips()
        total_renders = db.count_renders()
        latest_jobs = db.get_all_jobs(limit=5)
        latest_clips = db.get_latest_clips(limit=5)
        return {
            "total_jobs": total_jobs,
            "total_clips": total_clips,
            "total_renders": total_renders,
            "latest_jobs": latest_jobs,
            "latest_clips": latest_clips
        }
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/admin/audit-logs")
def admin_audit_logs():
    return {"logs": get_audit_logs()}

# Stripe webhook for payment events (automatic license activation)
@app.post("/api/payment/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = "whsec_REPLACE_WITH_YOUR_SECRET"
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        # ...existing code...
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"error": str(e)}
    # ...existing code...

# Models
class YouTubeJobCreate(BaseModel):
    source_type: str = "youtube"
    youtube_url: str

class WebhookRegister(BaseModel):
    webhook_url: str

class ClipCreate(BaseModel):
    start_sec: float
    end_sec: float
    score: float = 0
    title: str = ""
    transcript_snippet: str = ""
    thumbnail_path: str = ""

class MultiClipCreate(BaseModel):
    clips: List[ClipCreate]

class RenderCreate(BaseModel):
    face_tracking: bool = False
    captions: bool = False
    watermark_text: str = ""

# SaaS Licensing Models
class UserRegister(BaseModel):
    email: str
    password: str

class LicenseValidateRequest(BaseModel):
    key: str

@app.post("/api/register")
def register_user(payload: UserRegister):
    """Register a new user (SaaS)"""
    if db.get_user_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = db.create_user(payload.email, payload.password)
    return {"user_id": user["id"], "email": user["email"]}

@app.post("/api/license/validate")
def validate_license(payload: LicenseValidateRequest):
    """Validate a license key (SaaS)"""
    lic = db.get_license_by_key(payload.key)
    if not lic or not lic.get("is_active"):
        raise HTTPException(status_code=401, detail="Invalid or inactive license key")
    # Optionally check expiry and usage limit
    import datetime
    if lic.get("expires_at"):
        if datetime.datetime.fromisoformat(lic["expires_at"]) < datetime.datetime.utcnow():
            raise HTTPException(status_code=403, detail="License expired")
    if lic.get("usage_limit") is not None and lic["usage_count"] >= lic["usage_limit"]:
        raise HTTPException(status_code=403, detail="License usage limit reached")
    return {"key": lic["key"], "plan": lic["plan"], "user_id": lic["user_id"]}


# Webhook registration endpoints
@app.post("/api/jobs/{job_id}/webhook")
def register_job_webhook(job_id: str, payload: WebhookRegister):
    """Register a webhook URL for job status notification"""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.update_job(job_id, webhook_url=payload.webhook_url)
    return {"job_id": job_id, "webhook_url": payload.webhook_url}

@app.post("/api/renders/{render_id}/webhook")
def register_render_webhook(render_id: str, payload: WebhookRegister):
    """Register a webhook URL for render status notification"""
    render = db.get_render(render_id)
    if not render:
        raise HTTPException(status_code=404, detail="Render not found")
    db.update_render(render_id, webhook_url=payload.webhook_url)
    return {"render_id": render_id, "webhook_url": payload.webhook_url}
# Routes
@app.post("/api/jobs/{job_id}/clips")
def create_clips(job_id: str, payload: MultiClipCreate):
    """Create multiple clips for a job"""
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        created = []
        for clip in payload.clips:
            clip_id = str(uuid.uuid4())
            new_clip = db.create_clip(
                clip_id=clip_id,
                job_id=job_id,
                start_sec=clip.start_sec,
                end_sec=clip.end_sec,
                score=clip.score,
                title=clip.title,
                transcript_snippet=clip.transcript_snippet,
                thumbnail_path=clip.thumbnail_path
            )
            created.append(new_clip)
        return {"created": created, "count": len(created)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create multi-clip error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Routes
@app.get("/")
def read_root():
    return {"message": "Antariks Clipper API", "version": "1.0.0"}


# --- SaaS Licensing: require license_key in job creation ---
from fastapi import Header

@app.post("/api/jobs")
async def create_job(
    source_type: str = Form(...),
    youtube_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    license_key: Optional[str] = Header(None, alias="X-License-Key")
):
    """
    Create a new job (requires valid license key in X-License-Key header)
    - YouTube: source_type=youtube, youtube_url=...
    - Upload: source_type=upload, file=...
    """
    # --- License check ---
    if not license_key:
        raise HTTPException(status_code=401, detail="License key required (X-License-Key header)")
    lic = db.get_license_by_key(license_key)
    if not lic or not lic.get("is_active"):
        raise HTTPException(status_code=401, detail="Invalid or inactive license key")
    import datetime
    if lic.get("expires_at"):
        if datetime.datetime.fromisoformat(lic["expires_at"]) < datetime.datetime.utcnow():
            raise HTTPException(status_code=403, detail="License expired")
    if lic.get("usage_limit") is not None and lic["usage_count"] >= lic["usage_limit"]:
        raise HTTPException(status_code=403, detail="License usage limit reached")

    try:
        job_id = str(uuid.uuid4())
        if source_type == "youtube":
            if not youtube_url:
                raise HTTPException(status_code=400, detail="youtube_url required")
            # Create job
            job = db.create_job(job_id, source_type="youtube", source_url=youtube_url)
            # Submit to background processing
            submit_job(job_id)
            db.increment_license_usage(license_key)
            log_action(lic["user_id"], "create_job", f"Job created: {job_id}")
            return {"job_id": job_id, "status": "queued"}
        elif source_type == "upload":
            if not file:
                raise HTTPException(status_code=400, detail="file required")
            # Save uploaded file locally
            file_ext = Path(file.filename).suffix if file.filename else ".mp4"
            raw_path = RAW_DIR / f"{job_id}_upload{file_ext}"
            content = await file.read()
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            with open(raw_path, "wb") as f:
                f.write(content)
            # Upload to S3
            s3_key = f"uploads/{job_id}{file_ext}"
            try:
                s3_url = upload_file_to_s3(raw_path, s3_key)
            except Exception as e:
                logger.error(f"S3 upload error: {e}")
                s3_url = None
            # Create job
            job = db.create_job(job_id, source_type="upload")
            db.update_job(job_id, raw_path=str(raw_path), s3_url=s3_url)
            # Submit to background processing
            submit_job(job_id)
            db.increment_license_usage(license_key)
            log_action(lic["user_id"], "create_job", f"Job created: {job_id}")
            return {"job_id": job_id, "status": "queued", "s3_url": s3_url}
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
def list_jobs(limit: int = 100):
    """List all jobs"""
    try:
        jobs = db.get_all_jobs(limit=limit)
        return {"jobs": jobs}
    except Exception as e:
        logger.error(f"List jobs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    """Get job details"""
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/retry")
def retry_job(job_id: str):
    """
    Retry a failed job from the last failed step.
    If files from previous steps exist, resume from there.
    """
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job['status'] not in ['failed', 'ready']:
            raise HTTPException(
                status_code=400, 
                detail=f"Can only retry failed or ready jobs. Current status: {job['status']}"
            )
        
        # Reset job status
        db.update_job(
            job_id, 
            status='queued', 
            error=None,
            progress=0
        )
        
        # Submit to background processing (will resume from appropriate step)
        submit_job(job_id)
        
        return {
            "job_id": job_id, 
            "status": "queued",
            "message": "Job requeued for processing"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry job error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}/clips")
def get_job_clips(job_id: str):
    """Get all clips for a job"""
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        clips = db.get_clips_by_job(job_id)
        return {"clips": clips}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get clips error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clips/{clip_id}/render")
def create_render(clip_id: str, options: RenderCreate):
    """Create a render job for a clip"""
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        render_id = str(uuid.uuid4())
        
        # Create render
        render = db.create_render(
            render_id=render_id,
            clip_id=clip_id,
            options=options.dict()
        )
        
        # Submit to background processing
        submit_render(render_id)
        
        return {"render_id": render_id, "status": "queued"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/renders/{render_id}")
def get_render(render_id: str):
    """Get render details"""
    try:
        render = db.get_render(render_id)
        if not render:
            raise HTTPException(status_code=404, detail="Render not found")
        return render
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get render error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/renders/{render_id}/retry")
def retry_render(render_id: str):
    """Retry a failed render"""
    try:
        render = db.get_render(render_id)
        if not render:
            raise HTTPException(status_code=404, detail="Render not found")
        
        if render['status'] not in ['failed']:
            raise HTTPException(
                status_code=400,
                detail=f"Can only retry failed renders. Current status: {render['status']}"
            )
        
        # Reset render status
        db.update_render(
            render_id,
            status='queued',
            error=None,
            progress=0
        )
        
        # Submit to background processing
        submit_render(render_id)
        
        return {
            "render_id": render_id,
            "status": "queued",
            "message": "Render requeued for processing"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/renders/{render_id}/download")
def download_render(render_id: str):
    """Download rendered video"""
    try:
        render = db.get_render(render_id)
        if not render:
            raise HTTPException(status_code=404, detail="Render not found")
        
        if render['status'] != 'ready' or not render.get('output_path'):
            raise HTTPException(status_code=400, detail="Render not ready")
        
        output_path = Path(render['output_path'])
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Render file not found")
        
        return FileResponse(
            path=str(output_path),
            media_type="video/mp4",
            filename=f"clip_{render_id}.mp4"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download render error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/thumbnails/{clip_id}")
def get_thumbnail(clip_id: str):
    """Get clip thumbnail"""
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        if not clip.get('thumbnail_path'):
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        thumbnail_path = Path(clip['thumbnail_path'])
        if not thumbnail_path.exists():
            raise HTTPException(status_code=404, detail="Thumbnail file not found")
        
        return FileResponse(
            path=str(thumbnail_path),
            media_type="image/jpeg"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get thumbnail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clips/{clip_id}/preview")
async def get_clip_preview(clip_id: str, face_tracking: bool = True):
    """
    Stream preview of clip with 9:16 crop and optional face tracking.
    Returns low-res preview video for fast playback.
    """
    preview_path = None
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        job = db.get_job(clip['job_id'])
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Use raw_path (not normalized)
        video_path = Path(job['raw_path']) if job.get('raw_path') else None
        if not video_path or not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        # Generate preview
        preview_path = generate_preview_stream(
            video_path,
            clip['start_sec'],
            clip['end_sec'],
            face_tracking=face_tracking
        )
        
        if not preview_path or not preview_path.exists():
            raise HTTPException(status_code=500, detail="Preview generation failed")
        
        # Stream the file and cleanup after
        def iterfile():
            try:
                with open(preview_path, 'rb') as f:
                    yield from f
            finally:
                # Cleanup temp file even if streaming is interrupted
                try:
                    if preview_path and preview_path.exists():
                        os.unlink(preview_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup preview file: {e}")
        
        return StreamingResponse(
            iterfile(),
            media_type="video/mp4",
            headers={"Content-Disposition": f"inline; filename=preview_{clip_id}.mp4"}
        )
        
    except HTTPException:
        # Cleanup on error
        if preview_path and preview_path.exists():
            try:
                os.unlink(preview_path)
            except Exception:
                pass
        raise
    except Exception as e:
        # Cleanup on error
        if preview_path and preview_path.exists():
            try:
                os.unlink(preview_path)
            except Exception:
                pass
        logger.error(f"Preview error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/clips/{clip_id}/preview-frame")
async def get_clip_preview_frame(clip_id: str, face_tracking: bool = True):
    """
    Get single preview frame (thumbnail) with 9:16 crop.
    """
    try:
        clip = db.get_clip(clip_id)
        if not clip:
            raise HTTPException(status_code=404, detail="Clip not found")
        
        job = db.get_job(clip['job_id'])
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        video_path = Path(job['raw_path']) if job.get('raw_path') else None
        if not video_path or not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        mid_time = (clip['start_sec'] + clip['end_sec']) / 2
        duration = clip['end_sec'] - clip['start_sec']
        
        frame_bytes = get_preview_frame(
            video_path,
            mid_time,
            face_tracking=face_tracking,
            duration=duration
        )
        
        if not frame_bytes:
            raise HTTPException(status_code=500, detail="Frame extraction failed")
        
        return Response(
            content=frame_bytes,
            media_type="image/jpeg"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview frame error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/{job_id}/render-selected")
async def render_selected_clips(
    job_id: str, 
    clip_ids: str,  # Comma-separated clip IDs from query params
    options: RenderCreate
):
    """
    Render only selected clips (batch render).
    """
    try:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Parse comma-separated clip IDs
        clip_id_list = [cid.strip() for cid in clip_ids.split(',') if cid.strip()]
        
        render_ids = []
        for clip_id in clip_id_list:
            clip = db.get_clip(clip_id)
            if not clip or clip['job_id'] != job_id:
                continue
            
            render_id = str(uuid.uuid4())
            db.create_render(
                render_id=render_id,
                clip_id=clip_id,
                options=options.dict()
            )
            submit_render(render_id)
            render_ids.append(render_id)
        
        return {
            "job_id": job_id,
            "render_ids": render_ids,
            "count": len(render_ids),
            "status": "queued"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch render error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
