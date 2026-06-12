from typing import TypedDict
from langgraph.graph import StateGraph, END

from tools.ffprobe_tool import get_audio_metadata
from tools.volume_tool import get_volume_info
from tools.silence_tool import detect_silence
from tools.clipping_tool import detect_clipping
from llm.summarizer import generate_summary
from schemas.report import AudioReport
from agent.rules import rate_quality, build_issues


class AgentState(TypedDict):
    file_path: str
    metadata: dict
    volume: dict
    silence: dict
    clipping: dict
    report: dict


def metadata_node(state: AgentState) -> AgentState:
    """Run ffprobe to extract core audio metadata."""
    state["metadata"] = get_audio_metadata(state["file_path"])
    return state


def volume_node(state: AgentState) -> AgentState:
    """Run ffmpeg volumedetect to get average and max volume."""
    state["volume"] = get_volume_info(state["file_path"])
    return state


def silence_node(state: AgentState) -> AgentState:
    """Run ffmpeg silencedetect to find silence segments."""
    state["silence"] = detect_silence(state["file_path"])
    return state


def clipping_node(state: AgentState) -> AgentState:
    """Run ffmpeg volumedetect to check for clipping."""
    state["clipping"] = detect_clipping(state["file_path"])
    return state


def aggregate_node(state: AgentState) -> AgentState:
    """Combine all tool outputs into the fiinal structured report."""
    metadata = state["metadata"]
    volume = state["volume"]
    silence = state["silence"]
    clipping = state["clipping"]

    duration = metadata["duration_seconds"]
    silence_ratio = round(silence["total_silence_duration"] / duration, 3) if duration > 0 else 0

    report_data = {
        **metadata,
        "audio_quality": {
            "avg_volume_db": volume["avg_volume_db"],
            "max_volume_db": volume["max_volume_db"],
            "silence_ratio": silence_ratio,
            "clipping_detected": clipping["clipping_detected"],
            "clipping_sample_count": clipping["clipping_sample_count"],
            "quality_rating": "",
        },
        "silence_segments": silence["silence_segments"],
        "issues": [],
        "llm_summary": "",
        "recommendation": "",
    }

    report_data["audio_quality"]["quality_rating"] = rate_quality(report_data)
    report_data["issues"] = build_issues(report_data)

    state["report"] = report_data
    return state


def llm_node(state: AgentState) -> AgentState:
    """Generate LLM summary and recommendation."""
    llm_result = generate_summary(state["report"])
    state["report"]["llm_summary"] = llm_result["llm_summary"]
    state["report"]["recommendation"] = llm_result["recommendation"]
    return state


def build_graph():
    """Build sequential LangGraph pipeline for audio analysis."""
    graph = StateGraph(AgentState)

    graph.add_node("metadata", metadata_node)
    graph.add_node("volume", volume_node)
    graph.add_node("silence", silence_node)
    graph.add_node("clipping", clipping_node)
    graph.add_node("aggregate", aggregate_node)
    graph.add_node("llm", llm_node)

    graph.set_entry_point("metadata")
    graph.add_edge("metadata", "volume")
    graph.add_edge("volume", "silence")
    graph.add_edge("silence", "clipping")
    graph.add_edge("clipping", "aggregate")
    graph.add_edge("aggregate", "llm")
    graph.add_edge("llm", END)

    return graph.compile()


def run_pipeline(file_path: str) -> dict:
    """Run the full audio analysis pipeline and return a validated report dict."""
    graph = build_graph()
    final_state = graph.invoke({"file_path": file_path})
    validated = AudioReport(**final_state["report"])
    return validated.model_dump()


if __name__ == "__main__":
    import sys, json
    path = sys.argv[1] if len(sys.argv) > 1 else "audio_files/bad_audio.mp3"
    print(json.dumps(run_pipeline(path), indent=2))