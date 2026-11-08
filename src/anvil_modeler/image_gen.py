"""Gerador de concept art local (SDXL-Turbo via diffusers).

Instale com: pip install -e ".[imagegen]"
SDXL-Turbo roda em ~6-8 GB de VRAM, 1-4 passos, 512x512.
"""
from __future__ import annotations

from pathlib import Path

_pipe = None


def _load():
    global _pipe
    if _pipe is None:
        import torch
        from diffusers import AutoPipelineForText2Image

        cuda = torch.cuda.is_available()
        _pipe = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sdxl-turbo",
            torch_dtype=torch.float16 if cuda else torch.float32,
            variant="fp16" if cuda else None,
        ).to("cuda" if cuda else "cpu")
    return _pipe


def generate_concept(prompt: str, out_path: str | Path, seed: int = 0) -> str:
    import torch

    pipe = _load()
    gen = torch.Generator(device=pipe.device).manual_seed(seed)
    image = pipe(
        prompt=prompt, num_inference_steps=4, guidance_scale=0.0,
        width=512, height=512, generator=gen,
    ).images[0]
    image.save(out_path)
    return str(out_path)
