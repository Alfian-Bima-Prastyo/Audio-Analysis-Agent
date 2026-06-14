import pytest
from agent.rules import rate_quality, build_issues

def make_report(
    clipping=False,
    clipping_count=0,
    silence_ratio=0.1,
    avg_volume=-20.0,
    max_volume=-5.0,
    sample_rate=44100,
    bitrate=128.0,
    silence_segments=None,
):
    """Build a minimal report dict for testing rules."""
    return {
        "audio_quality": {
            "clipping_detected": clipping,
            "clipping_sample_count": clipping_count,
            "silence_ratio": silence_ratio,
            "avg_volume_db": avg_volume,
            "max_volume_db": max_volume,
        },
        "sample_rate_hz": sample_rate,
        "bitrate_kbps": bitrate,
        "silence_segments": silence_segments or [],
    }

class TestRateQuality:

    def test_poor_clipping(self):
        assert rate_quality(make_report(clipping=True)) == "poor"

    def test_poor_silence_ratio(self):
        assert rate_quality(make_report(silence_ratio=0.31)) == "poor"

    def test_poor_silence_ratio_boundary(self):
        assert rate_quality(make_report(silence_ratio=0.3)) != "poor"

    def test_poor_low_sample_rate(self):
        assert rate_quality(make_report(sample_rate=8000)) == "poor"

    def test_fair_low_bitrate(self):
        assert rate_quality(make_report(bitrate=48.0)) == "fair"

    def test_fair_low_volume(self):
        assert rate_quality(make_report(avg_volume=-31.0)) == "fair"

    def test_fair_silence_ratio_mid(self):
        assert rate_quality(make_report(silence_ratio=0.2)) == "fair"

    def test_fair_silence_ratio_lower_boundary(self):
        assert rate_quality(make_report(silence_ratio=0.15)) == "fair"

    def test_good_all_normal(self):
        assert rate_quality(make_report()) == "good"

    def test_poor_takes_priority_over_fair(self):
        assert rate_quality(make_report(clipping=True, bitrate=48.0)) == "poor"

class TestBuildIssues:

    def test_clipping_issue(self):
        report = make_report(clipping=True, clipping_count=779)
        issues = build_issues(report)
        assert any("779" in i for i in issues)
        assert any("0dBFS" in i for i in issues)

    def test_potential_clipping_warning(self):
        report = make_report(clipping=False, max_volume=-0.5)
        issues = build_issues(report)
        assert any("risk of clipping" in i for i in issues)

    def test_no_potential_clipping_when_confirmed(self):
        report = make_report(clipping=True, clipping_count=100, max_volume=-0.5)
        issues = build_issues(report)
        assert not any("risk of clipping" in i for i in issues)

    def test_low_bitrate_issue(self):
        report = make_report(bitrate=48.0)
        issues = build_issues(report)
        assert any("bitrate" in i.lower() for i in issues)

    def test_low_sample_rate_issue(self):
        report = make_report(sample_rate=8000)
        issues = build_issues(report)
        assert any("sample rate" in i.lower() for i in issues)

    def test_low_volume_issue(self):
        report = make_report(avg_volume=-35.0)
        issues = build_issues(report)
        assert any("volume" in i.lower() for i in issues)

    def test_long_silence_issue(self):
        segments = [{"start": 100.0, "end": 115.0, "duration": 15.0}]
        report = make_report(silence_segments=segments)
        issues = build_issues(report)
        assert any("Long silence" in i for i in issues)

    def test_short_silence_not_flagged(self):
        segments = [{"start": 10.0, "end": 18.0, "duration": 8.0}]
        report = make_report(silence_segments=segments)
        issues = build_issues(report)
        assert not any("Long silence" in i for i in issues)

    def test_no_issues_fallback(self):
        report = make_report()
        issues = build_issues(report)
        assert issues == ["No major issues detected"]

    def test_multiple_issues(self):
        report = make_report(clipping=True, clipping_count=500, bitrate=48.0)
        issues = build_issues(report)
        assert len(issues) >= 2