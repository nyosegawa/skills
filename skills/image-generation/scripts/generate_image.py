#!/usr/bin/env python3
"""Generate an image using Gemini's image generation API.

Usage:
    python scripts/generate_image.py "prompt text" /path/to/output.png
    python scripts/generate_image.py --image-size 4K --aspect-ratio 16:9 --downscale 1200 "prompt" /path/to/output.png

Requires:
    - google-genai: pip install google-genai
    - Pillow: pip install Pillow (for JPEG→PNG conversion and downscaling)
    - GEMINI_API_KEY environment variable
"""

import argparse
import io
import sys
from pathlib import Path

from PIL import Image
from google import genai


def generate_image(
    prompt: str,
    output_path: str,
    model: str = "gemini-3-pro-image-preview",
    downscale_width: int | None = None,
    image_size: str | None = None,
    aspect_ratio: str | None = None,
) -> None:
    client = genai.Client()

    image_config = None
    if image_size or aspect_ratio:
        kwargs = {}
        if image_size:
            kwargs["image_size"] = image_size
        if aspect_ratio:
            kwargs["aspect_ratio"] = aspect_ratio
        image_config = genai.types.ImageConfig(**kwargs)

    response = client.models.generate_content(
        model=model,
        contents=[prompt],
        config=genai.types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=image_config,
        ),
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)

            # inline_data.data is already bytes (not base64-encoded)
            img = Image.open(io.BytesIO(part.inline_data.data))
            original_size = img.size

            if downscale_width and img.width > downscale_width:
                ratio = downscale_width / img.width
                new_h = int(img.height * ratio)
                img = img.resize((downscale_width, new_h), Image.LANCZOS)

            img.save(str(out), "PNG")
            print(f"Saved: {output_path} (original={original_size}, final={img.size})")
            return

    print("No image generated in response", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate image with Gemini API")
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("output", help="Output file path (PNG)")
    parser.add_argument("--model", default="gemini-3-pro-image-preview",
                        help="Gemini model to use (default: gemini-3-pro-image-preview)")
    parser.add_argument("--downscale", type=int, default=None,
                        help="Downscale to this width (px) after generation, preserving aspect ratio")
    parser.add_argument("--image-size", default=None, choices=["512px", "1K", "2K", "4K"],
                        help="Output image size (default: 1K)")
    parser.add_argument("--aspect-ratio", default=None,
                        help="Aspect ratio (e.g. 16:9, 4:3, 1:1)")
    args = parser.parse_args()

    generate_image(args.prompt, args.output, args.model, args.downscale,
                   args.image_size, args.aspect_ratio)


if __name__ == "__main__":
    main()
