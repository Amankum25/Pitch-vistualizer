"""
image_generator.py – OpenRouter image generation using standard openai SDK round robin.

Set MOCK_IMAGES=true in .env to skip real API calls and return
a styled placeholder image. Perfect for local testing.
"""

import os
import asyncio
import logging
import re
from openai import AsyncOpenAI
from itertools import cycle

logger = logging.getLogger(__name__)

# The specific OpenRouter model required for Gemini text-to-image
OPENROUTER_MODEL = "google/gemini-2.5-flash-image"

# Retrieve all openrouter keys
_keys = [os.getenv(f"OPENROUTER_KEY{i}", "") for i in range(1, 13)]
_keys = [k for k in _keys if k]
if _keys:
    _key_cycle = cycle(_keys)
else:
    _key_cycle = None

# Minimal valid 1x1 dark-teal PNG (so the UI renders something)
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
    Generate an image via OpenRouter API using round-robin keys.
    OpenRouter uses chat.completions for image generation with modalities.
    """
    if _is_mock():
        logger.info("[MOCK] Skipping openrouter — returning placeholder image")
        return _placeholder()

    if not _key_cycle:
        logger.warning("No OPENROUTER_KEYs configured - returning placeholder")
        return _placeholder()

    max_attempts = len(_keys) if _keys else 1

    for attempt in range(max_attempts):
        current_key = next(_key_cycle)
        
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=current_key
        )

        try:
            # Setting max_tokens to a small number to bypass OpenRouter's massive default reservation limit
            resp = await client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                extra_body={"modalities": ["image"]},
                max_tokens=250
            )
            
            msg = resp.choices[0].message
            
            # 1. Extract from extended OpenRouter schema
            msg_dict = msg.model_dump()
            extra = getattr(msg, "model_extra", {}) or {}
            
            images_array = msg_dict.get("images") or extra.get("images")
            
            if images_array and isinstance(images_array, list) and len(images_array) > 0:
                image_obj = images_array[0]
                if "image_url" in image_obj and "url" in image_obj["image_url"]:
                    return image_obj["image_url"]["url"]

            # 2. Fallback to parsing markdown content
            content = msg.content or ""
            
            match = re.search(r'!\[.*?\]\((.*?)\)', content)
            if match:
                return match.group(1)
            
            if content.startswith("data:image/") or content.startswith("http"):
                return content.strip()

            logger.error(f"Failed to find image in response: {msg_dict}")
            raise RuntimeError("No image data returned by OpenRouter API.")
        
        except Exception as e:
            err_str = str(e)
            if "402" in err_str:
                logger.warning(f"OpenRouter 402 Error (Insufficient Funds) on key ending in {current_key[-4:]}. Trying next key...")
                continue
            else:
                logger.error(f"OpenRouter Image Gen Error: {err_str}")
                raise RuntimeError(err_str)
                
    raise RuntimeError("All configured OpenRouter keys exhausted (402) or failed.")

async def generate_images(prompts: list[str]) -> list[str]:
    """Generate all images in parallel (or mock in parallel)."""
    return list(await asyncio.gather(*[generate_image(p) for p in prompts]))
