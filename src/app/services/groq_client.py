import os
import asyncio
from itertools import cycle
from groq import AsyncGroq
import logging

logger = logging.getLogger(__name__)


class GroqRoundRobinClient:
    def __init__(self):
        self.keys = []
        for i in range(1, 6):
            key = os.getenv(f"groq_api_key{i}")
            if key and key.strip():
                self.keys.append(key.strip())

        if not self.keys:
            logger.warning("No Groq API keys found in env (expected groq_api_key1..5)")
        else:
            logger.info(f"Loaded {len(self.keys)} Groq API key(s).")

        self._clients = [AsyncGroq(api_key=k) for k in self.keys]
        self._cycle = cycle(self._clients) if self._clients else iter([])
        self._lock = asyncio.Lock()

    async def get_client(self) -> AsyncGroq:
        if not self._clients:
            raise ValueError("No Groq clients configured. Set groq_api_key1..5 in .env")
        async with self._lock:
            return next(self._cycle)

    async def complete(
        self,
        messages: list,
        model: str = "llama-3.3-70b-versatile",
        max_retries: int = 3,
    ) -> str:
        last_exc = None
        for attempt in range(max_retries):
            try:
                client = await self.get_client()
                resp = await client.chat.completions.create(
                    messages=messages,
                    model=model,
                )
                return resp.choices[0].message.content
            except Exception as e:
                logger.error(f"Groq attempt {attempt + 1} failed: {e}")
                last_exc = e
                await asyncio.sleep(1)
        raise last_exc or RuntimeError("Groq completion failed after all retries")


groq_client = GroqRoundRobinClient()
