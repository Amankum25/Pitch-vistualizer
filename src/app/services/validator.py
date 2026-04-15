from src.app.models.job import Panel


def validate_panels(panels: list[Panel]) -> list[Panel]:
    if len(panels) < 3:
        raise ValueError(
            f"Storyboard requires at least 3 panels, but got {len(panels)}. "
            "Provide a longer pitch text."
        )
    for i, panel in enumerate(panels):
        if not panel.enriched_prompt:
            raise ValueError(f"Panel {i + 1} is missing an enriched prompt.")
        if not panel.image_url:
            raise ValueError(f"Panel {i + 1} is missing an image.")
    return panels
