"""
image_generator.py – MiniMax image generation with MOCK_IMAGES mode.

Set MOCK_IMAGES=true in .env to skip real API calls and return
a styled placeholder image. Perfect for local testing.
"""

import os
import base64
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

MINIMAX_URL = "https://api.minimax.io/v1/image_generation"
MINIMAX_MODEL = "image-01"

# ── Minimal valid 1×1 dark-teal PNG (so the UI renders something) ──────────
_PLACEHOLDER_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAQAAAADCAYAAAC09K7GAAAAFklEQVQI12NgYGD4"
    "z8BQDwAAAP//AwBkAAMBHXJLAAAAAElFTkSuQmCC"
)


def _is_mock() -> bool:
    return os.getenv("MOCK_IMAGES", "false").lower() in ("true", "1", "yes")


def _placeholder(label: str = "") -> str:
    """Return a tiny labelled dark placeholder as a data URI."""
    return f"data:image/png;base64,{_PLACEHOLDER_B64}"


async def generate_image(prompt: str, aspect_ratio: str = "16:9") -> str:
    """
    Generate an image via MiniMax API.
    If MOCK_IMAGES=true → returns placeholder instantly (no API call).
    Returns a data URI string.
    """
    if _is_mock():
        logger.info("[MOCK] Skipping MiniMax — returning placeholder image")
        return _placeholder()

    api_key = os.getenv("minimax_api", "")
    if not api_key:
        logger.warning("minimax_api not set — returning placeholder")
        return _placeholder()

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": MINIMAX_MODEL,
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "response_format": "base64",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(MINIMAX_URL, headers=headers, json=payload)
            resp.raise_for_status()
            images: list = resp.json().get("data", {}).get("image_base64", [])
            if images:
                return f"data:image/jpeg;base64,{images[0]}"
            logger.error(f"MiniMax returned no images: {resp.json()}")
        except Exception as e:
            logger.error(f"MiniMax error: {e}")

    return _placeholder()


async def generate_images(prompts: list[str]) -> list[str]:
    """Generate all images in parallel (or mock in parallel)."""
    return list(await asyncio.gather(*[generate_image(p) for p in prompts]))
