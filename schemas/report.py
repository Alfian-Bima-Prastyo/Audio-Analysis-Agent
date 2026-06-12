from pydantic import BaseModel
from typing import Optional


class SilenceSegment(BaseModel):
    start: float
    end: float
    duration: float


class AudioQuality(BaseModel):
    avg_volume_db: Optional[float]
    max_volume_db: Optional[float]
    silence_ratio: float
    clipping_detected: bool
    clipping_sample_count: int
    quality_rating: str  # good / fair / poor


class AudioReport(BaseModel):
    file_name: str
    duration_seconds: float
    format: str
    sample_rate_hz: int
    bitrate_kbps: float
    channels: int
    audio_quality: AudioQuality
    silence_segments: list[SilenceSegment]
    issues: list[str]
    llm_summary: str = ""
    recommendation: str = ""