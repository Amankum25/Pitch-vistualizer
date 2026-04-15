import pathlib
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from src.app.models.job import StoryboardRequest, StoryboardResponse
from src.app.services.pipeline import process_storyboard

router = APIRouter()
logger = logging.getLogger(__name__)

OUTPUTS_DIR = pathlib.Path("outputs")


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "Pitch Visualizer API v2"}


@router.post("/generate-storyboard", response_model=StoryboardResponse)
async def generate_storyboard(request: StoryboardRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    try:
        return await process_storyboard(request.text, request.style)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storyboard/{storyboard_id}", response_class=HTMLResponse)
async def view_storyboard(storyboard_id: str):
    """View the storyboard HTML in browser."""
    html_file = OUTPUTS_DIR / f"storyboard_{storyboard_id}.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="Storyboard not found.")
    return HTMLResponse(content=html_file.read_text(encoding="utf-8"))


@router.get("/download/{storyboard_id}")
async def download_storyboard(storyboard_id: str):
    """Download the storyboard HTML file."""
    html_file = OUTPUTS_DIR / f"storyboard_{storyboard_id}.html"
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="Storyboard not found.")
    return FileResponse(
        path=str(html_file),
        media_type="text/html",
        filename=f"storyboard_{storyboard_id}.html",
        headers={"Content-Disposition": f'attachment; filename="storyboard_{storyboard_id}.html"'},
    )
