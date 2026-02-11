#!/usr/bin/env python3
"""
generate_report.py — Generate a self-contained HTML report from docs audit results.

Usage:
    python3 generate_report.py --workspace <dir> [--output <path>]
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path


def load_json_safe(filepath: str) -> dict | list | None:
    """Load a JSON file, returning None if it doesn't exist or fails."""
    if not os.path.isfile(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"WARNING: Could not load {filepath}: {e}", file=sys.stderr)
        return None


def find_template() -> str | None:
    """Find the HTML template relative to this script's location."""
    script_dir = Path(__file__).resolve().parent.parent
    template = script_dir / "assets" / "report_template.html"
    if template.is_file():
        return str(template)
    return None


def generate_report(workspace: str, template_path: str | None = None) -> str:
    """Generate HTML report from workspace data."""
    impact = load_json_safe(os.path.join(workspace, "doc-impact-report.json"))
    always_on = load_json_safe(os.path.join(workspace, "always-on-report.json"))
    portfolio = load_json_safe(os.path.join(workspace, "portfolio-analysis.json"))
    plan = load_json_safe(os.path.join(workspace, "improvement-plan.json"))
    manifest = load_json_safe(os.path.join(workspace, "doc-manifest.json"))

    # Try loading health history from parent dir
    base_dir = os.path.dirname(workspace)
    history = load_json_safe(os.path.join(base_dir, "health-history.json"))

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "doc_impact_report": impact,
        "always_on_report": always_on,
        "portfolio_analysis": portfolio,
        "improvement_plan": plan,
        "doc_manifest": manifest,
        "health_history": history or [],
    }

    if template_path and os.path.isfile(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        html = _builtin_template()

    json_data = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    html = html.replace("/*__EMBEDDED_DATA__*/", f"const REPORT_DATA = {json_data};")

    return html


def _builtin_template() -> str:
    """Fallback template if assets/report_template.html is not found."""
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>Docs Audit Report</title>
<style>:root{--bg:#faf9f5;--fg:#141413;--accent:#d97757;--success:#788c5d;--error:#c44;--info:#6a9bcc;--border:#e0ddd8;--card-bg:#fff;--muted:#666}*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:var(--bg);color:var(--fg);line-height:1.6;padding:2rem;max-width:1200px;margin:0 auto}.empty{text-align:center;color:var(--muted);padding:2rem;font-style:italic}</style>
</head><body><h1>Docs Audit Report</h1>
<div class="empty">Template not found. Use --template or place report_template.html in assets/.</div>
<script>/*__EMBEDDED_DATA__*/</script></body></html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate HTML docs audit report")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--template", default=None)
    args = parser.parse_args()

    if not os.path.isdir(args.workspace):
        print(f"ERROR: Workspace not found: {args.workspace}", file=sys.stderr)
        sys.exit(1)

    template = args.template or find_template()
    output = args.output or os.path.join(args.workspace, "docs-audit-report.html")

    html = generate_report(args.workspace, template)
    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report generated: {output}")


if __name__ == "__main__":
    main()
