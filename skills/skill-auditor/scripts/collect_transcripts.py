#!/usr/bin/env python3
"""
collect_transcripts.py — Collect and parse Claude Code session transcripts.

Reads .jsonl session files from ~/.claude/projects/ and produces a structured
JSON file suitable for routing analysis.

Usage:
    python3 collect_transcripts.py <project-path> [options]

Arguments:
    project-path    Path to a Claude project directory under ~/.claude/projects/,
                    OR a direct project working directory (auto-resolves the
                    encoded path). Use "all" to scan all projects.

Options:
    --days N        Only include sessions from the last N days (default: 14)
    --output PATH   Output file path (default: ./transcripts.json)
    --min-turns N   Skip sessions with fewer than N user turns (default: 1)
    --verbose       Print progress and parsing details
"""

import json
import os
import sys
import glob
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path


def encode_project_path(working_dir: str) -> str:
    """Convert a working directory to Claude's encoded project directory name.

    Claude Code encodes /Users/sakasegawa/src/github.com/nyosegawa/aituber as
    -Users-sakasegawa-src-github-com-nyosegawa-aituber
    (replace / and . with -, no trailing -)
    """
    abs_path = os.path.abspath(os.path.expanduser(working_dir))
    encoded = abs_path.replace("/", "-").replace(".", "-")
    if not encoded.startswith("-"):
        encoded = "-" + encoded
    return encoded


def find_project_dir(project_path: str) -> list[str]:
    """Resolve project_path to one or more ~/.claude/projects/ directories."""
    claude_projects = os.path.expanduser("~/.claude/projects")

    if project_path == "all":
        if not os.path.isdir(claude_projects):
            return []
        return [
            os.path.join(claude_projects, d)
            for d in os.listdir(claude_projects)
            if os.path.isdir(os.path.join(claude_projects, d))
        ]

    # Direct path to a claude projects subdirectory
    if os.path.isdir(project_path) and project_path.startswith(claude_projects):
        return [project_path]

    # Path under ~/.claude/projects/ by name
    direct = os.path.join(claude_projects, project_path)
    if os.path.isdir(direct):
        return [direct]

    # Working directory — encode it and try exact match
    encoded = encode_project_path(project_path)
    encoded_path = os.path.join(claude_projects, encoded)
    if os.path.isdir(encoded_path):
        return [encoded_path]

    # Fuzzy: try without trailing dash (backward compat)
    encoded_trail = encoded.rstrip("-") if encoded.endswith("-") else encoded + "-"
    alt_path = os.path.join(claude_projects, encoded_trail)
    if os.path.isdir(alt_path):
        return [alt_path]

    return []


def auto_detect_project(cwd: str, verbose: bool = False) -> str | None:
    """Auto-detect the Claude project directory from a working directory.

    Strategy:
    1. Exact match: encode cwd -> check if dir exists
    2. Walk up parent dirs: maybe cwd is a subdirectory of the project root
    3. Return None if no match found (caller should prompt user)
    """
    claude_projects = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(claude_projects):
        return None

    available = set(os.listdir(claude_projects))
    abs_cwd = os.path.abspath(os.path.expanduser(cwd))

    # Try exact match first
    encoded = encode_project_path(abs_cwd)
    if os.path.basename(encoded) in available:
        return os.path.join(claude_projects, os.path.basename(encoded))

    # Walk up parent directories (cwd might be a subdir of the project)
    current = abs_cwd
    while current != os.path.dirname(current):  # stop at root
        current = os.path.dirname(current)
        encoded_parent = encode_project_path(current)
        name = os.path.basename(encoded_parent) if "/" in encoded_parent else encoded_parent
        if name in available:
            if verbose:
                print(f"  Auto-detected project: {name} (from parent of cwd)",
                      file=sys.stderr)
            return os.path.join(claude_projects, name)

    return None


def list_available_projects() -> list[dict]:
    """List all available projects with decoded paths for display."""
    claude_projects = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(claude_projects):
        return []

    result = []
    for name in sorted(os.listdir(claude_projects)):
        full = os.path.join(claude_projects, name)
        if not os.path.isdir(full):
            continue

        # Decode: -Users-sakasegawa-src-... -> /Users/sakasegawa/src/...
        decoded = name.replace("-", "/")
        if decoded.startswith("/"):
            pass  # already correct
        else:
            decoded = "/" + decoded

        # Count sessions
        sessions = glob.glob(os.path.join(full, "*.jsonl"))

        result.append({
            "encoded": name,
            "decoded": decoded,
            "path": full,
            "session_count": len(sessions),
        })

    return result


def _normalize_jsonl_line(obj: dict) -> dict:
    """Normalize a Claude Code JSONL line into a flat message dict.

    Claude Code wraps API messages in an envelope. We flatten this so that
    content is directly accessible. If already flat, pass through unchanged.
    """
    inner = obj.get("message")
    if not isinstance(inner, dict):
        return obj

    normalized = {}

    # Preserve envelope-level fields
    for key in ("type", "timestamp", "sessionId", "cwd", "uuid",
                "parentUuid", "userType", "requestId"):
        if key in obj:
            normalized[key] = obj[key]

    # Promote inner message fields to top level
    for key in ("role", "content", "model", "id", "stop_reason",
                "stop_sequence", "usage"):
        if key in inner:
            if key == "type" and "type" in normalized:
                continue
            normalized[key] = inner[key]

    # Ensure "role" is set from either inner message or outer type
    if "role" not in normalized:
        outer_type = obj.get("type", "")
        role_map = {"human": "user", "user": "user",
                    "assistant": "assistant", "tool_result": "tool"}
        normalized["role"] = role_map.get(outer_type, outer_type)

    return normalized


def parse_jsonl_session(filepath: str, verbose: bool = False) -> dict | None:
    """Parse a single .jsonl session file into structured data."""
    session_id = Path(filepath).stem
    messages = []
    skills_loaded = []
    user_turns = []
    errors = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    obj = _normalize_jsonl_line(obj)
                    messages.append(obj)
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: {e}")
    except Exception as e:
        if verbose:
            print(f"  ERROR reading {filepath}: {e}", file=sys.stderr)
        return None

    if not messages:
        return None

    # Extract user turns and skill loads
    for msg in messages:
        msg_type = msg.get("type", msg.get("role", ""))

        if msg_type in ("human", "user"):
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                user_turns.append(content.strip())
            elif isinstance(content, list):
                text_parts = [
                    p.get("text", "") for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                combined = " ".join(t for t in text_parts if t).strip()
                if combined:
                    user_turns.append(combined)

        if msg_type in ("assistant",):
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        _check_skill_load(block, skills_loaded)

        if msg_type == "tool_use":
            _check_skill_load(msg, skills_loaded)

        for tc in msg.get("tool_calls", []):
            if isinstance(tc, dict):
                _check_skill_load(tc, skills_loaded)

    first_ts = _extract_timestamp(messages[0]) if messages else None
    last_ts = _extract_timestamp(messages[-1]) if messages else None

    result = {
        "session_id": session_id,
        "filepath": filepath,
        "messages": messages,
        "skills_loaded": list(dict.fromkeys(skills_loaded)),
        "user_turns": user_turns,
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "message_count": len(messages),
        "user_turn_count": len(user_turns),
    }

    if errors and verbose:
        print(f"  WARN {session_id}: {len(errors)} parse errors", file=sys.stderr)
        result["parse_errors"] = errors

    return result


# Claude Code built-in CLI commands — these are NOT skill invocations
CLAUDE_BUILTIN_COMMANDS = frozenset([
    "help", "clear", "compact", "model", "usage", "cost", "login", "logout",
    "status", "config", "permissions", "doctor", "review", "init", "memory",
    "mcp", "fast", "slow", "vim", "emacs", "terminal-setup", "tools", "tasks",
    "bug", "quit", "exit", "diff", "undo", "resume", "ide", "add-dir",
    "release-notes", "listen", "pr-comments",
])


def _check_skill_load(tool_call: dict, skills_loaded: list):
    """Check if a tool call is loading a skill (viewing a SKILL.md file)."""
    name = tool_call.get("name", "")
    inp = tool_call.get("input", {})

    if name in ("view", "Read", "read_file"):
        path = inp.get("path", inp.get("file_path", ""))
        if isinstance(path, str) and "SKILL.md" in path:
            skills_loaded.append(path)

    if name in ("bash", "bash_tool", "execute_command"):
        cmd = inp.get("command", inp.get("cmd", ""))
        if isinstance(cmd, str) and "SKILL.md" in cmd:
            for token in cmd.split():
                if "SKILL.md" in token:
                    skills_loaded.append(token)
                    break


def _extract_timestamp(msg: dict) -> str | None:
    """Try to extract a timestamp from a message object."""
    for key in ("timestamp", "created_at", "ts"):
        val = msg.get(key)
        if val:
            return str(val)
    return None


def filter_by_date(sessions: list[dict], days: int) -> list[dict]:
    """Filter sessions to only those within the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    filtered = []

    for s in sessions:
        ts = s.get("first_timestamp")
        if ts is None:
            filtered.append(s)
            continue

        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt >= cutoff:
                filtered.append(s)
        except (ValueError, TypeError):
            try:
                dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
                if dt >= cutoff:
                    filtered.append(s)
            except (ValueError, TypeError):
                filtered.append(s)

    return filtered


def collect(
    project_path: str,
    days: int = 14,
    min_turns: int = 1,
    verbose: bool = False,
) -> dict:
    """Main collection function. Returns structured JSON with session data."""
    project_dirs = find_project_dir(project_path)
    if not project_dirs:
        return {
            "error": f"No project directory found for: {project_path}",
            "hint": "Check ~/.claude/projects/ for available projects, "
                    "or use 'all' to scan everything.",
        }

    all_sessions = []
    parse_errors = []

    for pdir in project_dirs:
        jsonl_files = glob.glob(os.path.join(pdir, "*.jsonl"))
        if verbose:
            print(f"Scanning {pdir}: {len(jsonl_files)} session files", file=sys.stderr)

        for fp in sorted(jsonl_files):
            basename = Path(fp).name
            if basename == "history.jsonl":
                continue

            session = parse_jsonl_session(fp, verbose=verbose)
            if session is None:
                parse_errors.append(fp)
                continue

            if session["user_turn_count"] >= min_turns:
                all_sessions.append(session)

    if days > 0:
        before = len(all_sessions)
        all_sessions = filter_by_date(all_sessions, days)
        if verbose:
            print(
                f"Date filter: {before} -> {len(all_sessions)} sessions "
                f"(last {days} days)",
                file=sys.stderr,
            )

    all_sessions.sort(
        key=lambda s: s.get("first_timestamp") or "",
        reverse=True,
    )

    all_skills = set()
    total_turns = 0
    for s in all_sessions:
        all_skills.update(s["skills_loaded"])
        total_turns += s["user_turn_count"]

    # Strip raw messages — turn_skill_map has all the routing analysis needs
    sessions_slim = []
    for s in all_sessions:
        slim = {k: v for k, v in s.items()
                if k not in ("messages", "user_turns")}
        turn_skill_map = _build_turn_skill_map(s["messages"])
        slim["turn_skill_map"] = turn_skill_map
        slim["project_dir"] = _extract_project_dir(s["filepath"])
        sessions_slim.append(slim)

    # Per-project session counts
    sessions_by_project = {}
    for s in sessions_slim:
        pdir = s.get("project_dir", "unknown")
        sessions_by_project[pdir] = sessions_by_project.get(pdir, 0) + 1

    return {
        "project_path": project_path,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "config": {"days": days, "min_turns": min_turns},
        "sessions": sessions_slim,
        "summary": {
            "total_sessions": len(sessions_slim),
            "total_user_turns": total_turns,
            "unique_skills_loaded": sorted(all_skills),
            "skills_never_loaded": [],
            "parse_errors": len(parse_errors),
            "sessions_by_project": sessions_by_project,
        },
        "parse_error_files": parse_errors if parse_errors else [],
    }


def _build_turn_skill_map(messages: list[dict]) -> list[dict]:
    """For each user turn, find which skills were loaded between that turn
    and the next user turn."""
    result = []
    turn_index = 0
    current_user_msg = None
    skills_since_last_turn = []

    for msg in messages:
        msg_type = msg.get("type", msg.get("role", ""))

        if msg_type in ("human", "user"):
            if current_user_msg is not None:
                result.append({
                    "turn_index": turn_index,
                    "user_message": current_user_msg,
                    "skills_loaded_after": list(dict.fromkeys(skills_since_last_turn)),
                    "is_builtin_command": _is_builtin_command(current_user_msg),
                })
                turn_index += 1

            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = [
                    p.get("text", "") for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                content = " ".join(t for t in text_parts if t)
            current_user_msg = content.strip() if isinstance(content, str) else ""
            skills_since_last_turn = []

        else:
            _extract_skills_from_msg(msg, skills_since_last_turn)

    if current_user_msg is not None:
        result.append({
            "turn_index": turn_index,
            "user_message": current_user_msg,
            "skills_loaded_after": list(dict.fromkeys(skills_since_last_turn)),
            "is_builtin_command": _is_builtin_command(current_user_msg),
        })

    return result


def _extract_project_dir(session_filepath: str) -> str | None:
    """Extract the encoded project directory name from a session filepath.

    Session files live at ~/.claude/projects/<encoded-project-dir>/<uuid>.jsonl.
    Returns the encoded dir name (e.g., '-Users-sakasegawa-src-github-com-nyosegawa-aituber').
    """
    parts = Path(session_filepath).parts
    # Find 'projects' in the path and take the next segment
    for i, part in enumerate(parts):
        if part == "projects" and i + 1 < len(parts):
            return parts[i + 1]
    return None


def _is_builtin_command(msg: str) -> bool:
    """Check if a user message is a Claude Code built-in CLI command."""
    msg = msg.strip()
    if not msg.startswith("/"):
        return False
    cmd = msg.lstrip("/").split()[0].split("\n")[0].lower() if msg else ""
    return cmd in CLAUDE_BUILTIN_COMMANDS


def _extract_skills_from_msg(msg: dict, skills_list: list):
    """Extract any skill SKILL.md loads from a message."""
    msg_type = msg.get("type", msg.get("role", ""))

    if msg_type in ("assistant",):
        content = msg.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    _check_skill_load(block, skills_list)

    if msg_type == "tool_use":
        _check_skill_load(msg, skills_list)

    for tc in msg.get("tool_calls", []):
        if isinstance(tc, dict):
            _check_skill_load(tc, skills_list)


def main():
    parser = argparse.ArgumentParser(
        description="Collect Claude Code session transcripts for skill routing analysis"
    )
    parser.add_argument(
        "project_path", nargs="?", default=None,
        help='Project path, encoded directory name, or "all". '
             'If omitted, auto-detects from --cwd.',
    )
    parser.add_argument(
        "--cwd", default=None,
        help="Working directory to auto-detect project from",
    )
    parser.add_argument(
        "--list", action="store_true", dest="list_projects",
        help="List all available projects and exit",
    )
    parser.add_argument(
        "--days", type=int, default=14,
        help="Include sessions from the last N days (default: 14, 0=all)",
    )
    parser.add_argument(
        "--output", default="./transcripts.json",
        help="Output file path (default: ./transcripts.json)",
    )
    parser.add_argument(
        "--min-turns", type=int, default=1,
        help="Skip sessions with fewer than N user turns (default: 1)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print progress details",
    )

    args = parser.parse_args()

    if args.list_projects:
        projects = list_available_projects()
        if not projects:
            print("No projects found in ~/.claude/projects/", file=sys.stderr)
            sys.exit(1)
        print(f"Found {len(projects)} projects:\n")
        for p in projects:
            print(f"  {p['decoded']}")
            print(f"    encoded: {p['encoded']}")
            print(f"    sessions: {p['session_count']}")
            print()
        sys.exit(0)

    project_path = args.project_path

    if project_path is None and args.cwd:
        detected = auto_detect_project(args.cwd, verbose=args.verbose)
        if detected:
            project_path = detected
            print(f"Auto-detected project: {os.path.basename(detected)}",
                  file=sys.stderr)
        else:
            print(f"ERROR: Could not auto-detect project from cwd: {args.cwd}",
                  file=sys.stderr)
            print(f"\nAvailable projects:", file=sys.stderr)
            for p in list_available_projects():
                print(f"  {p['decoded']}  ({p['session_count']} sessions)",
                      file=sys.stderr)
            sys.exit(1)
    elif project_path is None:
        print("ERROR: No project path specified. Use a path argument, "
              "--cwd for auto-detect, or --list to see available projects.",
              file=sys.stderr)
        sys.exit(1)

    result = collect(
        project_path,
        days=args.days,
        min_turns=args.min_turns,
        verbose=args.verbose,
    )

    if "error" in result:
        print(json.dumps(result, indent=2), file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    summary = result["summary"]
    print(
        f"Collected {summary['total_sessions']} sessions, "
        f"{summary['total_user_turns']} user turns, "
        f"{len(summary['unique_skills_loaded'])} unique skills loaded"
    )
    if summary["parse_errors"]:
        print(f"  ({summary['parse_errors']} sessions had parse errors)")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
