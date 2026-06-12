import subprocess
import re


def detect_clipping(file_path: str) -> dict:
    """Detect clipping by counting samples at 0dBFS via ffmpeg histogram."""
    cmd = [
        "ffmpeg", "-i", file_path,
        "-af", "volumedetect",
        "-f", "null", "-"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr

    # histogram_0db is counts samples that hit maximum amplitude (the clipping indicator)
    match = re.search(r"histogram_0db:\s*(\d+)", output)
    clipping_samples = int(match.group(1)) if match else 0

    return {
        "clipping_detected": clipping_samples > 0,
        "clipping_sample_count": clipping_samples
    }


if __name__ == "__main__":
    import sys, json
    path = sys.argv[1] if len(sys.argv) > 1 else "audio_files/bad_audio.mp3"
    print(json.dumps(detect_clipping(path), indent=2))