import subprocess
import json


def get_audio_metadata(file_path: str) -> dict:
    """Extract core audio metadata from the data using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        file_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise ValueError(f"ffprobe failed: {result.stderr}")

    data = json.loads(result.stdout)
    stream = data["streams"][0]
    fmt = data["format"]

    return {
        "file_name": file_path.replace("\\", "/").split("/")[-1],
        "duration_seconds": round(float(fmt.get("duration", 0)), 2),
        "format": fmt.get("format_name", "unknown"),
        "sample_rate_hz": int(stream.get("sample_rate", 0)),
        "bitrate_kbps": round(int(fmt.get("bit_rate", 0)) / 1000, 1),
        "channels": stream.get("channels", 0),
    }


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "audio_files/bad_audio.mp3"
    print(json.dumps(get_audio_metadata(path), indent=2))