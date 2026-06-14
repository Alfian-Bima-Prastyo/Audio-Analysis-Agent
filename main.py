import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from agent.orchestrator import run_pipeline
from batch.processor import run_batch, AUDIO_DIR

app = FastAPI(title="Audio Analysis Agent")


@app.get("/")
def root():
    """Return API info."""
    return {"service": "audio-analysis-agent", "status": "ok"}


@app.post("/analyze")
def analyze(file_name: str):
    """Run the analysis pipeline on a single audio file in audio_files folder."""
    file_path = AUDIO_DIR / file_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_name}")

    try:
        return run_pipeline(str(file_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch")
def batch():
    """Run the analysis pipeline on all audio files in audio_files folder."""
    return run_batch()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)