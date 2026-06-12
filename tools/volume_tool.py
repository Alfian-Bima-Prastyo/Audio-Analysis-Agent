import subprocess
import re


def get_volume_info(file_path: str) -> dict:
    """Detect average and max volume (dBFS) using ffmpeg volumedetect."""
    cmd = [
        "ffmpeg", "-i", file_path,
        "-af", "volumedetect",
        "-f", "null", "-"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr

    mean = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", output)
    peak = re.search(r"max_volume:\s*([-\d.]+)\s*dB", output)

    return {
        "avg_volume_db": float(mean.group(1)) if mean else None,
        "max_volume_db": float(peak.group(1)) if peak else None,
    }


if __name__ == "__main__":
    import sys, json
    path = sys.argv[1] if len(sys.argv) > 1 else "audio_files/bad_audio.mp3"
    print(json.dumps(get_volume_info(path), indent=2))