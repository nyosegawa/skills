# Architecture Reference

Design decisions and execution architecture of the Skill Auditor.

---

## Execution Architecture: Sub-Agent Model

The analysis uses Claude sub-agents spawned via the Agent tool.

### Why Sub-Agents

| Approach | Pros | Cons |
|----------|------|------|
| Inline (coordinator does analysis) | Simple | Context compaction destroys data mid-analysis |
| External API (Gemini etc.) | Large context | Requires API key, additional cost, vendor dependency |
| **Sub-agent** (chosen) | No external deps, Claude analyzes own behavior | Need careful batching |

Sub-agents are the right fit because:
- **No external dependency**: No API keys, no additional cost beyond Claude Code usage
- **Self-analysis advantage**: Claude analyzing its own skill routing behavior has
  natural domain understanding
- **Progressive disclosure**: Each sub-agent reads only its batch of data, keeping
  context focused
- **Parallelism**: Multiple routing-analyst sub-agents can run simultaneously on
  different batches

### Batching Strategy

When transcripts exceed what a single sub-agent can analyze effectively:

1. Sort sessions by timestamp
2. Split into batches (~30 sessions per batch as a guideline)
3. Each routing-analyst sub-agent gets: full skill manifest + one batch
4. Coordinator merges results: union of incidents, recalculate per-skill stats

The coordinator manages batching, not the sub-agents. Sub-agents receive their
data and produce their analysis.

---

## Orchestration Flow

```
SKILL.md (Coordinator)
  |
  |-- Step 1-3: Data collection (scripts)
  |     collect_transcripts.py -> transcripts.json
  |     collect_skills.py -> skill-manifest.json
  |
  |-- Step 4: Routing Audit (sub-agents, parallel)
  |     Agent(routing-analyst) x N batches -> batch-audit-N.json
  |     Coordinator merges -> audit-report.json
  |
  |-- Step 5: Portfolio Analysis (sub-agent)
  |     Agent(portfolio-analyst) -> portfolio-analysis.json
  |
  |-- Step 6: Improvement Plan (sub-agent)
  |     Agent(improvement-planner) -> improvement-proposals.json
  |
  |-- Step 7: HTML Report (script)
  |     generate_report.py -> skill-audit-report.html
  |     open in browser
  |
  |-- Step 8: Apply Patches (script, with user approval)
  |     apply_patches.py -> changelog.md
```

### Sub-Agent Prompt Delivery

Each sub-agent is spawned with:
1. A task description referencing the agent prompt file (e.g., agents/routing-analyst.md)
2. Instructions to read that file for detailed rubric
3. Paths to input data files
4. Path for output JSON file

The coordinator instructs the sub-agent to:
```
Read agents/routing-analyst.md for your analysis rubric.
Read <workspace>/skill-manifest.json for skill definitions.
Read <workspace>/transcripts-batch-N.json for session data.
Write your analysis to <workspace>/batch-audit-N.json.
```

---

## Workspace Structure

```
<project>/.claude/skill-report/
├── transcripts.json              # All parsed sessions
├── transcripts-batch-*.json      # Per-batch session files (if batched)
├── skill-manifest.json           # Skill definitions + attention budget
├── batch-audit-*.json            # Per-batch routing audit results
├── audit-report.json             # Merged routing audit
├── portfolio-analysis.json       # Attention budget + competition matrix
├── improvement-proposals.json    # Patches + new skill suggestions
├── patches/                      # Per-skill patch files
│   ├── skill-name.patch.json
│   └── ...
├── skill-audit-report.html       # Interactive HTML report
├── health-history.json           # Append-only audit history
└── changelog.md                  # Applied changes log
```

---

## HTML Report

The report is a self-contained HTML file with all data embedded inline
(no external dependencies). Pattern follows skill-creator's eval-viewer:

1. `generate_report.py` reads all analysis JSON files
2. Embeds data into `assets/report_template.html` via placeholder replacement
3. Report sections:
   - Executive Summary (portfolio health score, key metrics)
   - Per-Skill Health Cards (accuracy, incidents, suggested fixes)
   - Competition Matrix (pair relationships, boundary suggestions)
   - Attention Budget (token distribution, trim candidates)
   - Improvement Patches (diff view, cascade risk)
   - Coverage Gaps (unmet intents, new skill proposals)
4. Opened in browser via `open` command

---

## Health History

`health-history.json` is an append-only array of audit snapshots. Each run
appends one entry. This enables run-over-run comparison:

```json
[
  {
    "timestamp": "2026-03-04T...",
    "sessions_analyzed": 36,
    "turns_analyzed": 316,
    "portfolio_health": "needs_attention",
    "routing_accuracy_avg": 0.82,
    "total_description_tokens": 3400,
    "competition_conflicts": 3,
    "coverage_gaps": 2,
    "skills_audited": 17
  }
]
```

The coordinator appends the current run's summary and reports the delta
from the previous run (if any).
