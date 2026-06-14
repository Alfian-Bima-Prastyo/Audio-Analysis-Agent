from openai import OpenAI
from dotenv import load_dotenv
import os
import time
import unicodedata

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "openai/gpt-oss-120b:free"


def cleaning_text(text: str) -> str:
    """Normalize unicode characters to ASCII-friendly text."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", errors="ignore").decode("ascii")
    return text.strip()


def generate_summary(report_data: dict) -> dict:
    """Generate human-readable summary and recommendation using LLM."""

    quality = report_data["audio_quality"]
    issues = report_data.get("issues", [])
    issues_text = "\n".join(f"- {i}" for i in issues) if issues else "- No issues detected"

    prompt = f"""You are an audio quality analyst for legal deposition recordings.

Analyze the following audio metrics and provide a professional assessment:

File: {report_data['file_name']}
Duration: {report_data['duration_seconds']}s
Sample Rate: {report_data['sample_rate_hz']} Hz
Bitrate: {report_data['bitrate_kbps']} kbps
Average Volume: {quality['avg_volume_db']} dBFS
Max Volume: {quality['max_volume_db']} dBFS
Clipping Detected: {quality['clipping_detected']}
Clipping Samples: {quality['clipping_sample_count']}
Silence Ratio: {quality['silence_ratio']}
Quality Rating: {quality['quality_rating']}

Detected Issues:
{issues_text}

Respond in this exact format:
SUMMARY: [2-3 sentences assessing overall recording quality and its impact on transcription accuracy]
RECOMMENDATION: [1-2 sentences of concrete action items for the legal team]"""

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            break
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"Rate limited, retrying in 30s... (attempt {attempt + 1}/3)")
                time.sleep(30)
            else:
                raise e

    content = response.choices[0].message.content

    summary = ""
    recommendation = ""

    for line in content.splitlines():
        line = line.strip()
        line = line.strip("*").strip()
        lower = line.lower()
        if lower.startswith("summary:"):
            summary = cleaning_text(line[line.index(":")+1:])
        elif lower.startswith("recommendation:"):
            recommendation = cleaning_text(line[line.index(":")+1:])

    # fallback: if parsing fails then use raw content
    if not summary and not recommendation:
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        summary = cleaning_text(lines[0]) if lines else ""
        recommendation = cleaning_text(lines[1]) if len(lines) > 1 else ""

    return {
        "llm_summary": summary,
        "recommendation": recommendation
    }


if __name__ == "__main__":
    import json

    test_data = {
        "file_name": "bad_audio.mp3",
        "duration_seconds": 121.21,
        "sample_rate_hz": 16000,
        "bitrate_kbps": 47.2,
        "audio_quality": {
            "avg_volume_db": -16.6,
            "max_volume_db": -0.4,
            "silence_ratio": 0.32,
            "clipping_detected": True,
            "clipping_sample_count": 779,
            "quality_rating": "poor"
        },
        "issues": [
            "Clipping detected: 779 samples at 0dBFS",
            "Low bitrate: 47.2 kbps is below recommended 128 kbps",
            "Low sample rate: 16000 Hz may reduce ASR accuracy"
        ]
    }

    result = generate_summary(test_data)
    print(json.dumps(result, indent=2))