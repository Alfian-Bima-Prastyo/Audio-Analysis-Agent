import subprocess
import re


def detect_silence(file_path: str, noise_db: int = -30, min_duration: float = 1.0) -> dict:
    """Detect silence segments with timestamps using ffmpeg silencedetect."""
    cmd = [
        "ffmpeg", "-i", file_path,
        "-af", f"silencedetect=n={noise_db}dB:d={min_duration}",
        "-f", "null", "-"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr

    starts = re.findall(r"silence_start:\s*([\d.]+)", output)
    ends = re.findall(r"silence_end:\s*([\d.]+)", output)
    durations = re.findall(r"silence_duration:\s*([\d.]+)", output)

    segments = []
    for s, e, d in zip(starts, ends, durations):
        if not s or not e:
            continue
        segments.append({
            "start": round(float(s), 2),
            "end": round(float(e), 2),
            "duration": round(float(d), 2)
        })

    total_silence = sum(float(d) for d in durations)

    return {
        "silence_segments": segments,
        "total_silence_duration": round(total_silence, 2),
        "silence_count": len(segments)
    }


if __name__ == "__main__":
    import sys, json
    path = sys.argv[1] if len(sys.argv) > 1 else "audio_files/bad_audio.mp3"
    print(json.dumps(detect_silence(path), indent=2))