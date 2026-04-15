"""
prompts.py – All LLM prompt builders for the Pitch Visualizer pipeline.
"""

CONSISTENCY_TEMPLATE = (
    "same team of 3 professionals, consistent appearance, "
    "same clothing, same faces, comic storyboard style, "
    "high-quality illustration"
)


# ── LLM CALL 0: Extract narrative attributes ───────────────────────────────

def build_attribute_extraction_prompt(text: str) -> list:
    return [
        {
            "role": "system",
            "content": (
                "You are a narrative analyst. Extract structured attributes from the pitch text.\n"
                "Return ONLY valid JSON (no markdown) with keys:\n"
                "  objective, num_frames (int, 3-6), main_character, environment, "
                "tone_progression (list of strings), style\n"
                'Example: {"objective":"...", "num_frames": 4, "main_character":"...", '
                '"environment":"...", "tone_progression":["hopeful","tense","triumphant"], "style":"cinematic"}'
            ),
        },
        {"role": "user", "content": f"Pitch:\n{text}"},
    ]


# ── LLM CALL 1: Generate storyboard frames ─────────────────────────────────

def build_storyboard_prompt(attributes: dict) -> list:
    scenes_hint = attributes.get("num_frames", 4)
    character = attributes.get("main_character", "a professional")
    tones = ", ".join(attributes.get("tone_progression", []))
    environment = attributes.get("environment", "modern office")
    objective = attributes.get("objective", "")

    return [
        {
            "role": "system",
            "content": (
                "You are a storyboard generator. Create a visual storyboard.\n"
                "Rules:\n"
                "- Maintain SAME characters across all frames\n"
                "- Each frame MUST have: title, subject, action, environment, emotion, tone\n"
                f"- Generate exactly {scenes_hint} frames\n"
                "Return ONLY a valid JSON array of frame objects. No markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Objective: {objective}\n"
                f"Character: {character}\n"
                f"Environment: {environment}\n"
                f"Tone progression: {tones}"
            ),
        },
    ]


# ── LLM CALL 2: Generate visual prompts (few-shot) ─────────────────────────

def build_visual_prompt_prompt(frames: list, style: str) -> list:
    frames_str = "\n".join(
        f"Frame {i+1}: title={f.get('title','')}, action={f.get('action','')}, "
        f"emotion={f.get('emotion','')}, tone={f.get('tone','')}"
        for i, f in enumerate(frames)
    )
    return [
        {
            "role": "system",
            "content": (
                "You are a visual prompt engineer for AI image generation.\n"
                "Rules:\n"
                "- Same characters across all frames\n"
                "- Reflect the tone in lighting and composition\n"
                "- Use cinematic composition\n"
                "- Include environment details\n"
                f"- End every prompt with: {CONSISTENCY_TEMPLATE}\n"
                f"- Style: {style}\n"
                "Return ONLY a valid JSON array of strings (one prompt per frame). No markdown."
            ),
        },
        {
            "role": "user",
            "content": (
                "Few-shot example:\n"
                "Frame: title=Struggle, action=team arguing\n"
                'Output: "A frustrated team in a cluttered office, dim lighting, '
                f'messy dashboards, tense expressions, {CONSISTENCY_TEMPLATE}"\n\n'
                f"Now generate for:\n{frames_str}"
            ),
        },
    ]


# ── Reviewer prompt ────────────────────────────────────────────────────────

def build_reviewer_prompt(weak_prompt: str, style: str) -> list:
    return [
        {
            "role": "system",
            "content": "Expand this brief prompt with vivid cinematic details for an AI image generator. Return only the improved prompt string.",
        },
        {"role": "user", "content": f"Style: {style}\nPrompt: {weak_prompt}"},
    ]
