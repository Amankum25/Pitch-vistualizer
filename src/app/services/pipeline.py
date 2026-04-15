"""
pipeline.py – Main orchestrator for the Pitch Visualizer.

Flow:
  1. segment_text(text)              → basic scenes
  2. extract_attributes(text)        → Groq LLM call 0
  3. generate_storyboard_llm(attrs)  → Groq LLM call 1
  4. generate_prompts_llm(frames)    → Groq LLM call 2 (few-shot)
  5. generate_images(prompts)        → MiniMax (parallel)
  6. store_image(img) per panel      → Cloudinary or inline
  7. build_panels(frames, images)    → Panel objects
  8. export_html_storyboard(panels)  → storyboard_<id>.html
  9. return StoryboardResponse
"""

import asyncio
import json
import uuid
import logging
from src.app.services.groq_client import groq_client
from src.app.services.prompts import (
    build_attribute_extraction_prompt,
    build_storyboard_prompt,
    build_visual_prompt_prompt,
)
from src.app.services.image_generator import generate_images
from src.app.services.storage_service import store_image
from src.app.services.html_exporter import export_html_storyboard
from src.app.services.reviewer import review_prompt
from src.app.services.validator import validate_panels
from src.app.models.job import (
    Panel, FrameAttributes, NarrativeAttributes, StoryboardResponse
)

logger = logging.getLogger(__name__)


def _parse_json_safe(raw: str, fallback):
    """Strip markdown fences and parse JSON."""
    text = raw.strip()
    for fence in ("```json", "```"):
        if text.startswith(fence):
            text = text.split(fence, 1)[-1]
            if "```" in text:
                text = text.rsplit("```", 1)[0]
            text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}\nRaw text: {text[:500]}")
        return fallback


def segment_text(text: str, max_segments: int = 6) -> list[str]:
    """Simple sentence/paragraph splitter as initial segmentation."""
    import re
    # Split on sentence boundaries or newlines
    parts = re.split(r'(?<=[.!?])\s+|\n{2,}', text.strip())
    parts = [p.strip() for p in parts if p.strip()]
    # If very few parts, try newline split
    if len(parts) < 3:
        parts = [p.strip() for p in text.split('\n') if p.strip()]
    if len(parts) < 3:
        # Last resort: split by period
        parts = [p.strip() + '.' for p in text.split('.') if p.strip()]
    return parts[:max_segments] if len(parts) > max_segments else parts


async def process_storyboard(text: str, style: str) -> StoryboardResponse:
    storyboard_id = str(uuid.uuid4())[:8]

    # ─── Step 1: Segment text ───────────────────────────────────────────────
    scenes = segment_text(text)
    logger.info(f"[{storyboard_id}] Segmented into {len(scenes)} scenes")

    # ─── Step 2: Extract narrative attributes (Groq Call 0) ─────────────────
    attr_raw = await groq_client.complete(build_attribute_extraction_prompt(text))
    attrs = _parse_json_safe(attr_raw, {
        "objective": text[:80],
        "num_frames": max(3, len(scenes)),
        "main_character": "a professional",
        "environment": "modern setting",
        "tone_progression": ["hopeful", "determined", "triumphant"],
        "style": style,
    })
    attrs["style"] = style  # Always use user-selected style
    logger.info(f"[{storyboard_id}] Attributes extracted: {attrs}")

    # ─── Step 3: Generate storyboard frames (Groq Call 1) ───────────────────
    frames_raw = await groq_client.complete(build_storyboard_prompt(attrs))
    frames = _parse_json_safe(frames_raw, [])
    if not frames:
        # Fallback frames from scenes
        frames = [
            {"title": f"Scene {i+1}", "subject": s[:40], "action": s, "environment": attrs.get("environment",""), "emotion": "neutral", "tone": "neutral"}
            for i, s in enumerate(scenes)
        ]
    logger.info(f"[{storyboard_id}] Generated {len(frames)} storyboard frames")

    # Ensure minimum 3 frames
    while len(frames) < 3:
        frames.append(frames[-1] if frames else {"title": "Scene", "subject": text[:40], "action": text, "environment": "", "emotion": "neutral", "tone": "neutral"})

    # ─── Step 4: Generate visual prompts (Groq Call 2, few-shot) ────────────
    prompts_raw = await groq_client.complete(build_visual_prompt_prompt(frames, style))
    prompts = _parse_json_safe(prompts_raw, [])
    if not isinstance(prompts, list) or not prompts:
        prompts = [f"{f.get('action','scene')} in {f.get('environment','modern setting')}, {style} style" for f in frames]

    # Align prompts to frame count
    while len(prompts) < len(frames):
        prompts.append(prompts[-1] if prompts else style)

    # ─── Step 4b: Review weak prompts ───────────────────────────────────────
    prompts = await asyncio.gather(*[review_prompt(p, style) for p in prompts])

    # ─── Step 5: Generate images in parallel (MiniMax) ──────────────────────
    logger.info(f"[{storyboard_id}] Generating {len(prompts)} images via MiniMax...")
    images = await generate_images(list(prompts))

    # ─── Step 6: Store images (Cloudinary or inline) ────────────────────────
    images = list(await asyncio.gather(*[store_image(img) for img in images]))

    # ─── Step 7: Build panels ────────────────────────────────────────────────
    panels: list[Panel] = []
    for i, frame in enumerate(frames):
        scene_text = scenes[i] if i < len(scenes) else frame.get("action", "")
        caption_words = scene_text.split()[:12]
        caption = " ".join(caption_words) + ("..." if len(scene_text.split()) > 12 else "")

        panel = Panel(
            scene_number=i + 1,
            scene_text=scene_text,
            frame=FrameAttributes(
                title=frame.get("title", f"Scene {i+1}"),
                subject=frame.get("subject", ""),
                action=frame.get("action", ""),
                environment=frame.get("environment", ""),
                emotion=frame.get("emotion", "neutral"),
                tone=frame.get("tone", "neutral"),
            ),
            enriched_prompt=prompts[i],
            image_url=images[i] if i < len(images) else "",
            caption=caption,
        )
        panels.append(panel)

    # ─── Step 8: Validate ────────────────────────────────────────────────────
    panels = validate_panels(panels)

    # ─── Step 9: Export HTML ─────────────────────────────────────────────────
    panels_dicts = [p.model_dump() for p in panels]
    html_path = export_html_storyboard(panels_dicts, storyboard_id)
    logger.info(f"[{storyboard_id}] HTML exported → {html_path}")

    return StoryboardResponse(
        panels=panels,
        style=style,
        total_panels=len(panels),
        html_download_url=f"/api/v1/storyboard/{storyboard_id}",
    )
