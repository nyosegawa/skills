# Docs Auditor JSON Schemas

Reference schemas for all intermediate JSON files produced during the audit.

## doc-manifest.json

Produced by `collect_docs.py`.

```json
{
  "project_root": "string — absolute path",
  "collected_at": "ISO 8601",
  "docs": [
    {
      "filepath": "string — relative to project root",
      "filepath_abs": "string — absolute path",
      "doc_type": "claude_md | agents_md | general_doc | adr | readme",
      "injection_mode": "always | on_demand",
      "content_tokens": "number",
      "line_count": "number",
      "heading_count": "number",
      "last_validated": "YYYY-MM-DD | null",
      "last_validated_age_days": "number | null",
      "phase": "current | target | null",
      "status": "string | null — ADR status (Accepted, Superseded, etc.)",
      "superseded_by": "ADR-NNN | null",
      "git_last_modified": "ISO 8601 | null",
      "git_last_modified_age_days": "number | null",
      "git_last_author": "string | null",
      "git_commit_count": "number",
      "freshness_source": "last_validated | git",
      "freshness_status": "superseded | null",
      "first_heading": "string | null",
      "body_preview": "string — first ~300 chars"
    }
  ],
  "context_budget": {
    "total_doc_tokens": "number",
    "always_on_tokens": "number",
    "on_demand_tokens": "number",
    "doc_count": "number",
    "mean_tokens_per_doc": "number",
    "median_tokens_per_doc": "number",
    "docs_above_2x_median": ["filepath"]
  }
}
```

## transcripts.json

Produced by `collect_transcripts.py`.

```json
{
  "project_path": "string",
  "collected_at": "ISO 8601",
  "config": { "days": 14, "min_turns": 1 },
  "sessions": [
    {
      "session_id": "UUID",
      "filepath": "string — path to .jsonl",
      "docs_read": [
        { "filepath": "string", "doc_type": "string" }
      ],
      "first_timestamp": "string | null",
      "last_timestamp": "string | null",
      "message_count": "number",
      "user_turn_count": "number",
      "turn_doc_map": [
        {
          "turn_index": "number",
          "user_message": "string",
          "docs_read_after": [
            { "filepath": "string", "doc_type": "string" }
          ],
          "is_builtin_command": "boolean"
        }
      ],
      "project_dir": "string | null — encoded project dir"
    }
  ],
  "summary": {
    "total_sessions": "number",
    "total_user_turns": "number",
    "unique_docs_read": ["filepath"],
    "parse_errors": "number",
    "sessions_by_project": { "project_dir": "number" }
  }
}
```

## doc-impact-report.json

Produced by doc-impact-analyst sub-agents (merged by coordinator).

```json
{
  "doc_reports": [
    {
      "filepath": "string",
      "doc_type": "string",
      "stats": {
        "total_reads": "number",
        "beneficial": "number",
        "neutral": "number",
        "harmful": "number",
        "unnecessary": "number",
        "inconclusive": "number",
        "impact_score": "number — (beneficial - harmful) / total_reads"
      },
      "incidents": [
        {
          "session_id": "string",
          "turn_index": "number",
          "user_message": "string",
          "verdict": "beneficial | neutral | harmful | unnecessary | inconclusive",
          "detail": "string",
          "evidence": "string",
          "confidence": "high | medium | low"
        }
      ],
      "health_assessment": "string",
      "suggested_action": "string | null"
    }
  ],
  "docs_never_read": [
    {
      "filepath": "string",
      "doc_type": "string",
      "content_tokens": "number",
      "reason": "string"
    }
  ],
  "meta": {
    "sessions_analyzed": "number",
    "turns_analyzed": "number",
    "turns_with_doc_reads": "number",
    "total_doc_reads": "number",
    "docs_in_scope": "number"
  }
}
```

## always-on-report.json

Produced by always-on-analyst sub-agent.

```json
{
  "always_on_reports": [
    {
      "filepath": "string",
      "content_tokens": "number",
      "directives": [
        {
          "directive_text": "string",
          "category": "prohibition | convention | command | read_order | context_info",
          "sessions_relevant": "number",
          "sessions_followed": "number",
          "sessions_violated": "number",
          "relevance_rate": "number — 0.0-1.0",
          "compliance_rate": "number — 0.0-1.0",
          "violations": [
            {
              "session_id": "string",
              "detail": "string",
              "severity": "high | medium | low"
            }
          ]
        }
      ],
      "overall_utilization": "number — 0.0-1.0",
      "dead_weight_tokens": "number",
      "health_assessment": "string"
    }
  ],
  "meta": {
    "sessions_analyzed": "number",
    "unique_directives_found": "number",
    "directives_never_relevant": "number",
    "directives_by_category": {
      "prohibition": "number",
      "convention": "number",
      "command": "number",
      "read_order": "number",
      "context_info": "number"
    }
  }
}
```

## portfolio-analysis.json

Produced by portfolio-analyst sub-agent.

```json
{
  "context_budget": {
    "total_tokens": "number",
    "always_on_tokens": "number",
    "on_demand_tokens": "number",
    "per_doc": [
      {
        "filepath": "string",
        "doc_type": "string",
        "content_tokens": "number",
        "read_count": "number",
        "impact_score": "number | null",
        "roi": "number | null",
        "efficiency_rating": "high_roi | acceptable | low_roi | dead_weight",
        "suggestion": "string | null"
      }
    ]
  },
  "freshness_analysis": {
    "docs_with_last_validated": "number",
    "docs_without_last_validated": "number",
    "freshness_distribution": {
      "fresh": "number",
      "aging": "number",
      "stale": "number",
      "very_stale": "number",
      "superseded": "number"
    },
    "staleness_harm_correlation": "string",
    "high_risk_stale_docs": [
      {
        "filepath": "string",
        "age_days": "number",
        "read_count": "number",
        "harmful_count": "number",
        "risk_description": "string"
      }
    ]
  },
  "overlap_candidates": [
    {
      "doc_a": "string",
      "doc_b": "string",
      "shared_topics": ["string"],
      "consolidation_benefit": "string"
    }
  ],
  "portfolio_health": {
    "overall_score": "healthy | needs_attention | critical",
    "context_efficiency": "efficient | acceptable | bloated",
    "freshness_score": "fresh | aging | stale",
    "always_on_utilization": "number — 0.0-1.0",
    "summary": "string"
  }
}
```

## improvement-plan.json

Produced by improvement-planner sub-agent.

```json
{
  "recommendations": [
    {
      "filepath": "string",
      "doc_type": "string",
      "action": "update_last_validated | add_last_validated | update_content | archive | remove | move_to_code | consolidate | strengthen_enforcement",
      "priority": "high | medium | low",
      "rationale": "string",
      "evidence": {
        "impact_score": "number | null",
        "read_count": "number",
        "harmful_incidents": "number",
        "freshness_age_days": "number | null",
        "violations": "number"
      },
      "implementation_hint": "string",
      "context_token_delta": "number",
      "risk": "string"
    }
  ],
  "no_change_needed": [
    {
      "filepath": "string",
      "reason": "string"
    }
  ],
  "summary": {
    "total_docs": "number",
    "docs_with_actions": "number",
    "docs_no_change": "number",
    "total_context_token_delta": "number",
    "actions_by_type": {},
    "actions_by_priority": {}
  }
}
```

## recommendations/*.rec.json

Individual auto-applicable recommendation files.

```json
{
  "filepath": "string — path to the doc file",
  "action": "update_last_validated | add_last_validated",
  "new_date": "YYYY-MM-DD",
  "rationale": "string"
}
```

## health-history.json

Append-only array at `<base_dir>/health-history.json`.

```json
[
  {
    "timestamp": "ISO 8601",
    "sessions_analyzed": "number",
    "turns_analyzed": "number",
    "docs_analyzed": "number",
    "total_doc_tokens": "number",
    "always_on_tokens": "number",
    "portfolio_health": "healthy | needs_attention | critical",
    "freshness_score": "fresh | aging | stale",
    "mean_impact_score": "number",
    "docs_never_read": "number",
    "recommendations_proposed": "number"
  }
]
```
