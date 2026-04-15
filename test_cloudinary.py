import asyncio
import os
from dotenv import load_dotenv

# Load from .env so Cloudinary sees the keys
load_dotenv()

from src.app.services.storage_service import store_image

# Tiny valid png
_PLACEHOLDER_B64 = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAQAAAADCAYAAAC09K7GAAAAFklEQVQI12NgYGD4"
    "z8BQDwAAAP//AwBkAAMBHXJLAAAAAElFTkSuQmCC"
)

async def main():
    import cloudinary
    import cloudinary.uploader
    print("Cloudinary Env Vars:")
    print("NAME:", os.getenv("CLOUDINARY_CLOUD_NAME"))
    print("KEY:", bool(os.getenv("CLOUDINARY_API_KEY")))
    print("SECRET:", bool(os.getenv("CLOUDINARY_API_SECRET")))
    
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    )
    
    print("\nUploading directly to Cloudinary...")
    try:
        result = cloudinary.uploader.upload(_PLACEHOLDER_B64, folder="pitch-visualizer")
        print("Success! URL:", result.get("secure_url"))
    except Exception as e:
        print("ERROR:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
