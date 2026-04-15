"""
storage_service.py – Optional Cloudinary image hosting.
If Cloudinary env vars are not set, returns the image URL/base64 unchanged.
"""

import os
import logging

logger = logging.getLogger(__name__)


def _cloudinary_configured() -> bool:
    return all(
        os.getenv(k)
        for k in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
    )


async def store_image(image_data: str) -> str:
    """
    Upload image to Cloudinary if configured, otherwise return as-is.
    image_data can be a URL or a data URI (base64).
    Returns the final URL/data URI.
    """
    if not _cloudinary_configured():
        return image_data  # Return base64 inline (self-contained)

    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        )
        result = cloudinary.uploader.upload(image_data, folder="pitch-visualizer")
        return result.get("secure_url", image_data)
    except Exception as e:
        logger.error(f"Cloudinary upload failed, using original: {e}")
        return image_data
