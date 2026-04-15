import requests
import json

r = requests.post(
    'http://localhost:8000/api/v1/preview-prompts',
    json={
        'text': 'i had a small business but sales were very low and i was worried about losses then i discovered a marketing tool and started using it to promote my products gradually more customers started coming and my sales increased and finally my business became profitable',
        'style': 'comic'
    }
)
d = r.json()

with open("preview_output.md", "w", encoding="utf-8") as f:
    f.write(f"### CHARACTER EXTRACTED\n`{d['character_description']}`\n\n### THE PROMPTS\n\n")
    for i, frame in enumerate(d['frames']):
        f.write(f"**Frame {i+1}: {frame['title']}**\n```\n{frame['minimax_prompt']}\n```\n\n")
