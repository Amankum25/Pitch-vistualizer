"""
ping_minimax.py – Local ping test for MiniMax Image API connectivity.
Run: python ping_minimax.py

Uses the exact same API format as the official MiniMax docs.
"""

import os
import base64
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

MINIMAX_URL = "https://api.minimax.io/v1/image_generation"


async def ping():
    api_key = os.getenv("minimax_api", "")
    if not api_key:
        print("❌ minimax_api not found in .env")
        return

    print(f"✅ minimax_api key loaded (length: {len(api_key)} chars)")
    print("─" * 50)
    print("📤 Sending test image generation request...")

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "image-01",
        "prompt": "a single teal geometric shape on a dark background, minimalist test image",
        "aspect_ratio": "16:9",
        "response_format": "base64",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(MINIMAX_URL, headers=headers, json=payload)
            print(f"HTTP Status: {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                images = data.get("data", {}).get("image_base64", [])
                if images:
                    # Save the first image to disk as a test
                    with open("ping_minimax_output.jpeg", "wb") as f:
                        f.write(base64.b64decode(images[0]))
                    print(f"✅ SUCCESS! Got {len(images)} image(s). Saved → ping_minimax_output.jpeg")
                else:
                    print(f"⚠️  Status 200 but no images in response: {data}")
            else:
                print(f"❌ FAILED with status {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            print(f"❌ Exception: {e}")

    print("─" * 50)
    print("MiniMax ping complete.")


if __name__ == "__main__":
    asyncio.run(ping())
