#!/usr/bin/env python3
"""
collect_transcripts.py — Collect Claude Code session transcripts for doc analysis.

Forked from skill-auditor's collect_transcripts.py. Detects document reads
(docs/*.md, CLAUDE.md, AGENTS.md, ADR-*.md, README.md) instead of SKILL.md loads.

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
import re
import sys
import glob
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path


# Patterns that identify documentation reads
DOC_PATTERNS = [
    (re.compile(r"(?:^|/)CLAUDE\.md$"), "claude_md"),
    (re.compile(r"(?:^|/)AGENTS\.md$"), "agents_md"),
    (re.compile(r"(?:^|/)README\.md$"), "readme"),
    (re.compile(r"(?:^|/)docs/adr/.*\.md$"), "adr"),
    (re.compile(r"(?:^|/)docs/.*\.md$"), "general_doc"),
]


def encode_project_path(working_dir: str) -> str:
    """Convert a working directory to Claude's encoded project directory name."""
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

    if os.path.isdir(project_path) and project_path.startswith(claude_projects):
        return [project_path]

    direct = os.path.join(claude_projects, project_path)
    if os.path.isdir(direct):
        return [direct]

    encoded = encode_project_path(project_path)
    encoded_path = os.path.join(claude_projects, encoded)
    if os.path.isdir(encoded_path):
        return [encoded_path]

    encoded_trail = encoded.rstrip("-") if encoded.endswith("-") else encoded + "-"
    alt_path = os.path.join(claude_projects, encoded_trail)
    if os.path.isdir(alt_path):
        return [alt_path]

    return []


def auto_detect_project(cwd: str, verbose: bool = False) -> str | None:
    """Auto-detect the Claude project directory from a working directory."""
    claude_projects = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(claude_projects):
        return None

    available = set(os.listdir(claude_projects))
    abs_cwd = os.path.abspath(os.path.expanduser(cwd))

    encoded = encode_project_path(abs_cwd)
    if os.path.basename(encoded) in available:
        return os.path.join(claude_projects, os.path.basename(encoded))

    current = abs_cwd
    while current != os.path.dirname(current):
        current = os.path.dirname(current)
        encoded_parent = encode_project_path(current)
        name = os.path.basename(encoded_parent) if "/" in encoded_parent else encoded_parent
        if name in available:
            if verbose:
                print(f"  Auto-detected project: {name}", file=sys.stderr)
            return os.path.join(claude_projects, name)

    return None


def list_available_projects() -> list[dict]:
    """List all available projects with decoded paths."""
    claude_projects = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(claude_projects):
        return []

    result = []
    for name in sorted(os.listdir(claude_projects)):
        full = os.path.join(claude_projects, name)
        if not os.path.isdir(full):
            continue
        decoded = name.replace("-", "/")
        if not decoded.startswith("/"):
            decoded = "/" + decoded
        sessions = glob.glob(os.path.join(full, "*.jsonl"))
        result.append({
            "encoded": name,
            "decoded": decoded,
            "path": full,
            "session_count": len(sessions),
        })
    return result


def _normalize_jsonl_line(obj: dict) -> dict:
    """Normalize a Claude Code JSONL line into a flat message dict."""
    inner = obj.get("message")
    if not isinstance(inner, dict):
        return obj

    normalized = {}
    for key in ("type", "timestamp", "sessionId", "cwd", "uuid",
                "parentUuid", "userType", "requestId"):
        if key in obj:
            normalized[key] = obj[key]

    for key in ("role", "content", "model", "id", "stop_reason",
                "stop_sequence", "usage"):
        if key in inner:
            if key == "type" and "type" in normalized:
                continue
            normalized[key] = inner[key]

    if "role" not in normalized:
        outer_type = obj.get("type", "")
        role_map = {"human": "user", "user": "user",
                    "assistant": "assistant", "tool_result": "tool"}
        normalized["role"] = role_map.get(outer_type, outer_type)

    return normalized


def _classify_doc_path(path: str) -> tuple[str, str] | None:
    """Classify a file path as a doc type. Returns (filepath, doc_type) or None."""
    if not isinstance(path, str):
        return None
    for pattern, doc_type in DOC_PATTERNS:
        if pattern.search(path):
            return (path, doc_type)
    return None


def _check_doc_read(tool_call: dict, docs_read: list):
    """Check if a tool call is reading a documentation file."""
    name = tool_call.get("name", "")
    inp = tool_call.get("input", {})

    if name in ("view", "Read", "read_file"):
        path = inp.get("path", inp.get("file_path", ""))
        result = _classify_doc_path(path)
        if result:
            docs_read.append(result)

    if name in ("bash", "bash_tool", "execute_command"):
        cmd = inp.get("command", inp.get("cmd", ""))
        if isinstance(cmd, str):
            for token in cmd.split():
                result = _classify_doc_path(token)
                if result:
                    docs_read.append(result)
                    break


def _extract_timestamp(msg: dict) -> str | None:
    """Try to extract a timestamp from a message object."""
    for key in ("timestamp", "created_at", "ts"):
        val = msg.get(key)
        if val:
            return str(val)
    return None


def parse_jsonl_session(filepath: str, verbose: bool = False) -> dict | None:
    """Parse a single .jsonl session file."""
    session_id = Path(filepath).stem
    messages = []
    docs_read = []
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
                        _check_doc_read(block, docs_read)

        if msg_type == "tool_use":
            _check_doc_read(msg, docs_read)

        for tc in msg.get("tool_calls", []):
            if isinstance(tc, dict):
                _check_doc_read(tc, docs_read)

    first_ts = _extract_timestamp(messages[0]) if messages else None
    last_ts = _extract_timestamp(messages[-1]) if messages else None

    # Deduplicate docs_read preserving order
    seen = set()
    unique_docs = []
    for filepath_doc, doc_type in docs_read:
        if filepath_doc not in seen:
            seen.add(filepath_doc)
            unique_docs.append({"filepath": filepath_doc, "doc_type": doc_type})

    result = {
        "session_id": session_id,
        "filepath": filepath,
        "messages": messages,
        "docs_read": unique_docs,
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


CLAUDE_BUILTIN_COMMANDS = frozenset([
    "help", "clear", "compact", "model", "usage", "cost", "login", "logout",
    "status", "config", "permissions", "doctor", "review", "init", "memory",
    "mcp", "fast", "slow", "vim", "emacs", "terminal-setup", "tools", "tasks",
    "bug", "quit", "exit", "diff", "undo", "resume", "ide", "add-dir",
    "release-notes", "listen", "pr-comments",
])


def _is_builtin_command(msg: str) -> bool:
    """Check if a user message is a Claude Code built-in CLI command."""
    msg = msg.strip()
    if not msg.startswith("/"):
        return False
    cmd = msg.lstrip("/").split()[0].split("\n")[0].lower() if msg else ""
    return cmd in CLAUDE_BUILTIN_COMMANDS


def _extract_docs_from_msg(msg: dict, docs_list: list):
    """Extract any doc reads from a message."""
    msg_type = msg.get("type", msg.get("role", ""))

    if msg_type in ("assistant",):
        content = msg.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    _check_doc_read(block, docs_list)

    if msg_type == "tool_use":
        _check_doc_read(msg, docs_list)

    for tc in msg.get("tool_calls", []):
        if isinstance(tc, dict):
            _check_doc_read(tc, docs_list)


def _build_turn_doc_map(messages: list[dict]) -> list[dict]:
    """For each user turn, find which docs were read between that turn and the next."""
    result = []
    turn_index = 0
    current_user_msg = None
    docs_since_last_turn = []

    for msg in messages:
        msg_type = msg.get("type", msg.get("role", ""))

        if msg_type in ("human", "user"):
            if current_user_msg is not None:
                # Deduplicate
                seen = set()
                unique = []
                for fp, dt in docs_since_last_turn:
                    if fp not in seen:
                        seen.add(fp)
                        unique.append({"filepath": fp, "doc_type": dt})

                result.append({
                    "turn_index": turn_index,
                    "user_message": current_user_msg,
                    "docs_read_after": unique,
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
            docs_since_last_turn = []

        else:
            _extract_docs_from_msg_raw(msg, docs_since_last_turn)

    if current_user_msg is not None:
        seen = set()
        unique = []
        for fp, dt in docs_since_last_turn:
            if fp not in seen:
                seen.add(fp)
                unique.append({"filepath": fp, "doc_type": dt})

        result.append({
            "turn_index": turn_index,
            "user_message": current_user_msg,
            "docs_read_after": unique,
            "is_builtin_command": _is_builtin_command(current_user_msg),
        })

    return result


def _extract_docs_from_msg_raw(msg: dict, docs_list: list):
    """Extract doc reads as raw (filepath, doc_type) tuples."""
    msg_type = msg.get("type", msg.get("role", ""))

    if msg_type in ("assistant",):
        content = msg.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    _check_doc_read(block, docs_list)

    if msg_type == "tool_use":
        _check_doc_read(msg, docs_list)

    for tc in msg.get("tool_calls", []):
        if isinstance(tc, dict):
            _check_doc_read(tc, docs_list)


def _extract_project_dir(session_filepath: str) -> str | None:
    """Extract the encoded project directory name from a session filepath."""
    parts = Path(session_filepath).parts
    for i, part in enumerate(parts):
        if part == "projects" and i + 1 < len(parts):
            return parts[i + 1]
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
    """Main collection function."""
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

    all_docs = set()
    total_turns = 0
    for s in all_sessions:
        for d in s["docs_read"]:
            all_docs.add(d["filepath"])
        total_turns += s["user_turn_count"]

    # Build slim sessions with turn_doc_map
    sessions_slim = []
    for s in all_sessions:
        slim = {k: v for k, v in s.items()
                if k not in ("messages", "user_turns")}
        turn_doc_map = _build_turn_doc_map(s["messages"])
        slim["turn_doc_map"] = turn_doc_map
        slim["project_dir"] = _extract_project_dir(s["filepath"])
        sessions_slim.append(slim)

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
            "unique_docs_read": sorted(all_docs),
            "parse_errors": len(parse_errors),
            "sessions_by_project": sessions_by_project,
        },
        "parse_error_files": parse_errors if parse_errors else [],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Collect Claude Code session transcripts for doc analysis"
    )
    parser.add_argument(
        "project_path", nargs="?", default=None,
        help='Project path, encoded directory name, or "all".',
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
        f"{len(summary['unique_docs_read'])} unique docs read"
    )
    if summary["parse_errors"]:
        print(f"  ({summary['parse_errors']} sessions had parse errors)")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
