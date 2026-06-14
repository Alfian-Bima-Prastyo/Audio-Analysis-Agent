import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from agent.orchestrator import run_pipeline

AUDIO_DIR = ROOT / "audio_files"
OUTPUT_DIR = ROOT / "outputs"
SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac"}


def find_audio_files(audio_dir: Path) -> list[Path]:
    """Return all audio files in the given directory with supported extensions."""
    return [f for f in audio_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS]


def process_file(file_path: Path) -> dict:
    """Run the analysis pipeline for one file, returning the report or an error entry."""
    try:
        return run_pipeline(str(file_path))
    except Exception as e:
        return {"file_name": file_path.name, "error": str(e)}


def summarize_batch(reports: list[dict]) -> dict:
    """Aggregate quality ratings and issue counts across all processed files."""
    rating_counts = {"good": 0, "fair": 0, "poor": 0}
    total_issues = 0

    for report in reports:
        if "error" in report:
            continue
        rating = report["audio_quality"]["quality_rating"]
        rating_counts[rating] = rating_counts.get(rating, 0) + 1
        total_issues += len(report["issues"])

    return {
        "total_files": len(reports),
        "rating_counts": rating_counts,
        "total_issues": total_issues,
    }


def run_batch(max_workers: int = 4) -> dict:
    """Process all audio files in audio_files folder concurrently and write aggregated results to outputs folders."""
    files = find_audio_files(AUDIO_DIR)
    reports = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, f): f for f in files}
        for future in as_completed(futures):
            reports.append(future.result())

    batch_result = {
        "summary": summarize_batch(reports),
        "reports": reports,
    }

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "batch_report.json"
    output_path.write_text(json.dumps(batch_result, indent=2))

    return batch_result


if __name__ == "__main__":
    result = run_batch()
    print(json.dumps(result["summary"], indent=2))
    print(f"\nFull report written to outputs/batch_report.json")