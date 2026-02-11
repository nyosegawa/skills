#!/usr/bin/env python3
"""
collect_skills.py — Gather all skill definitions into a structured manifest.

Scans skill directories and extracts metadata from each SKILL.md file.
Includes description token counting for attention budget analysis.

Usage:
    python3 collect_skills.py [options]

Options:
    --skill-dirs DIR [DIR ...]   Directories to scan (default: standard locations)
    --output PATH                Output file path (default: ./skill-manifest.json)
    --verbose                    Print progress details
"""

import json
import os
import re
import sys
import argparse
from pathlib import Path

# Token counting: tiktoken preferred, character-based fallback
try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        return len(_enc.encode(text))
except ImportError:
    def count_tokens(text: str) -> int:
        # Rough approximation: 1 token ~= 4 chars for English
        return max(1, len(text) // 4)


# Standard skill locations in Claude Code
DEFAULT_SKILL_DIRS = [
    "/mnt/skills/public",
    "/mnt/skills/private",
    "/mnt/skills/examples",
    "/mnt/skills/user",
    os.path.expanduser("~/.claude/skills"),
    ".claude/skills",
]


def parse_skill_md(filepath: str) -> dict | None:
    """Parse a SKILL.md file and extract structured metadata."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {"error": str(e), "filepath": filepath}

    resolved = os.path.realpath(filepath)
    result = {
        "filepath": filepath,
        "filepath_resolved": resolved if resolved != filepath else None,
        "name": None,
        "description": None,
        "trigger": None,
        "body_preview": None,
        "full_content_length": len(content),
    }

    # Parse YAML frontmatter
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if frontmatter_match:
        fm_text = frontmatter_match.group(1)
        result.update(_parse_yaml_simple(fm_text))
        body = content[frontmatter_match.end():]
    else:
        body = content

    if not result["name"]:
        result["name"] = Path(filepath).parent.name

    # Body preview
    body = body.strip()
    if body:
        lines = body.split("\n")
        preview_lines = []
        heading_count = 0
        for line in lines:
            if line.startswith("#") and preview_lines:
                heading_count += 1
                if heading_count >= 2:
                    break
            preview_lines.append(line)
            if sum(len(l) for l in preview_lines) > 500:
                break
        result["body_preview"] = "\n".join(preview_lines).strip()

    result["description_raw"] = result.get("description", "")

    # Check disable-model-invocation flag
    dmi = result.get("disable-model-invocation", "")
    result["disable_model_invocation"] = str(dmi).lower() in ("true", "yes", "1")

    # Token counting for attention budget analysis
    desc = result.get("description", "") or ""
    result["description_tokens"] = count_tokens(desc) if desc else 0

    return result


def _parse_yaml_simple(text: str) -> dict:
    """Simple YAML-like parser for frontmatter."""
    result = {}
    current_key = None
    current_value_lines = []
    is_multiline = False

    for line in text.split("\n"):
        key_match = re.match(r"^(\w[\w-]*)\s*:\s*(.*)", line)
        if key_match and not (is_multiline and line.startswith(" ")):
            if current_key:
                result[current_key] = _finalize_value(current_value_lines, is_multiline)

            current_key = key_match.group(1).lower()
            value = key_match.group(2).strip()

            if value in (">", "|", ">-", "|-"):
                is_multiline = True
                current_value_lines = []
            else:
                is_multiline = False
                current_value_lines = [value.strip("'\"")]
        elif current_key and is_multiline:
            current_value_lines.append(line.strip())

    if current_key:
        result[current_key] = _finalize_value(current_value_lines, is_multiline)

    return result


def _finalize_value(lines: list[str], is_multiline: bool) -> str:
    if is_multiline:
        return " ".join(l for l in lines if l).strip()
    return lines[0] if lines else ""


def discover_project_skill_dirs(verbose: bool = False) -> list[tuple[str, str]]:
    """Discover .claude/skills/ directories inside known project roots.

    Returns list of (skill_dir, project_root) tuples.
    """
    claude_projects = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(claude_projects):
        return []

    results = []
    for name in os.listdir(claude_projects):
        full = os.path.join(claude_projects, name)
        if not os.path.isdir(full):
            continue
        decoded = name.lstrip("-")
        parts = decoded.split("-")
        # Try simple slash-join first
        candidate = "/" + "/".join(parts)
        skill_dir = os.path.join(candidate, ".claude", "skills")
        if os.path.isdir(skill_dir):
            if verbose:
                print(f"  Project-local skills: {skill_dir}", file=sys.stderr)
            results.append((skill_dir, candidate))
            continue
        # Try reconstructing dots (github-com -> github.com, etc.)
        for i in range(len(parts) - 1):
            dotted = parts[:i] + [parts[i] + "." + parts[i + 1]] + parts[i + 2:]
            candidate = "/" + "/".join(dotted)
            skill_dir = os.path.join(candidate, ".claude", "skills")
            if os.path.isdir(skill_dir):
                if verbose:
                    print(f"  Project-local skills: {skill_dir}", file=sys.stderr)
                results.append((skill_dir, candidate))
                break

    return results


def find_skills(
    skill_dirs: list[str],
    project_skill_dirs: list[tuple[str, str]] | None = None,
    verbose: bool = False,
) -> list[dict]:
    """Find all SKILL.md files in the given directories.

    skill_dirs: global skill directories (scope="global")
    project_skill_dirs: list of (dir, project_root) tuples (scope="project-local")
    """
    skills = []
    seen_paths = set()

    def _scan(base_dir: str, scope: str, project_path: str | None):
        base_dir = os.path.expanduser(base_dir)
        if not os.path.isdir(base_dir):
            if verbose:
                print(f"  Skipping (not found): {base_dir}", file=sys.stderr)
            return

        for root, dirs, files in os.walk(base_dir, followlinks=True):
            if "SKILL.md" in files:
                fp = os.path.join(root, "SKILL.md")
                real_fp = os.path.realpath(fp)
                if real_fp in seen_paths:
                    continue
                seen_paths.add(real_fp)

                if verbose:
                    print(f"  Found: {fp}", file=sys.stderr)

                parsed = parse_skill_md(fp)
                if parsed:
                    if "/public/" in fp:
                        parsed["category"] = "public"
                    elif "/private/" in fp:
                        parsed["category"] = "private"
                    elif "/examples/" in fp:
                        parsed["category"] = "example"
                    elif "/user/" in fp or "/.claude/skills/" in fp:
                        parsed["category"] = "user"
                    else:
                        parsed["category"] = "other"
                    parsed["scope"] = scope
                    parsed["project_path"] = project_path
                    skills.append(parsed)

    for base_dir in skill_dirs:
        _scan(base_dir, scope="global", project_path=None)

    for pdir, project_root in (project_skill_dirs or []):
        _scan(pdir, scope="project-local", project_path=project_root)

    return skills


def collect(skill_dirs: list[str] | None = None, verbose: bool = False,
            include_project_skills: bool = True) -> dict:
    """Main collection function. Returns structured manifest with attention budget."""
    global_dirs = list(skill_dirs or DEFAULT_SKILL_DIRS)
    project_skill_dirs = []
    if include_project_skills:
        project_skill_dirs = discover_project_skill_dirs(verbose=verbose)
    skills = find_skills(
        global_dirs,
        project_skill_dirs=project_skill_dirs,
        verbose=verbose,
    )

    skills.sort(key=lambda s: (s.get("scope", ""), s.get("category", ""), s.get("name", "")))

    # Description overlap analysis
    descriptions = {}
    for s in skills:
        desc = s.get("description", "") or ""
        if desc:
            descriptions[s["name"]] = desc.lower()

    overlaps = []
    skill_names = list(descriptions.keys())
    for i in range(len(skill_names)):
        for j in range(i + 1, len(skill_names)):
            a, b = skill_names[i], skill_names[j]
            words_a = set(descriptions[a].split())
            words_b = set(descriptions[b].split())
            stop = {"a", "an", "the", "is", "are", "for", "to", "of", "in",
                    "and", "or", "this", "that", "with", "use", "when", "it",
                    "not", "do", "be", "as", "on", "at", "by", "if", "any"}
            words_a -= stop
            words_b -= stop
            shared = words_a & words_b
            if len(shared) >= 3:
                overlaps.append({
                    "skill_a": a,
                    "skill_b": b,
                    "shared_keywords": sorted(shared),
                    "shared_count": len(shared),
                })

    overlaps.sort(key=lambda o: o["shared_count"], reverse=True)

    # Attention budget statistics
    token_counts = [s.get("description_tokens", 0) for s in skills if s.get("description")]
    total_tokens = sum(token_counts)
    mean_tokens = total_tokens / len(token_counts) if token_counts else 0
    sorted_counts = sorted(token_counts)
    median_tokens = (
        sorted_counts[len(sorted_counts) // 2]
        if sorted_counts
        else 0
    )

    # Per-project attention budget: each project sees global + its own local skills
    project_budgets = {}
    global_skills = [s for s in skills if s.get("scope") == "global"]
    global_tokens = sum(s.get("description_tokens", 0) for s in global_skills if s.get("description"))
    project_paths = sorted(set(
        s["project_path"] for s in skills
        if s.get("scope") == "project-local" and s.get("project_path")
    ))
    for pp in project_paths:
        local_skills = [s for s in skills if s.get("project_path") == pp]
        local_tokens = sum(s.get("description_tokens", 0) for s in local_skills if s.get("description"))
        project_budgets[pp] = {
            "global_tokens": global_tokens,
            "local_tokens": local_tokens,
            "total_tokens": global_tokens + local_tokens,
            "local_skill_names": [s["name"] for s in local_skills],
        }

    all_dirs = global_dirs + [d for d, _ in project_skill_dirs]

    return {
        "collected_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "skill_dirs_scanned": all_dirs,
        "skills": skills,
        "summary": {
            "total_skills": len(skills),
            "by_category": _count_by(skills, "category"),
            "by_scope": _count_by(skills, "scope"),
            "skills_without_description": [
                s["name"] for s in skills if not s.get("description")
            ],
        },
        "attention_budget": {
            "total_description_tokens": total_tokens,
            "global_description_tokens": global_tokens,
            "mean_tokens_per_skill": round(mean_tokens, 1),
            "median_tokens_per_skill": median_tokens,
            "max_tokens": max(token_counts) if token_counts else 0,
            "min_tokens": min(token_counts) if token_counts else 0,
            "skills_above_2x_median": [
                s["name"] for s in skills
                if s.get("description_tokens", 0) > median_tokens * 2
                and median_tokens > 0
            ],
            "per_project": project_budgets,
        },
        "description_overlaps": overlaps,
    }


def _count_by(items: list[dict], key: str) -> dict:
    counts = {}
    for item in items:
        val = item.get(key, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts


def main():
    parser = argparse.ArgumentParser(
        description="Collect skill definitions into a structured manifest"
    )
    parser.add_argument(
        "--skill-dirs", nargs="+", default=None,
        help="Directories to scan for skills (default: standard locations)",
    )
    parser.add_argument(
        "--output", default="./skill-manifest.json",
        help="Output file path (default: ./skill-manifest.json)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print progress details",
    )
    parser.add_argument(
        "--no-project-skills", action="store_true",
        help="Skip scanning project-local .claude/skills/ directories",
    )

    args = parser.parse_args()
    result = collect(
        skill_dirs=args.skill_dirs,
        verbose=args.verbose,
        include_project_skills=not args.no_project_skills,
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    summary = result["summary"]
    budget = result["attention_budget"]
    by_scope = summary.get("by_scope", {})
    print(f"Found {summary['total_skills']} skills "
          f"({by_scope.get('global', 0)} global, "
          f"{by_scope.get('project-local', 0)} project-local)")
    print(f"  Attention budget: {budget['total_description_tokens']} tokens total "
          f"({budget.get('global_description_tokens', 0)} global), "
          f"median {budget['median_tokens_per_skill']} per skill")
    for pp, pb in budget.get("per_project", {}).items():
        print(f"  Project {os.path.basename(pp)}: "
              f"{pb['total_tokens']} tokens ({pb['local_tokens']} local + "
              f"{pb['global_tokens']} global), "
              f"skills: {', '.join(pb['local_skill_names'])}")
    if budget["skills_above_2x_median"]:
        print(f"  Oversized descriptions (>2x median): "
              f"{', '.join(budget['skills_above_2x_median'])}")
    if summary["skills_without_description"]:
        print(f"  Warning: {len(summary['skills_without_description'])} skills "
              f"have no description")
    if result["description_overlaps"]:
        top = result["description_overlaps"][0]
        print(f"  Highest keyword overlap: {top['skill_a']} <-> {top['skill_b']} "
              f"({top['shared_count']} shared words)")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
