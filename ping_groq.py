"""
ping_groq.py – Local ping test for Groq API connectivity.
Run: python ping_groq.py
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


async def ping():
    from groq import AsyncGroq

    keys = {f"groq_api_key{i}": os.getenv(f"groq_api_key{i}") for i in range(1, 6)}
    loaded = {k: v for k, v in keys.items() if v}

    if not loaded:
        print("❌ No Groq keys found in .env (expected groq_api_key1..5)")
        return

    print(f"✅ Found {len(loaded)} Groq key(s): {list(loaded.keys())}")
    print("─" * 50)

    for name, key in loaded.items():
        try:
            client = AsyncGroq(api_key=key)
            resp = await client.chat.completions.create(
                messages=[{"role": "user", "content": "Say PONG in one word."}],
                model="llama-3.3-70b-versatile",
                max_tokens=5,
            )
            reply = resp.choices[0].message.content.strip()
            print(f"✅ {name}: RESPONSE → {reply}")
        except Exception as e:
            print(f"❌ {name}: FAILED → {e}")

    print("─" * 50)
    print("Groq ping complete.")


if __name__ == "__main__":
    asyncio.run(ping())
