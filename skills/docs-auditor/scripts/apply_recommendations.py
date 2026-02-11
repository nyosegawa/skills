#!/usr/bin/env python3
"""
apply_recommendations.py — Apply auto-applicable doc recommendations.

Handles update_last_validated and add_last_validated actions.
Dry-run by default.

Usage:
    python3 apply_recommendations.py --recommendations <dir> [--confirm] [--backup]
"""

import json
import os
import re
import sys
import shutil
import argparse
from datetime import datetime, timezone


def load_recommendations(recs_dir: str) -> list[dict]:
    """Load all .rec.json files from directory."""
    recs = []
    for fname in sorted(os.listdir(recs_dir)):
        if fname.endswith(".rec.json"):
            fp = os.path.join(recs_dir, fname)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    rec = json.load(f)
                rec["_source_file"] = fp
                recs.append(rec)
            except Exception as e:
                print(f"WARNING: Could not load {fp}: {e}", file=sys.stderr)
    return recs


def update_last_validated(filepath: str, new_date: str, dry_run: bool = True,
                          backup: bool = True) -> dict:
    """Update the last-validated field in a markdown file's frontmatter."""
    result = {"filepath": filepath, "status": None, "detail": None}

    if not os.path.isfile(filepath):
        result["status"] = "error"
        result["detail"] = f"File not found: {filepath}"
        return result

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        result["status"] = "error"
        result["detail"] = f"Could not read: {e}"
        return result

    # Try to update existing last-validated
    pattern = r"(last[-_]validated\s*:\s*)(\S+)"
    if re.search(pattern, content, re.IGNORECASE):
        new_content = re.sub(pattern, rf"\g<1>{new_date}", content,
                             count=1, flags=re.IGNORECASE)
        if dry_run:
            result["status"] = "dry_run"
            result["detail"] = f"Would update last-validated to {new_date}"
        else:
            if backup:
                shutil.copy2(filepath, filepath + ".bak")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            result["status"] = "applied"
            result["detail"] = f"Updated last-validated to {new_date}"
        return result

    result["status"] = "error"
    result["detail"] = "No last-validated field found in file"
    return result


def add_last_validated(filepath: str, new_date: str, dry_run: bool = True,
                       backup: bool = True) -> dict:
    """Add a last-validated field to a markdown file's frontmatter."""
    result = {"filepath": filepath, "status": None, "detail": None}

    if not os.path.isfile(filepath):
        result["status"] = "error"
        result["detail"] = f"File not found: {filepath}"
        return result

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        result["status"] = "error"
        result["detail"] = f"Could not read: {e}"
        return result

    # Check if frontmatter exists
    fm_match = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)", content, re.DOTALL)
    if fm_match:
        # Add last-validated before closing ---
        new_content = (
            content[:fm_match.end(2)]
            + f"\nlast-validated: {new_date}"
            + content[fm_match.end(2):]
        )
    else:
        # Add frontmatter with last-validated at the top
        new_content = f"---\nlast-validated: {new_date}\n---\n\n{content}"

    if dry_run:
        result["status"] = "dry_run"
        result["detail"] = f"Would add last-validated: {new_date}"
    else:
        if backup:
            shutil.copy2(filepath, filepath + ".bak")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        result["status"] = "applied"
        result["detail"] = f"Added last-validated: {new_date}"

    return result


def main():
    parser = argparse.ArgumentParser(description="Apply doc recommendations")
    parser.add_argument("--recommendations", required=True,
                        help="Directory containing .rec.json files")
    parser.add_argument("--confirm", action="store_true",
                        help="Actually apply changes (default: dry-run)")
    parser.add_argument("--backup", action="store_true", default=True,
                        help="Create .bak files before modifying")
    parser.add_argument("--output", default="./changelog.md",
                        help="Changelog output path")
    args = parser.parse_args()

    if not os.path.isdir(args.recommendations):
        print(f"ERROR: Directory not found: {args.recommendations}",
              file=sys.stderr)
        sys.exit(1)

    recs = load_recommendations(args.recommendations)
    if not recs:
        print("No .rec.json files found.", file=sys.stderr)
        sys.exit(0)

    mode = "APPLY" if args.confirm else "DRY RUN"
    print(f"\n{'='*60}")
    print(f"  Docs Auditor — Recommendation Application ({mode})")
    print(f"{'='*60}\n")

    changelog = []
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for rec in recs:
        filepath = rec.get("filepath", "")
        action = rec.get("action", "")
        new_date = rec.get("new_date", today)

        print(f"[{action}] {filepath}")
        print(f"  Date: {new_date}")
        print(f"  Rationale: {rec.get('rationale', '?')}")

        if action == "update_last_validated":
            result = update_last_validated(
                filepath, new_date, dry_run=not args.confirm, backup=args.backup
            )
        elif action == "add_last_validated":
            result = add_last_validated(
                filepath, new_date, dry_run=not args.confirm, backup=args.backup
            )
        else:
            result = {"status": "skipped", "detail": f"Non-automatable: {action}"}

        print(f"  Status: {result['status']} — {result['detail']}\n")
        changelog.append({
            "filepath": filepath, "action": action,
            "status": result["status"], "detail": result["detail"],
        })

    # Write changelog
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(f"# Docs Auditor Changelog\n\n")
        f.write(f"**Date**: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Mode**: {mode}\n")
        f.write(f"**Recommendations processed**: {len(changelog)}\n\n")
        for entry in changelog:
            f.write(f"- `{entry['filepath']}`: {entry['action']} "
                    f"({entry['status']}) — {entry['detail']}\n")

    print(f"Changelog: {args.output}")
    if not args.confirm:
        print("\nDry run. To apply: re-run with --confirm")


if __name__ == "__main__":
    main()
