"""
groq_client.py – 5-key Groq client with:
  - Round-robin rotation for sequential calls
  - parallel_complete() race pattern (all 5 keys simultaneously, first wins)
"""

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
            logger.warning("No Groq API keys found (expected groq_api_key1..5)")
        else:
            logger.info(f"Loaded {len(self.keys)} Groq API key(s).")

        self._clients = [AsyncGroq(api_key=k) for k in self.keys]
        self._cycle = cycle(self._clients) if self._clients else iter([])
        self._lock = asyncio.Lock()

    async def _call_single(self, client: AsyncGroq, messages: list, model: str) -> str:
        resp = await client.chat.completions.create(messages=messages, model=model)
        return resp.choices[0].message.content

    async def complete(
        self,
        messages: list,
        model: str = "llama-3.3-70b-versatile",
        max_retries: int = 3,
    ) -> str:
        """Sequential call with round-robin key rotation and retry."""
        last_exc = None
        for attempt in range(max_retries):
            try:
                async with self._lock:
                    client = next(self._cycle)
                return await self._call_single(client, messages, model)
            except Exception as e:
                logger.error(f"Groq attempt {attempt + 1} failed: {e}")
                last_exc = e
                await asyncio.sleep(0.5)
        raise last_exc or RuntimeError("Groq completion failed after all retries")

    async def parallel_complete(
        self,
        messages: list,
        model: str = "llama-3.3-70b-versatile",
    ) -> str:
        """
        RACE PATTERN: Fire same request to all 5 keys simultaneously.
        Returns the first successful response and cancels the rest.
        Achieves minimum latency + maximum reliability.
        """
        if not self._clients:
            raise ValueError("No Groq clients configured.")

        loop = asyncio.get_event_loop()

        # Create one task per client — they race
        pending: set[asyncio.Task] = set()
        for client in self._clients:
            task = loop.create_task(self._call_single(client, messages, model))
            pending.add(task)

        result = None
        try:
            while pending:
                done, pending = await asyncio.wait(
                    pending, return_when=asyncio.FIRST_COMPLETED
                )
                for task in done:
                    exc = task.exception()
                    if exc is None:
                        result = task.result()
                        break
                    else:
                        logger.warning(f"parallel_complete task error (ignored): {exc}")
                if result is not None:
                    break
        finally:
            # Cancel all remaining tasks
            for t in pending:
                t.cancel()

        if result is None:
            raise RuntimeError("All parallel Groq calls failed.")
        return result


groq_client = GroqRoundRobinClient()
