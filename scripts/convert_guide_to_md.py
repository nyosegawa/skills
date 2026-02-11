"""
PDF to Markdown Converter for Anthropic's Skill Building Guide.

This script performs the following operations:
1. Downloads the specific PDF from Anthropic's resources.
2. Extracts raw text and hyperlink metadata using PyMuPDF to aid the LLM.
3. Sends the PDF binary and the extracted metadata to Google's Gemini 3 Pro.
4. Generates a high-fidelity Markdown transcription.
5. Saves the output to the reference_docs directory and cleans up artifacts.

Dependencies:
    pip install google-genai pymupdf requests
"""

import os
import sys
import shutil
import requests
import pymupdf  # fitz
from pathlib import Path
from typing import Tuple, List, Dict

# Check for the genai library (new version)
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: The 'google-genai' library is required.")
    print("Please install it via: pip install google-genai")
    sys.exit(1)


# --- Configuration ---
PDF_URL = "https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf"
MODEL_ID = "gemini-3-pro-preview"
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "reference_docs"
OUTPUT_FILENAME = "skill-bestpractice.md"
TEMP_PDF_NAME = "temp_source.pdf"
TEMP_TXT_NAME = "temp_meta.txt"


def check_api_key() -> str:
    """Retrieves the Gemini API key from environment variables or raises an error."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        print("Please export your API key:")
        print("  export GEMINI_API_KEY='your_key_here'")
        sys.exit(1)
    return api_key


def download_pdf(url: str, save_path: Path) -> None:
    """Downloads the PDF from the specified URL."""
    print(f"Downloading PDF from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
    except requests.RequestException as e:
        print(f"Failed to download PDF: {e}")
        sys.exit(1)


def extract_metadata(pdf_path: Path, output_txt_path: Path) -> str:
    """
    Extracts text layout and link information to assist the LLM.

    Returns:
        The content of the extracted text file as a string.
    """
    print("Extracting metadata (text & links) for LLM context...")
    doc = pymupdf.open(pdf_path)
    extracted_content = []

    extracted_content.append("=== EXTRACTED METADATA & LINK MAP ===")
    extracted_content.append("Use this data to ensure all URLs in the final Markdown are correct.")

    for page_index, page in enumerate(doc):
        page_num = page_index + 1
        extracted_content.append(f"\n--- Page {page_num} ---")

        # Extract text to help with OCR verification
        text = page.get_text()
        extracted_content.append(f"[Text Content]:\n{text.strip()}")

        # Extract links with their associated text
        links = page.get_links()
        if links:
            extracted_content.append("[Hyperlinks Found]:")
            for link in links:
                uri = link.get("uri")
                if uri:
                    # Attempt to find the text covered by the link rect
                    rect = link.get("from")
                    link_text = page.get_text("text", clip=rect).strip().replace("\n", " ")
                    if not link_text:
                        link_text = "Unknown/Image Link"
                    extracted_content.append(f"  - Text: '{link_text}' -> URL: {uri}")

    full_text = "\n".join(extracted_content)

    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    doc.close()
    return full_text


def generate_markdown(client: genai.Client, pdf_path: Path, meta_text: str) -> str:
    """
    Calls Gemini 3 Pro to transcribe the PDF into Markdown.
    """
    print(f"Sending request to {MODEL_ID}. This may take a minute...")

    # Read PDF binary
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    # The Prompt Engineering
    system_instruction = """
    You are an expert technical documentation specialist. Your task is to transcribe the attached PDF into a perfect, structured Markdown document.

    ### Source Material
    1. **The PDF File**: This is the primary visual source.
    2. **The Metadata Text**: Use this to strictly verify exact URLs and ensure no link information is lost or hallucinated.

    ### Formatting Rules
    1. **Headings**: strict hierarchy based on visual weight and document structure.
       - `#` (H1): The Document Title ("The Complete Guide to Building Skills for Claude").
       - `##` (H2): Chapter/Major Section Titles (e.g., "Introduction", "Chapter 1: Fundamentals").
       - `###` (H3): Sub-sections (e.g., "What is a skill?", "Core design principles").
       - `####` (H4): Detailed concepts (e.g., "Progressive Disclosure").
    2. **Links**: You MUST include all hyperlinks found in the document. Use the syntax `[Link Text](URL)`. Refer to the provided Metadata Text to ensure the URLs are 100% accurate.
    3. **Code Blocks**: Preserve all code snippets. Use correct language fencing (e.g., ```python, ```yaml, ```bash).
    4. **Cleanliness**:
       - Do NOT include page numbers.
       - Do NOT include headers/footers (like "Anthropic" logos or page counts) that repeat on every page.
       - Do NOT output "Page 1", "Page 2" separators.
    5. **Images**: If an image conveys crucial information (like a diagram), describe it briefly in blockquote context, e.g., `> [Diagram: description of flow]`. Do not use markdown image syntax `![]()` as we cannot host the images.

    ### Output Requirement
    Output ONLY the raw Markdown content. Do not include conversational filler like "Here is the markdown".
    """

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                types.Content(
                    parts=[
                        # System instruction as context
                        types.Part.from_text(text=system_instruction),
                        # The extracted metadata to help with links
                        types.Part.from_text(text=f"REFERENCE METADATA:\n{meta_text}"),
                        # The actual PDF
                        types.Part.from_bytes(data=pdf_data, mime_type="application/pdf"),
                        types.Part.from_text(text="Begin the transcription now.")
                    ]
                )
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,  # Low temperature for factual transcription
                max_output_tokens=65536  # Ensure enough space for the whole doc
            )
        )
        return response.text
    except Exception as e:
        print(f"Error during Gemini generation: {e}")
        sys.exit(1)


def main():
    # 1. Setup
    api_key = check_api_key()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_pdf = SCRIPT_DIR / TEMP_PDF_NAME
    temp_txt = SCRIPT_DIR / TEMP_TXT_NAME
    final_output = OUTPUT_DIR / OUTPUT_FILENAME

    client = genai.Client(api_key=api_key)

    try:
        # 2. Download
        download_pdf(PDF_URL, temp_pdf)

        # 3. Extract Metadata
        meta_text = extract_metadata(temp_pdf, temp_txt)

        # 4. Generate with Gemini
        markdown_content = generate_markdown(client, temp_pdf, meta_text)

        # 5. Save Output
        print(f"Saving markdown to {final_output}...")
        with open(final_output, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print("Success! Document conversion complete.")

    finally:
        # 6. Cleanup
        print("Cleaning up temporary files...")
        if temp_pdf.exists():
            os.remove(temp_pdf)
        if temp_txt.exists():
            os.remove(temp_txt)


if __name__ == "__main__":
    main()