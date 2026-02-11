# Architecture

## Design Decisions

### Fork vs. Shared collect_transcripts.py

The transcript collector is forked from skill-auditor rather than shared.
The detection logic is fundamentally different (doc reads vs SKILL.md loads),
and coupling the two skills would complicate independent evolution. The shared
parts (JSONL parsing, date filtering, project detection) are copied.

### Separate always-on-analyst

CLAUDE.md/AGENTS.md require a fundamentally different evaluation method
(behavioral alignment vs. before/after impact). A separate sub-agent with
its own rubric produces cleaner, more accurate results than trying to
handle both modes in a single agent.

### 8-Step Workflow (vs. skill-auditor's 10)

Compressed for simplicity:
- Steps 1-2 (project detect + setup + collection) merged
- Steps 7-8 (report + history + apply) merged
- The workflow is sequential where needed, parallel where possible (Step 3)

### Auto-applicable vs. Manual Recommendations

Only `update_last_validated` and `add_last_validated` are auto-applicable
because they are safe, reversible operations. All other actions (remove,
archive, consolidate, move_to_code) require human judgment and are presented
as guidance in the HTML report.

## Sub-Agent Model

```
Coordinator (SKILL.md workflow)
├── collect_transcripts.py    → transcripts.json
├── collect_docs.py           → doc-manifest.json
├── [parallel] doc-impact-analyst × N batches
│   └── batch-impact-*.json   → merged → doc-impact-report.json
├── always-on-analyst × 1
│   └── always-on-report.json
├── portfolio-analyst × 1
│   └── portfolio-analysis.json
├── improvement-planner × 1
│   └── improvement-plan.json + recommendations/*.rec.json
└── generate_report.py        → docs-audit-report.html
```

### Batching Strategy

Sessions are batched ~60 per batch, capped at 12 sub-agents. Unlike
skill-auditor, docs-auditor does not need project-aware skill visibility
batching because docs are project-specific (the manifest only includes
docs from the target project).

For cross-project mode, sessions are grouped by project_dir and each
project's docs are evaluated independently.

## Workspace Structure

```
<base_dir>/                          # .claude/docs-report/ or project-local
├── health-history.json              # Append-only, shared across runs
└── <TIMESTAMP>/
    ├── transcripts.json
    ├── doc-manifest.json
    ├── batch-impact-*.json
    ├── doc-impact-report.json
    ├── always-on-report.json
    ├── portfolio-analysis.json
    ├── improvement-plan.json
    ├── recommendations/*.rec.json
    ├── docs-audit-report.html
    └── changelog.md
```

## HTML Report

Self-contained HTML with embedded JSON data. The `/*__EMBEDDED_DATA__*/`
placeholder in the template is replaced with `const REPORT_DATA = {...};`
by generate_report.py. No external dependencies to view.

Design tokens match skill-auditor for visual consistency:
- `--accent: #d97757` (orange for actions and highlights)
- `--success: #788c5d` (green for healthy/beneficial)
- `--error: #c44` (red for harmful/critical)
- Cards, badges, and tables follow the same layout patterns
