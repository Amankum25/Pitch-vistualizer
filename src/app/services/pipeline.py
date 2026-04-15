"""
pipeline.py – Optimized orchestrator using:
  - SINGLE LLM call (master prompt returns character + frames + prompts + captions)
  - PARALLEL LLM via race pattern (5 keys compete, fastest wins)
  - PARALLEL MiniMax image generation
Target latency: ≤ 20-30 seconds
"""

import asyncio
import json
import uuid
import logging
from src.app.services.groq_client import groq_client
from src.app.services.prompts import build_master_prompt, build_image_prompt, build_reviewer_prompt
from src.app.services.image_generator import generate_images
from src.app.services.storage_service import store_image
from src.app.services.html_exporter import export_html_storyboard
from src.app.services.validator import validate_panels
from src.app.models.job import Panel, FrameAttributes, StoryboardResponse

logger = logging.getLogger(__name__)


def _parse_json_safe(raw: str) -> dict | None:
    text = raw.strip()
    # Strip markdown fences if LLM added them
    for fence in ("```json", "```"):
        if text.startswith(fence):
            text = text.split(fence, 1)[-1]
            if "```" in text:
                text = text.rsplit("```", 1)[0]
            text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e} | Raw snippet: {text[:300]}")
        return None


async def process_storyboard(text: str, style: str) -> StoryboardResponse:
    storyboard_id = str(uuid.uuid4())[:8]
    logger.info(f"[{storyboard_id}] Starting pipeline | style={style}")

    # ─── STEP 1: Single LLM call (parallel race across 5 keys) ─────────────
    # parallel_complete fires to all 5 Groq keys simultaneously — fastest wins
    messages = build_master_prompt(text, style)
    logger.info(f"[{storyboard_id}] Firing master LLM call (parallel race, 5 keys)...")
    raw = await groq_client.parallel_complete(messages)

    parsed = _parse_json_safe(raw)

    # ─── Parse new array format: [{"__character__": true, ...}, {frame}, ...] ─
    character_desc = "one person, consistent appearance"
    frames = []

    if isinstance(parsed, list) and len(parsed) > 0:
        # New format: array with optional leading __character__ object
        char_obj = parsed[0] if parsed[0].get("__character__") else None
        if char_obj:
            character_desc = (
                char_obj.get("appearance") or
                char_obj.get("description") or
                character_desc
            )
            frames = [f for f in parsed[1:] if not f.get("__character__")]
        else:
            frames = [f for f in parsed if not f.get("__character__")]

    elif isinstance(parsed, dict):
        # Legacy dict format fallback
        character_desc = parsed.get("character", {}).get("description", character_desc)
        frames = parsed.get("frames", [])

    # ─── Hard fallback if still empty ────────────────────────────────────────
    if not frames:
        logger.warning(f"[{storyboard_id}] Malformed LLM output, using fallback frames.")
        import re
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\bthen\b|\bafter\b|\bfinally\b', text, flags=re.IGNORECASE) if len(s.strip()) > 8]
        while len(sentences) < 3:
            sentences.append(sentences[-1] if sentences else text)
        frames = [
            {"title": f"Scene {i+1}", "scene": s, "prompt": s, "caption": s[:80], "emotion": "neutral", "meaning": "story moment"}
            for i, s in enumerate(sentences[:5])
        ]

    # Ensure minimum 3 frames
    while len(frames) < 3:
        frames.append(frames[-1])

    logger.info(f"[{storyboard_id}] Got {len(frames)} frames. Character: {character_desc}")

    # ─── STEP 2: Enrich image prompts with strict identity + style ──────────
    enriched_prompts = [
        build_image_prompt(
            # new format uses "prompt" key; old format used "image_prompt" or "scene"
            scene=f.get("prompt") or f.get("image_prompt") or f.get("scene", ""),
            character_desc=character_desc,
            style=style,
            emotion=f.get("emotion", ""),
            meaning=f.get("meaning", ""),
        )
        for f in frames
    ]

    # ─── STEP 3: Parallel MiniMax image generation ──────────────────────────
    logger.info(f"[{storyboard_id}] Generating {len(enriched_prompts)} images in parallel...")
    images = await generate_images(enriched_prompts)

    # ─── STEP 4: Optional storage (Cloudinary or inline) ────────────────────
    images = list(await asyncio.gather(*[store_image(img) for img in images]))

    # ─── STEP 5: Assemble panels ─────────────────────────────────────────────
    panels: list[Panel] = []
    for i, frame in enumerate(frames):
        panel = Panel(
            scene_number=i + 1,
            scene_text=frame.get("scene", ""),
            frame=FrameAttributes(
                title=frame.get("title", f"Frame {i+1}"),
                subject=character_desc,
                action=frame.get("scene", ""),
                environment="",
                emotion=frame.get("emotion", ""),
                tone=frame.get("meaning", ""),
            ),
            enriched_prompt=enriched_prompts[i],
            image_url=images[i] if i < len(images) else "",
            caption=frame.get("caption", frame.get("scene", "")[:80]),
        )
        panels.append(panel)

    # ─── STEP 6: Validate ────────────────────────────────────────────────────
    panels = validate_panels(panels)

    # ─── STEP 7: Export HTML ─────────────────────────────────────────────────
    panels_dicts = [p.model_dump() for p in panels]
    html_path = export_html_storyboard(panels_dicts, storyboard_id)
    logger.info(f"[{storyboard_id}] HTML exported → {html_path}")

    return StoryboardResponse(
        panels=panels,
        style=style,
        total_panels=len(panels),
        html_download_url=f"/api/v1/storyboard/{storyboard_id}",
    )
