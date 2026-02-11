# Methodology

## The Documentation Effectiveness Problem

In the Coding Agent era, documentation has a measurable cost (context tokens)
and a potential benefit (improved agent behavior). Unlike code, which has
compiler errors, test failures, and linter warnings as feedback loops,
documentation lacks mechanical verification of its value.

docs-auditor creates this feedback loop through transcript-based analysis.

## Two-Layer Evaluation

### Layer 1: On-Demand Docs (docs/, adr/)

On-demand docs are read explicitly by the agent during a session. The
evaluation method is **before/after impact analysis**:

1. Identify turns where the agent reads a doc (Read/view tool calls)
2. Observe agent behavior in the 3-5 subsequent turns
3. Determine whether the doc improved, worsened, or had no effect on behavior

This yields an **impact_score** per doc: `(beneficial - harmful) / total_reads`

### Layer 2: Always-On Docs (CLAUDE.md, AGENTS.md)

Always-on docs are injected into every session's context. They are never
explicitly "read", so before/after comparison is impossible. Instead, we use
**Behavioral Alignment Analysis**:

1. Extract discrete directives from the doc
2. Check whether the agent's behavior aligns with each directive
3. Calculate relevance_rate and compliance_rate

**Limitation**: This cannot prove causation. The agent might follow a
convention even without the doc. Behavioral alignment is a best-effort proxy.

## Freshness and Staleness

Documentation decays over time as code changes. Two freshness signals:

1. **last-validated** (human-verified): When present, this is the trusted
   freshness indicator. Managed by check-doc-freshness.sh + linter hooks.
2. **git history** (universal fallback): `git log` provides last-modified
   date for any tracked file. Less reliable than last-validated because a
   doc might be modified without being validated.

The audit correlates freshness with impact: do staler docs produce more
harmful verdicts?

## Context Budget and ROI

Every doc consumes context tokens. ROI combines impact and cost:

`ROI = impact_score / (content_tokens / 1000)`

This identifies docs that consume many tokens but provide little benefit
(low ROI) versus docs that are small but highly effective (high ROI).

## Relationship to check-doc-freshness.sh

| | check-doc-freshness.sh | docs-auditor |
|---|---|---|
| **Type** | Static linter | Dynamic analyzer |
| **When** | PreToolUse hook (every commit) | On-demand (periodic) |
| **Checks** | Date thresholds, broken refs, superseded ADRs | Transcript-based impact |
| **Cost** | Milliseconds | Minutes (sub-agent analysis) |
| **Strength** | Always running, catches obvious staleness | Measures actual effectiveness |

They are complementary:
- The linter catches obvious freshness violations cheaply
- The auditor evaluates whether docs are actually useful (even if "fresh")
- Ideally, last-validated updates are informed by audit results

## LLM-as-Judge

Sub-agents evaluate doc impact using LLM judgment with structured rubrics.
This approach has inherent limitations:

- **No ground truth**: We cannot know what the agent would have done without
  the doc. We infer from behavioral signals.
- **Confidence calibration**: Each verdict includes a confidence level
  (high/medium/low) to communicate certainty.
- **Conservative defaults**: The rubric is designed to minimize false
  positives for "beneficial" and "harmful" verdicts. Most reads are
  classified as neutral/unnecessary.
