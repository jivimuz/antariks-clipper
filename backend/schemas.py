"""Request/Response schemas for API endpoints"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


# License schemas
class LicenseValidateRequest(BaseModel):
    """Request schema for license validation"""
    license_key: Optional[str] = None


# Webhook schemas
class WebhookRegister(BaseModel):
    """Request schema for webhook registration"""
    webhook_url: str


# Clip schemas
class ClipCreate(BaseModel):
    """Request schema for creating a clip"""
    start_sec: float
    end_sec: float
    score: float = 0
    title: str = ""
    transcript_snippet: str = ""
    thumbnail_path: str = ""


class MultiClipCreate(BaseModel):
    """Request schema for creating multiple clips"""
    clips: List[ClipCreate]


# Render schemas
class RenderCreate(BaseModel):
    """Request schema for creating a render"""
    face_tracking: bool = False
    smart_crop: bool = False
    captions: bool = False
    watermark_text: str = ""


# Job schemas
class YouTubeJobCreate(BaseModel):
    """Request schema for YouTube job creation"""
    source_type: str = "youtube"
    youtube_url: str


class AutomateRequest(BaseModel):
    """Request schema for automation endpoint"""
    source_type: str
    youtube_url: Optional[str] = None
    file_url: Optional[str] = None
    clips: Optional[list] = None
    render_options: Optional[dict] = None
    webhook_url: Optional[str] = None


class RegenerateHighlightsRequest(BaseModel):
    """Request schema for regenerating highlights"""
    clip_count: Optional[int] = None
    adaptive: bool = True
