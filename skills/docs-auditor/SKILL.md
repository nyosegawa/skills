---
name: docs-auditor
description: >
  セッションtranscriptを分析してドキュメントの効果を評価する。
  doc参照がAgentの行動を改善したか、Context浪費か、腐敗して有害かを判定。
  last-validated がないドキュメントにもgit履歴ベースで対応。
  HTML reportでper-doc健全性、Context budget、freshness、推奨アクションを表示。
  Use when user says "audit docs", "docs audit", "run docs-auditor",
  "ドキュメント監査", "doc ROI", "ドキュメントの効果分析".
disable-model-invocation: true
---

# Docs Auditor

Transcript-based documentation effectiveness analysis. Evaluates whether
reading docs actually improves agent behavior or wastes context tokens.
Generates an interactive HTML report with per-doc health, freshness dashboard,
context budget, and actionable recommendations.

## Prerequisites

- `pip install tiktoken` (optional — falls back to character-based estimation)
- No external API keys required. Analysis uses Claude sub-agents.

## Workflow

Run all steps sequentially. The coordinator (you) manages data flow between
scripts and sub-agents.

### Step 1: Initial Questions

Ask the user for the report language using AskUserQuestion:
"レポートの言語は？ (e.g. 日本語, English)"
Default to the user's conversation language if not specified.
Pass the language choice to all sub-agents as an instruction prefix:
"Write all output text in [chosen language]."

Scope is always current project only. Do NOT ask.

### Step 2: Workspace Setup & Data Collection

Set up a timestamped workspace:

```bash
RUN_ID=$(date +%Y-%m-%dT%H-%M-%S)
WORKSPACE=<project>/.claude/docs-report/${RUN_ID}
mkdir -p ${WORKSPACE}
```

Collect transcripts:

```bash
python3 scripts/collect_transcripts.py --cwd "$(pwd)" --days 14 \
  --output ${WORKSPACE}/transcripts.json --verbose
```

Collect doc metadata:

```bash
python3 scripts/collect_docs.py --project-root "$(pwd)" \
  --output ${WORKSPACE}/doc-manifest.json --verbose
```

Report: "N sessions, M user turns, K docs found. Context budget: T tokens
(A always-on, D on-demand)."

### Step 3: Doc Impact Audit (Sub-agents, Batched)

Batch sessions (~60 per batch, cap at MAX_BATCHES=12). Spawn parallel
sub-agents — one per batch:

```
For each batch i:
  Agent tool (general-purpose):
    "Read agents/doc-impact-analyst.md from the docs-auditor skill directory
     for your analysis instructions.
     Read ${WORKSPACE}/doc-manifest.json for doc definitions.
     Read ${WORKSPACE}/transcripts.json for session data.
     Only analyze sessions with these indices: [list from batch].
     Write all output text in [chosen language].
     Write your analysis as JSON to ${WORKSPACE}/batch-impact-${i}.json
     following the exact schema in schemas/schemas.md (doc-impact-report section)."
```

After all sub-agents complete, merge batch results:
- Union all `doc_reports` (combine incidents, recalculate stats per doc)
- Union `docs_never_read`
- Recalculate `meta` totals
- Write merged result to `${WORKSPACE}/doc-impact-report.json`

### Step 4: Always-On Analysis (Single Sub-agent)

```
Agent tool (general-purpose):
  "Read agents/always-on-analyst.md from the docs-auditor skill directory.
   Read ${WORKSPACE}/doc-manifest.json for doc definitions.
   Read ${WORKSPACE}/transcripts.json for session data.
   Focus on docs with injection_mode 'always' (CLAUDE.md, AGENTS.md).
   Write all output text in [chosen language].
   Write analysis to ${WORKSPACE}/always-on-report.json."
```

### Step 5: Portfolio Analysis (Single Sub-agent)

```
Agent tool (general-purpose):
  "Read agents/portfolio-analyst.md from the docs-auditor skill directory.
   Read ${WORKSPACE}/doc-manifest.json
   Read ${WORKSPACE}/doc-impact-report.json
   Read ${WORKSPACE}/always-on-report.json
   Write all output text in [chosen language].
   Write analysis to ${WORKSPACE}/portfolio-analysis.json."
```

### Step 6: Improvement Plan (Single Sub-agent)

```
Agent tool (general-purpose):
  "Read agents/improvement-planner.md from the docs-auditor skill directory.
   Read ${WORKSPACE}/doc-impact-report.json
   Read ${WORKSPACE}/always-on-report.json
   Read ${WORKSPACE}/portfolio-analysis.json
   Read ${WORKSPACE}/doc-manifest.json
   Write all output text in [chosen language].
   Write recommendations to ${WORKSPACE}/improvement-plan.json.
   Write individual recommendation files to ${WORKSPACE}/recommendations/."
```

### Step 7: Generate Report & Apply

Generate HTML report:

```bash
python3 scripts/generate_report.py --workspace ${WORKSPACE}
open ${WORKSPACE}/docs-audit-report.html
```

Update health history — read `<base_dir>/health-history.json` (create if
doesn't exist as `[]`). Append:

```json
{
  "timestamp": "<ISO 8601>",
  "sessions_analyzed": 0,
  "turns_analyzed": 0,
  "docs_analyzed": 0,
  "total_doc_tokens": 0,
  "always_on_tokens": 0,
  "portfolio_health": "healthy | needs_attention | critical",
  "freshness_score": "fresh | aging | stale",
  "mean_impact_score": 0.0,
  "docs_never_read": 0,
  "recommendations_proposed": 0
}
```

Show delta from previous run if exists.

Do NOT auto-apply any recommendations. All recommendations (including
update_last_validated and add_last_validated) are presented in the HTML
report for human review. The user decides what to apply manually.

If the user explicitly asks to apply specific recommendations after
reviewing the report:

```bash
python3 scripts/apply_recommendations.py \
  --recommendations ${WORKSPACE}/recommendations/ --confirm \
  --output ${WORKSPACE}/changelog.md
```

### Step 8: Summary

Report what was done:
- Sessions and turns analyzed
- Docs analyzed and their context budget
- Portfolio health score and freshness score
- Always-on utilization score
- Recommendations proposed (by action type)
- Link to the HTML report

## Doc Impact Verdicts

| Verdict | Description |
|---------|-------------|
| beneficial | Agent behavior improved after reading the doc |
| neutral | No observable behavior change |
| harmful | Outdated/conflicting info caused agent to act incorrectly |
| unnecessary | Doc was irrelevant to the task (context waste) |
| inconclusive | Cannot determine impact from available context |

## Always-On Directive Verdicts

| Verdict | Description |
|---------|-------------|
| followed | Agent behavior aligned with directive |
| violated | Agent behavior contradicted directive |
| not_applicable | Directive was not relevant to this session |

## Workspace Structure

```
<base_dir>/
├── health-history.json
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

## Troubleshooting

- **"No project found"**: Use `--cwd` or `--list` with collect_transcripts.py.
- **tiktoken not installed**: Token counts use character-based approximation.
- **Large project (100+ sessions)**: Batched automatically, max 12 sub-agents.
- **No docs found**: Ensure project has docs/, CLAUDE.md, or AGENTS.md.
