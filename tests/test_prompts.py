"""
test_prompts.py – Unit tests for prompt builder functions.
Run: pytest tests/ -v
"""

from src.app.services.prompts import (
    build_attribute_extraction_prompt,
    build_storyboard_prompt,
    build_visual_prompt_prompt,
    CONSISTENCY_TEMPLATE,
)


def test_attribute_prompt_not_empty():
    """Attribute extraction prompt should contain the pitch text."""
    msgs = build_attribute_extraction_prompt("Our app solves remote team collaboration.")
    assert any("Our app" in str(m.get("content", "")) for m in msgs)


def test_storyboard_prompt_contains_character():
    """Storyboard prompt should reference the main character."""
    attrs = {
        "objective": "show product value",
        "num_frames": 3,
        "main_character": "Alice the developer",
        "environment": "startup office",
        "tone_progression": ["hopeful", "tense", "triumphant"],
        "style": "comic",
    }
    msgs = build_storyboard_prompt(attrs)
    full = " ".join(str(m.get("content", "")) for m in msgs)
    assert "Alice the developer" in full


def test_visual_prompt_style_injection():
    """Visual prompt builder should include the selected style."""
    frames = [
        {"title": "Start", "action": "team discusses", "emotion": "hopeful", "tone": "bright"},
        {"title": "Struggle", "action": "team debates", "emotion": "tense", "tone": "dark"},
        {"title": "Victory", "action": "team celebrates", "emotion": "joyful", "tone": "vibrant"},
    ]
    msgs = build_visual_prompt_prompt(frames, "cyberpunk")
    full = " ".join(str(m.get("content", "")) for m in msgs)
    assert "cyberpunk" in full.lower()


def test_consistency_template_in_visual_prompt():
    """Consistency template should be embedded in the visual prompt instructions."""
    frames = [{"title": "T", "action": "a", "emotion": "happy", "tone": "bright"}]
    msgs = build_visual_prompt_prompt(frames, "comic")
    full = " ".join(str(m.get("content", "")) for m in msgs)
    assert "consistent" in full.lower()
