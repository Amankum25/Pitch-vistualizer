from src.app.services.groq_client import groq_client
from src.app.services.prompts import build_reviewer_prompt
import logging

logger = logging.getLogger(__name__)


async def review_prompt(prompt: str, style: str = "comic") -> str:
    """Expand weak prompts (< 30 chars) via Groq before sending to MiniMax."""
    if len(prompt.strip()) < 30:
        logger.info(f"Expanding weak prompt: {prompt!r}")
        try:
            messages = build_reviewer_prompt(prompt, style)
            improved = await groq_client.complete(messages)
            return improved.strip()
        except Exception as e:
            logger.error(f"Reviewer failed, using original: {e}")
    return prompt
