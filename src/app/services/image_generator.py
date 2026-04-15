"""
image_generator.py – MiniMax image generation via REST API.
Endpoint: https://api.minimax.io/v1/image_generation
Model: image-01
Returns base64-encoded JPEG images.
"""

import os
import base64
import asyncio
import logging
import httpx

logger = logging.getLogger(__name__)

MINIMAX_URL = "https://api.minimax.io/v1/image_generation"
MINIMAX_MODEL = "image-01"


async def generate_image(prompt: str, aspect_ratio: str = "16:9") -> str:
    """
    Generate an image via MiniMax API.
    Returns a data URI string: 'data:image/jpeg;base64,...'
    Falls back to a placeholder dark image on failure.
    """
    api_key = os.getenv("minimax_api", "")
    if not api_key:
        logger.warning("minimax_api not set in env. Returning placeholder.")
        return _placeholder_image()

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
            data = resp.json()
            images: list = data.get("data", {}).get("image_base64", [])
            if images:
                return f"data:image/jpeg;base64,{images[0]}"
            logger.error(f"MiniMax returned no images. Response: {data}")
        except Exception as e:
            logger.error(f"MiniMax image generation failed: {e}")

    return _placeholder_image()


async def generate_images(prompts: list[str]) -> list[str]:
    """Generate all images in parallel."""
    tasks = [generate_image(p) for p in prompts]
    return list(await asyncio.gather(*tasks))


def _placeholder_image() -> str:
    """Return a tiny dark placeholder as base64 PNG."""
    # 1x1 pixel dark teal PNG (hardcoded minimal PNG bytes)
    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return f"data:image/png;base64,{png_b64}"
