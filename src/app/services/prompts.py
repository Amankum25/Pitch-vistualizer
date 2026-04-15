"""
prompts.py – Robust 2-phase master prompt for the Pitch Visualizer.

PHASE 1: Intelligent scene extraction from messy input
  - No punctuation required
  - Extract: character, objective, action sequence, environment, emotion flow,
             meaning + importance per scene, entities
PHASE 2: Consistent storyboard generation
  - Strict character identity across ALL frames
  - Strict style consistency (no mixing)
  - Visual continuity + emotional progression
"""

# ── Style definitions ──────────────────────────────────────────────────────

STYLE_DESCRIPTIONS = {
    "comic":              "comic book style — bold black outlines, high contrast, expressive faces, panel-style illustration",
    "corporate minimal":  "corporate minimal illustration — clean lines, flat color palette, modern professional aesthetic",
    "cinematic":          "cinematic photography style — dramatic lighting, film grain, wide-angle composition, moody shadows",
    "flat illustration":  "flat 2D illustration — solid geometric shapes, no shadows, bright solid colors",
    "cyberpunk":          "cyberpunk digital art — neon glow, dark environment, futuristic HUD elements, rain-soaked streets",
    "watercolor":         "watercolor painting — soft brush strokes, gentle color bleeds, pastel tones, painterly texture",
    "anime":              "anime illustration style — large expressive eyes, clean linework, vibrant colors, dynamic poses",
}


def get_style_desc(style: str) -> str:
    return STYLE_DESCRIPTIONS.get(style.lower().strip(), f"{style} illustration style, consistent across all frames")


# ── STRICT identity/character injection block ───────────────────────────────

IDENTITY_RULES = (
    "STRICT CHARACTER RULES — NON-NEGOTIABLE:\n"
    "- Only ONE main character appears in every frame\n"
    "- SAME face, SAME hairstyle, SAME clothing across ALL frames\n"
    "- DO NOT change gender, age, or number of characters\n"
    "- DO NOT introduce new people\n"
    "- Character must remain visually IDENTICAL in every panel"
)

STYLE_RULES = (
    "STRICT STYLE RULES — NON-NEGOTIABLE:\n"
    "- Use ONLY the selected style — no mixing styles\n"
    "- If anime → ALL frames are anime\n"
    "- If cinematic → ALL frames are cinematic\n"
    "- DO NOT switch between animation and realism"
)


def build_image_prompt(scene: str, character_desc: str, style: str, emotion: str = "", meaning: str = "") -> str:
    """Assemble a fully structured image prompt from parts."""
    style_desc = get_style_desc(style)
    parts = [
        f"CHARACTER:\n{character_desc}",
        f"SCENE:\n{scene}",
        f"STYLE:\n{style_desc}",
    ]
    if emotion:
        parts.append(f"EMOTION:\n{emotion}")
    if meaning:
        parts.append(f"MEANING:\n{meaning}")
    parts += [
        (
            "VISUAL RULES:\n"
            "- Clear subject and action\n"
            "- Expressive emotion on character's face\n"
            "- Rich, detailed environment\n"
            "- Cinematic rule-of-thirds composition"
        ),
        IDENTITY_RULES,
        STYLE_RULES,
    ]
    return "\n\n".join(parts)


# ── MASTER PROMPT (2-phase, single call) ────────────────────────────────────

def build_master_prompt(text: str, style: str) -> list:
    style_desc = get_style_desc(style)
    return [
        {
            "role": "system",
            "content": (
                "You are an expert AI for robust narrative understanding and consistent storyboard generation.\n"
                "You operate in TWO internal phases before outputting JSON.\n\n"

                "═══════════════════════════════════════════════\n"
                "PHASE 1: INTELLIGENT SCENE EXTRACTION + MEANING\n"
                "═══════════════════════════════════════════════\n\n"

                "The input text MAY be messy (no punctuation, shorthand, informal).\n"
                "You MUST extract scenes intelligently by detecting:\n"
                "  • Change in ACTION (e.g. 'struggling' → 'found' → 'improved')\n"
                "  • Change in EMOTION (frustration → hope → achievement)\n"
                "  • Transition keywords: then, after, finally, because, until, once, so\n"
                "  • Logical story progression even without explicit markers\n\n"

                "EXTRACT these elements:\n"
                "  👤 CHARACTER — who, age, gender, consistent visual appearance (define ONCE)\n"
                "  🎯 OBJECTIVE — final outcome of the story\n"
                "  ⚙️ ACTION SEQUENCE — ordered list of key events\n"
                "  🌍 ENVIRONMENT — where each scene takes place\n"
                "  🎭 EMOTION FLOW — e.g. struggle → hope → effort → success\n"
                "  🧠 MEANING + IMPORTANCE — for EACH scene: what does it represent + why it matters\n"
                "  🏢 ENTITIES — any product / company / tool and its role in the outcome\n\n"

                "═══════════════════════════════════════════════\n"
                "PHASE 2: STORYBOARD GENERATION (STRICT RULES)\n"
                "═══════════════════════════════════════════════\n\n"

                "Generate EXACTLY 4 to 6 frames based on the story complexity. Absolute MINIMUM of 4 frames.\n\n"

                "EACH frame MUST have:\n"
                "  title    — short, evocative (max 5 words)\n"
                "  scene    — 1–2 sentences, clear visual description\n"
                "  prompt   — full structured image generation prompt (see template)\n"
                "  caption  — 1 emotional sentence that reflects the IMPORTANCE of the scene\n\n"

                "┌─────────────────────────────────────────────────┐\n"
                "│  IMAGE PROMPT TEMPLATE (follow this STRICTLY)   │\n"
                "│                                                  │\n"
                "│  CHARACTER: {same character description}         │\n"
                "│  SCENE: {scene description}                      │\n"
                "│  ACTION: {what is happening}                     │\n"
                "│  ENVIRONMENT: {location}                         │\n"
                f"│  STYLE: {style_desc[:50]}...   │\n"
                "│  EMOTION: {emotion}                              │\n"
                "│  MEANING: {what this scene represents}           │\n"
                "│  VISUAL: same character, expressive face,        │\n"
                "│          cinematic composition                   │\n"
                "│  STRICT: Do NOT change character or style        │\n"
                "└─────────────────────────────────────────────────┘\n\n"

                "GLOBAL CONSISTENCY RULES — ALL NON-NEGOTIABLE:\n\n"
                "  👤 CHARACTER CONSISTENCY:\n"
                "     • SAME face, age, gender, clothing across ALL frames\n"
                "     • Define character ONCE and copy exactly into every prompt\n"
                "     • Never add or remove people\n"
                "     • Never change gender or age\n\n"
                f"  🎨 STYLE CONSISTENCY:\n"
                f"     • Use ONLY: {style_desc}\n"
                "     • ALL frames must match — no mixing styles\n"
                "     • If animation → ALL animation. Never switch to realism.\n\n"
                "  🧬 VISUAL CONTINUITY:\n"
                "     • Smooth visual flow between frames (no random jumps)\n"
                "     • Environment evolves naturally through the story\n\n"
                "  🎭 EMOTIONAL PROGRESSION:\n"
                "     • Beginning → Middle → End structure\n"
                "     • Each frame reflects its emotion clearly\n"
                "     • Caption must feel like a human page-turn moment\n\n"
                "  ✍️ CAPTION RULES:\n"
                "     • 1 sentence only — emotionally meaningful\n"
                "     • Reflects the IMPORTANCE of the scene\n"
                "     • GOOD: 'He struggled silently, unsure if things would ever change.'\n"
                "     • BAD: 'Student studying.'\n\n"

                "OUTPUT FORMAT — return ONLY this valid JSON array (no markdown, no commentary):\n"
                "[\n"
                "  {\n"
                '    "title": "...",\n'
                '    "scene": "...",\n'
                '    "prompt": "...",\n'
                '    "caption": "...",\n'
                '    "emotion": "...",\n'
                '    "meaning": "..."\n'
                "  }\n"
                "]\n\n"
                "Also include a leading character object as the FIRST element:\n"
                "[\n"
                "  {\n"
                '    "__character__": true,\n'
                '    "description": "one sentence: who is this character",\n'
                '    "appearance": "face, hair, clothing — used in ALL prompts"\n'
                "  },\n"
                "  { ...frames... }\n"
                "]"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Story (may be messy — extract meaning intelligently):\n{text}\n\n"
                f"Visual style: {style}\n\n"
                "Generate the full storyboard JSON now. Remember: meaning + importance + consistency."
            ),
        },
    ]


# ── Reviewer prompt ─────────────────────────────────────────────────────────

def build_reviewer_prompt(weak_prompt: str, style: str) -> list:
    return [
        {
            "role": "system",
            "content": (
                "Expand this brief prompt into a rich, structured AI image generation prompt. "
                f"Style: {get_style_desc(style)}. "
                "Keep character consistent, add environment and emotion details. "
                "Return only the improved prompt string."
            ),
        },
        {"role": "user", "content": weak_prompt},
    ]
