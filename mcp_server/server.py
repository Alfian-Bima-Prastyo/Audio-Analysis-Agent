import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastmcp import FastMCP
from tools.ffprobe_tool import get_audio_metadata as _get_audio_metadata
from tools.silence_tool import detect_silence as _detect_silence
from tools.clipping_tool import detect_clipping as _detect_clipping

mcp = FastMCP("audio-analysis-tools")


@mcp.tool()
def get_audio_metadata(file_path: str) -> dict:
    """Extract duration, format, sample rate, bitrate, and channels from an audio file."""
    return _get_audio_metadata(file_path)


@mcp.tool()
def detect_silence(file_path: str, noise_db: int = -30, min_duration: float = 1.0) -> dict:
    """Detect silence segments in an audio file with start/end timestamps."""
    return _detect_silence(file_path, noise_db, min_duration)


@mcp.tool()
def detect_clipping(file_path: str) -> dict:
    """Detect audio clipping by checking for samples at 0dBFS."""
    return _detect_clipping(file_path)


if __name__ == "__main__":
    mcp.run()