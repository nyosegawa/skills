#!/usr/bin/env python3
"""
apply_patches.py — Apply approved skill description patches.

Reads patch files from the workspace and applies them to SKILL.md files.
Always runs in dry-run mode unless --confirm is passed.

Usage:
    python3 apply_patches.py --patches <dir> [--confirm] [--backup]

Options:
    --patches DIR    Directory containing .patch.json files
    --confirm        Actually write changes (default: dry-run)
    --backup         Create .bak files before modifying (default: true)
    --output PATH    Write changelog to this path
"""

import json
import os
import re
import sys
import shutil
import argparse
from datetime import datetime, timezone


def load_patches(patches_dir: str) -> list[dict]:
    """Load all patch files from directory."""
    patches = []
    for fname in sorted(os.listdir(patches_dir)):
        if fname.endswith(".patch.json"):
            fp = os.path.join(patches_dir, fname)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    patch = json.load(f)
                patch["_source_file"] = fp
                patches.append(patch)
            except Exception as e:
                print(f"WARNING: Could not load {fp}: {e}", file=sys.stderr)
    return patches


def apply_description_patch(
    skill_path: str,
    current_description: str,
    proposed_description: str,
    dry_run: bool = True,
    backup: bool = True,
) -> dict:
    """Apply a description change to a SKILL.md file."""
    result = {
        "skill_path": skill_path,
        "status": None,
        "detail": None,
    }

    if not os.path.isfile(skill_path):
        result["status"] = "error"
        result["detail"] = f"File not found: {skill_path}"
        return result

    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        result["status"] = "error"
        result["detail"] = f"Could not read: {e}"
        return result

    frontmatter_match = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n)", content, re.DOTALL)
    if frontmatter_match:
        fm_content = frontmatter_match.group(2)

        desc_patterns = [
            r"(description\s*:\s*[>|]-?\s*\n)((?:\s+.*\n)*)",
            r"(description\s*:\s*)(.*)",
        ]

        replaced = False
        for pattern in desc_patterns:
            match = re.search(pattern, fm_content)
            if match:
                indent = "  "
                wrapped_lines = _wrap_text(proposed_description, width=76, indent=indent)
                new_desc_block = f"description: >\n{wrapped_lines}\n"

                new_content = (
                    content[:frontmatter_match.start(2) + match.start()]
                    + new_desc_block
                    + content[frontmatter_match.start(2) + match.end():]
                )

                if dry_run:
                    result["status"] = "dry_run"
                    result["detail"] = "Would apply change"
                    result["preview"] = new_desc_block.strip()
                else:
                    if backup:
                        shutil.copy2(skill_path, skill_path + ".bak")
                    with open(skill_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    result["status"] = "applied"
                    result["detail"] = "Description updated"

                replaced = True
                break

        if not replaced:
            result["status"] = "error"
            result["detail"] = "Could not locate description field in frontmatter"
    else:
        result["status"] = "error"
        result["detail"] = "No YAML frontmatter found in SKILL.md"

    return result


def _wrap_text(text: str, width: int = 76, indent: str = "  ") -> str:
    """Wrap text to width with indent prefix."""
    words = text.split()
    lines = []
    current_line = indent

    for word in words:
        if len(current_line) + len(word) + 1 > width:
            lines.append(current_line)
            current_line = indent + word
        else:
            if current_line == indent:
                current_line += word
            else:
                current_line += " " + word

    if current_line.strip():
        lines.append(current_line)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Apply skill description patches"
    )
    parser.add_argument(
        "--patches", required=True,
        help="Directory containing .patch.json files",
    )
    parser.add_argument(
        "--confirm", action="store_true",
        help="Actually apply changes (default: dry-run)",
    )
    parser.add_argument(
        "--backup", action="store_true", default=True,
        help="Create .bak files before modifying",
    )
    parser.add_argument(
        "--output", default="./changelog.md",
        help="Changelog output path",
    )

    args = parser.parse_args()

    if not os.path.isdir(args.patches):
        print(f"ERROR: Patches directory not found: {args.patches}", file=sys.stderr)
        sys.exit(1)

    patches = load_patches(args.patches)
    if not patches:
        print("No .patch.json files found.", file=sys.stderr)
        sys.exit(1)

    mode = "APPLY" if args.confirm else "DRY RUN"
    print(f"\n{'='*60}")
    print(f"  Skill Auditor — Patch Application ({mode})")
    print(f"{'='*60}\n")

    changelog_entries = []

    for patch in patches:
        skill_name = patch.get("skill_name", "unknown")
        skill_path = patch.get("skill_path", "")
        priority = patch.get("priority", "?")

        print(f"[{priority.upper()}] {skill_name}")
        print(f"  Path: {skill_path}")
        print(f"  Fixes: {', '.join(patch.get('fixes_issues', []))}")

        for change in patch.get("changes_made", []):
            print(f"  -> {change}")

        print(f"  Cascade risk: {patch.get('cascade_risk', '?')}")

        result = apply_description_patch(
            skill_path=skill_path,
            current_description=patch.get("current_description", ""),
            proposed_description=patch.get("proposed_description", ""),
            dry_run=not args.confirm,
            backup=args.backup,
        )

        print(f"  Status: {result['status']} -- {result['detail']}")
        if result.get("preview"):
            print(f"  Preview:\n{result['preview']}")
        print()

        changelog_entries.append({
            "skill": skill_name,
            "path": skill_path,
            "status": result["status"],
            "changes": patch.get("changes_made", []),
            "fixes": patch.get("fixes_issues", []),
        })

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(f"# Skill Auditor Changelog\n\n")
        f.write(f"**Date**: {datetime.now(timezone.utc).isoformat()}\n")
        f.write(f"**Mode**: {mode}\n")
        f.write(f"**Patches applied**: {len(changelog_entries)}\n\n")

        for entry in changelog_entries:
            f.write(f"## {entry['skill']}\n\n")
            f.write(f"- **Path**: `{entry['path']}`\n")
            f.write(f"- **Status**: {entry['status']}\n")
            f.write(f"- **Fixes**:\n")
            for fix in entry["fixes"]:
                f.write(f"  - {fix}\n")
            f.write(f"- **Changes**:\n")
            for change in entry["changes"]:
                f.write(f"  - {change}\n")
            f.write("\n")

    print(f"Changelog written to: {args.output}")

    if not args.confirm:
        print(
            "\nThis was a dry run. To apply changes, re-run with --confirm"
        )


if __name__ == "__main__":
    main()
