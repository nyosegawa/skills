#!/usr/bin/env python3
"""
collect_docs.py — Collect documentation metadata from a project.

Scans for CLAUDE.md, AGENTS.md, docs/*.md, docs/adr/ADR-*.md, and README.md.
Extracts frontmatter fields (last-validated, phase, status), token counts,
and git-based freshness data.

Usage:
    python3 collect_docs.py --project-root <path> [--output <path>] [--verbose]
"""

import json
import os
import re
import subprocess
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken if available, else character-based fallback."""
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4")
        return len(enc.encode(text))
    except ImportError:
        return len(text) // 4


def parse_frontmatter(content: str) -> dict:
    """Extract YAML-like frontmatter fields from markdown content."""
    result = {}
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return result

    for line in match.group(1).splitlines():
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().lower().replace("-", "_")
            val = val.strip().strip('"').strip("'")
            if val:
                result[key] = val

    return result


def git_freshness(filepath: str, project_root: str) -> dict:
    """Get git-based freshness info for a file."""
    result = {
        "git_last_modified": None,
        "git_last_modified_age_days": None,
        "git_last_author": None,
        "git_commit_count": 0,
    }

    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%aI\t%an", "--", filepath],
            cwd=project_root, capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            parts = out.stdout.strip().split("\t", 1)
            iso_date = parts[0]
            result["git_last_modified"] = iso_date
            result["git_last_author"] = parts[1] if len(parts) > 1 else None
            try:
                dt = datetime.fromisoformat(iso_date)
                age = (datetime.now(timezone.utc) - dt).days
                result["git_last_modified_age_days"] = max(age, 0)
            except ValueError:
                pass
    except Exception:
        pass

    try:
        out = subprocess.run(
            ["git", "rev-list", "--count", "HEAD", "--", filepath],
            cwd=project_root, capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            result["git_commit_count"] = int(out.stdout.strip())
    except Exception:
        pass

    return result


def classify_doc(filepath: str) -> tuple[str, str]:
    """Return (doc_type, injection_mode) for a document path."""
    basename = os.path.basename(filepath)
    if basename == "CLAUDE.md":
        return "claude_md", "always"
    if basename == "AGENTS.md":
        return "agents_md", "always"
    if basename == "README.md":
        return "readme", "on_demand"
    if "/adr/" in filepath or "\\adr\\" in filepath:
        return "adr", "on_demand"
    return "general_doc", "on_demand"


def extract_adr_status(content: str) -> tuple[str | None, str | None]:
    """Extract ADR Status and Superseded-by from content."""
    status = None
    superseded_by = None

    status_match = re.search(r"\*\*Status\*\*\s*:\s*(.+)", content)
    if status_match:
        status = status_match.group(1).strip()

    if not status_match:
        status_match = re.search(r"^Status\s*:\s*(.+)", content, re.MULTILINE)
        if status_match:
            status = status_match.group(1).strip()

    if status:
        sup_match = re.search(r"[Ss]uperseded\s+by\s+(ADR[- ]?\d+)", status)
        if sup_match:
            superseded_by = sup_match.group(1).replace(" ", "-")

    return status, superseded_by


def scan_doc(filepath_abs: str, project_root: str, verbose: bool = False) -> dict:
    """Scan a single document and extract all metadata."""
    rel_path = os.path.relpath(filepath_abs, project_root)
    doc_type, injection_mode = classify_doc(rel_path)

    try:
        with open(filepath_abs, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        if verbose:
            print(f"  WARNING: Could not read {rel_path}: {e}", file=sys.stderr)
        return None

    fm = parse_frontmatter(content)
    lines = content.splitlines()
    headings = [l for l in lines if l.startswith("#")]

    # Freshness from frontmatter
    last_validated = fm.get("last_validated")
    last_validated_age_days = None
    if last_validated:
        try:
            dt = datetime.fromisoformat(last_validated)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            last_validated_age_days = max(
                (datetime.now(timezone.utc) - dt).days, 0
            )
        except ValueError:
            pass

    # ADR-specific
    status, superseded_by = None, None
    if doc_type == "adr":
        status, superseded_by = extract_adr_status(content)

    # Git freshness
    git_info = git_freshness(rel_path, project_root)

    # Freshness source
    if last_validated:
        freshness_source = "last_validated"
    else:
        freshness_source = "git"

    freshness_status = "superseded" if (status and "supersed" in status.lower()) else None

    # Body preview
    body_start = content.find("---", content.find("---") + 3)
    if body_start >= 0:
        body = content[body_start + 3:].strip()
    else:
        body = content.strip()
    body_preview = body[:300]

    return {
        "filepath": rel_path,
        "filepath_abs": filepath_abs,
        "doc_type": doc_type,
        "injection_mode": injection_mode,
        "content_tokens": count_tokens(content),
        "line_count": len(lines),
        "heading_count": len(headings),
        # Frontmatter freshness
        "last_validated": last_validated,
        "last_validated_age_days": last_validated_age_days,
        "phase": fm.get("phase"),
        "status": status,
        "superseded_by": superseded_by,
        # Git freshness
        **git_info,
        # Freshness meta
        "freshness_source": freshness_source,
        "freshness_status": freshness_status,
        # Content preview
        "first_heading": headings[0].lstrip("#").strip() if headings else None,
        "body_preview": body_preview,
    }


def discover_docs(project_root: str, verbose: bool = False) -> list[str]:
    """Find all documentation files in the project."""
    candidates = []
    root = Path(project_root)

    # Top-level files
    for name in ("CLAUDE.md", "AGENTS.md", "README.md"):
        p = root / name
        if p.is_file():
            candidates.append(str(p))

    # .claude/CLAUDE.md
    claude_sub = root / ".claude" / "CLAUDE.md"
    if claude_sub.is_file():
        candidates.append(str(claude_sub))

    # docs/*.md
    docs_dir = root / "docs"
    if docs_dir.is_dir():
        for f in sorted(docs_dir.glob("*.md")):
            if f.is_file():
                candidates.append(str(f))

    # docs/adr/ADR-*.md (also match lowercase)
    adr_dir = docs_dir / "adr"
    if adr_dir.is_dir():
        for f in sorted(adr_dir.glob("*.md")):
            if f.is_file():
                candidates.append(str(f))

    # Deduplicate by resolved path
    seen = set()
    unique = []
    for c in candidates:
        resolved = os.path.realpath(c)
        if resolved not in seen:
            seen.add(resolved)
            unique.append(c)

    if verbose:
        print(f"Found {len(unique)} documentation files", file=sys.stderr)

    return unique


def collect(project_root: str, verbose: bool = False) -> dict:
    """Main collection function."""
    project_root = os.path.abspath(project_root)

    if not os.path.isdir(project_root):
        return {"error": f"Project root not found: {project_root}"}

    doc_paths = discover_docs(project_root, verbose)
    docs = []

    for dp in doc_paths:
        doc = scan_doc(dp, project_root, verbose)
        if doc:
            docs.append(doc)
            if verbose:
                print(
                    f"  {doc['filepath']} ({doc['doc_type']}, "
                    f"{doc['content_tokens']} tokens, "
                    f"freshness: {doc['freshness_source']})",
                    file=sys.stderr,
                )

    # Context budget summary
    always_on_tokens = sum(d["content_tokens"] for d in docs if d["injection_mode"] == "always")
    on_demand_tokens = sum(d["content_tokens"] for d in docs if d["injection_mode"] == "on_demand")
    total = always_on_tokens + on_demand_tokens
    token_values = [d["content_tokens"] for d in docs] if docs else [0]
    token_values_sorted = sorted(token_values)
    median = token_values_sorted[len(token_values_sorted) // 2]
    mean = total / len(docs) if docs else 0

    return {
        "project_root": project_root,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "docs": docs,
        "context_budget": {
            "total_doc_tokens": total,
            "always_on_tokens": always_on_tokens,
            "on_demand_tokens": on_demand_tokens,
            "doc_count": len(docs),
            "mean_tokens_per_doc": round(mean),
            "median_tokens_per_doc": median,
            "docs_above_2x_median": [
                d["filepath"] for d in docs if d["content_tokens"] > 2 * median
            ] if median > 0 else [],
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Collect documentation metadata from a project"
    )
    parser.add_argument(
        "--project-root", required=True,
        help="Path to the project root directory",
    )
    parser.add_argument(
        "--output", default="./doc-manifest.json",
        help="Output file path (default: ./doc-manifest.json)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print progress details",
    )

    args = parser.parse_args()

    result = collect(args.project_root, verbose=args.verbose)

    if "error" in result:
        print(json.dumps(result, indent=2), file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    budget = result["context_budget"]
    print(
        f"Collected {budget['doc_count']} docs. "
        f"Context budget: {budget['total_doc_tokens']} tokens "
        f"(always-on: {budget['always_on_tokens']}, "
        f"on-demand: {budget['on_demand_tokens']})"
    )
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
