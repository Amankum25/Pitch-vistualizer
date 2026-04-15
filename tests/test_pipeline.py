"""
test_pipeline.py – Unit tests for the pipeline logic.
Run: pytest tests/ -v
"""

import pytest
from src.app.services.pipeline import segment_text


def test_segment_text_basic():
    """Sentence splitter should return at least 3 segments from a multi-sentence pitch."""
    text = (
        "Our app helps remote teams collaborate. "
        "It uses async video updates and AI summaries. "
        "Teams report 40% fewer meetings. "
        "We have 200 beta users already."
    )
    result = segment_text(text)
    assert len(result) >= 3, f"Expected >= 3 segments, got {len(result)}"


def test_segment_text_short():
    """Short text should still produce at least 1 segment (not crash)."""
    result = segment_text("Hello world.")
    assert isinstance(result, list)
    assert len(result) >= 1


def test_segment_text_max():
    """Segmenter should not exceed max_segments."""
    text = ". ".join([f"Sentence {i}" for i in range(20)])
    result = segment_text(text, max_segments=6)
    assert len(result) <= 6


def test_panel_count_minimum():
    """Pipeline validator should require at least 3 panels."""
    from src.app.services.validator import validate_panels
    from src.app.models.job import Panel, FrameAttributes

    def make_panel(n):
        return Panel(
            scene_number=n,
            scene_text=f"Scene {n} text",
            frame=FrameAttributes(title=f"T{n}", subject="s", action="a", environment="e", emotion="happy", tone="bright"),
            enriched_prompt="A vivid cinematic scene with professionals.",
            image_url="data:image/png;base64,abc",
            caption="Caption",
        )

    # 2 panels should fail
    with pytest.raises(ValueError):
        validate_panels([make_panel(1), make_panel(2)])

    # 3 panels should pass
    result = validate_panels([make_panel(1), make_panel(2), make_panel(3)])
    assert len(result) == 3
