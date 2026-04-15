from pydantic import BaseModel
from typing import List, Optional


class StoryboardRequest(BaseModel):
    text: str
    style: str = "comic"


class NarrativeAttributes(BaseModel):
    objective: str
    num_frames: int
    main_character: str
    environment: str
    tone_progression: List[str]
    style: str


class FrameAttributes(BaseModel):
    title: str
    subject: str
    action: str
    environment: str
    emotion: str
    tone: str


class Panel(BaseModel):
    scene_number: int
    scene_text: str
    frame: FrameAttributes
    enriched_prompt: str
    image_url: str
    caption: str


class StoryboardResponse(BaseModel):
    panels: List[Panel]
    style: str
    total_panels: int
    html_download_url: str
