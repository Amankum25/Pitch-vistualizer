# Architecture

## System Diagram
```text
[ User Browser (Frontend UI) ]
         |
    (POST /generate-storyboard)
         |
         v
[ FastAPI Backend (Pipeline Orchestrator) ]
         |
         +--> [ Groq Client ] (Round-robin keys)
         |        - Segments Scenes
         |        - Enriches Prompts
         |
         +--> [ HuggingFace Client ]
                  - Generates Images (Parallel)
```

## Data Flow
1. User provides `text` and `style`.
2. Pipeline calls Groq to parse `text` into `scenes` [JSON array].
3. For each `scene`, Groq is called to build an `enriched_prompt`.
4. The Pipeline launches concurrent `asyncio.gather` calls to `image_generator.py`.
5. HuggingFace returns image bytes which are converted into base64 data URIs.
6. The `validator` checks constraints.
7. Backend returns a `StoryboardResponse` JSON object to the frontend.

## Component Responsibilities
- `pipeline.py`: Orchestrates the main async logic flow.
- `groq_client.py`: Manages LLM connections, auto-retries, and rotates 7 API keys for high availability.
- `image_generator.py`: Specific integration layer for HuggingFace's Inference API.
- `prompts.py`: Central store for system instructions to the LLM.

## Scaling Considerations
- **Stateless:** The backend keeps no state. Images are not saved to disk, they are streamed back in base64 immediately. Fits perfectly on serverless or load-balanced environments (Render).
- **Rate Limits:** Rotating Groq keys allows 7x the base rate limit. The HuggingFace integration gracefully falls back to SDXL if FLUX is busy, or returns a placeholder if it completely fails.
