# Workflow

## Step-by-Step Pipeline
1. **Input Reception**: The `process_storyboard` pipeline function receives raw string text and a selected style.
2. **Segmentation**: `build_segmentation_prompt` transforms the text into 3 to 6 distinct scenes.
3. **Enrichment**: Each scene text is padded with visual descriptors (lighting, subject, format) to match the selected `style` using `build_enrichment_prompt`.
4. **Validation/Review**: Overly short prompts are passed to `review_prompt` to be expanded.
5. **Image Generation**: All enriched prompts are fired asynchronously against the HuggingFace Inference API.
6. **Formatting**: Base64 data and metadata are assembled into Pydantic models.
7. **Validation**: The storyboard is checked explicitly for >= 3 panels.
8. **Delivery**: Payload delivered to frontend.

## Example Flow
**Input**:
`text`: "An AI developer typing at his desk. He gets a brilliant idea."
`style`: "cyberpunk"

**Segmentation**:
1. "An AI developer typing at his desk."
2. "He gets a brilliant idea."

*(Note: If segmentation is less than 3 scenes, the app warns but attempts to process)*

**Enrichment 1**: "A pale cyber-developer typing on a holographic keyboard at his messy, neon-lit desk. Style: cyberpunk."
**Enrichment 2**: "The developer's face illuminates with sudden realization as the matrix code reflects in his cybernetic eyes. Style: cyberpunk."

**Images**: [Base64 Encoded Strings]

## Error Handling Flow
- **LLM Error**: `groq_client` auto-rotates to the next key. If all keys fail, `HTTP 500` is returned.
- **JSON Format Error**: If Groq fails to return valid JSON arrays for scenes, a regex text-splitter fallback evaluates the raw string.
- **Image Generation Error**: `image_generator` tries FLUX.1. On failure, falls back to SD-XL Turbo. On total failure, returns a grey 1x1 base64 image rather than completely crashing the pipeline, allowing the user to still see the story text.
- **Validation Error**: Throws `HTTP 422`.
