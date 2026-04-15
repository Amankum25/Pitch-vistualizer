import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

async def main():
    api_key = os.getenv("minimax_api")
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "image-01",
        "prompt": "a beautiful landscape",
        "aspect_ratio": "16:9",
        "response_format": "base64",
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://api.minimax.io/v1/image_generation", headers=headers, json=payload)
        with open("minimax_out.txt", "w", encoding="utf-8") as f:
            f.write(f"STATUS: {resp.status_code}\n")
            f.write(f"TEXT: {resp.text[:500]}\n")

if __name__ == "__main__":
    asyncio.run(main())
