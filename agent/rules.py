def rate_quality(report_data: dict) -> str:
    """Determine overall audio quality rating based on metrics."""
    quality = report_data["audio_quality"]

    if quality["clipping_detected"]:
        return "poor"
    if quality["silence_ratio"] > 0.3:
        return "poor"
    if report_data["sample_rate_hz"] < 16000:
        return "poor"
    if report_data["bitrate_kbps"] < 64:
        return "fair"
    if quality["avg_volume_db"] is not None and quality["avg_volume_db"] < -30:
        return "fair"
    if 0.15 <= quality["silence_ratio"] <= 0.3:
        return "fair"

    return "good"


def build_issues(report_data: dict, long_silence_threshold: float = 10.0) -> list[str]:
    """Generate human readable issue descriptions based on audio metrics."""
    quality = report_data["audio_quality"]
    issues = []

    if quality["clipping_detected"]:
        n = quality["clipping_sample_count"]
        issues.append(f"Clipping detected: {n} samples at 0dBFS")

    if report_data["bitrate_kbps"] < 64:
        bitrate = report_data["bitrate_kbps"]
        issues.append(f"Low bitrate: {bitrate} kbps is below recommended 128 kbps")

    if report_data["sample_rate_hz"] < 16000:
        rate = report_data["sample_rate_hz"]
        issues.append(f"Low sample rate: {rate} Hz may reduce ASR accuracy")

    if quality["avg_volume_db"] is not None and quality["avg_volume_db"] < -30:
        vol = quality["avg_volume_db"]
        issues.append(f"Low average volume: {vol} dBFS may affect transcription accuracy")

    for segment in report_data.get("silence_segments", []):
        if segment["duration"] >= long_silence_threshold:
            start, end = segment["start"], segment["end"]
            issues.append(f"Long silence detected between {start}-{end}s")

    if not issues:
        issues.append("No major issues detected")

    return issues