#!/usr/bin/env python3
"""
Gemini Query Script for Repository Analysis.

Sends a prompt with optional file content to Gemini 3 Pro for analysis.
This is a thin API bridge — cost estimation is handled externally using
gtc's token count output.

Usage:
    python3 gemini_query.py --prompt "Analyze the architecture" --file content.txt
    python3 gemini_query.py --prompt-file prompt.txt --file content.txt
    python3 gemini_query.py --prompt "..." --file tree.txt --file src.txt --output result.md
"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Query Gemini 3 Pro with optional file content for repository analysis"
    )
    parser.add_argument("--prompt", help="Analysis prompt text")
    parser.add_argument("--prompt-file", help="File containing the analysis prompt")
    parser.add_argument(
        "--file", action="append", dest="files",
        help="File(s) to include as context (can be specified multiple times)"
    )
    parser.add_argument("--model", default="gemini-3-pro-preview",
                        help="Gemini model ID (default: gemini-3-pro-preview)")
    parser.add_argument("--temperature", type=float, default=0.2,
                        help="Generation temperature (default: 0.2)")
    parser.add_argument("--max-tokens", type=int, default=65536,
                        help="Max output tokens (default: 65536)")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    args = parser.parse_args()

    # Gather prompt
    prompt = None
    if args.prompt:
        prompt = args.prompt
    elif args.prompt_file:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read()
    elif not sys.stdin.isatty():
        prompt = sys.stdin.read()

    if not prompt:
        print("Error: No prompt provided. Use --prompt, --prompt-file, or pipe via stdin.",
              file=sys.stderr)
        sys.exit(1)

    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.",
              file=sys.stderr)
        print("Set it with: export GEMINI_API_KEY='your_key_here'",
              file=sys.stderr)
        sys.exit(1)

    # Check google-genai
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Error: google-genai library is not installed.", file=sys.stderr)
        print("Install with: pip install google-genai", file=sys.stderr)
        sys.exit(1)

    # Build content parts
    parts = [types.Part.from_text(text=prompt)]

    if args.files:
        for file_path in args.files:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            size_mb = len(content.encode("utf-8")) / (1024 * 1024)
            print(f"[INFO] Loaded: {file_path} ({size_mb:.2f} MB)", file=sys.stderr)
            parts.append(
                types.Part.from_text(
                    text=f"=== Content from: {os.path.basename(file_path)} ===\n{content}"
                )
            )

    # Call Gemini
    client = genai.Client(api_key=api_key)
    print(f"[INFO] Sending request to {args.model}...", file=sys.stderr)

    try:
        response = client.models.generate_content(
            model=args.model,
            contents=[types.Content(parts=parts)],
            config=types.GenerateContentConfig(
                temperature=args.temperature,
                max_output_tokens=args.max_tokens,
            ),
        )

        result = response.text

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[INFO] Output written to: {args.output}", file=sys.stderr)
        else:
            print(result)

        # Print actual usage from API response
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            um = response.usage_metadata
            actual_in = getattr(um, "prompt_token_count", "?")
            actual_out = getattr(um, "candidates_token_count", "?")
            print(f"[INFO] Actual usage: {actual_in} input tokens, "
                  f"{actual_out} output tokens", file=sys.stderr)

    except Exception as e:
        print(f"Error during Gemini API call: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
