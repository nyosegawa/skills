# Audit Report Schema Reference

JSON structures used by the skill-auditor. Sub-agents and scripts MUST follow
these schemas exactly — the HTML report generator depends on field names.

---

## transcripts.json

Output of `collect_transcripts.py`.

```json
{
  "project_path": "string",
  "collected_at": "string — ISO 8601",
  "config": {
    "days": "number",
    "min_turns": "number"
  },
  "sessions": [
    {
      "session_id": "string — UUID from filename",
      "filepath": "string",
      "skills_loaded": ["string — SKILL.md paths"],
      "first_timestamp": "string | null",
      "last_timestamp": "string | null",
      "message_count": "number",
      "user_turn_count": "number",
      "turn_skill_map": [
        {
          "turn_index": "number — 0-based",
          "user_message": "string — full user message",
          "skills_loaded_after": ["string — SKILL.md paths"],
          "is_builtin_command": "boolean — true if /help, /usage, etc.",
          "project_dir": "string | null — encoded project dir name from filepath"
        }
      ]
    }
  ],
  "summary": {
    "total_sessions": "number",
    "total_user_turns": "number",
    "unique_skills_loaded": ["string"],
    "skills_never_loaded": ["string"],
    "parse_errors": "number"
  }
}
```

---

## skill-manifest.json

Output of `collect_skills.py`. Includes attention budget data.

```json
{
  "collected_at": "string — ISO 8601",
  "skill_dirs_scanned": ["string"],
  "skills": [
    {
      "filepath": "string",
      "filepath_resolved": "string | null — realpath if symlink, null otherwise",
      "name": "string",
      "scope": "global | project-local",
      "project_path": "string | null — project root if project-local",
      "description": "string — routing-critical",
      "description_raw": "string",
      "description_tokens": "number — token count for attention budget",
      "disable_model_invocation": "boolean — true if skill is explicit-only",
      "trigger": "string | null",
      "body_preview": "string — first ~500 chars of body",
      "full_content_length": "number",
      "category": "public | private | example | user | other"
    }
  ],
  "summary": {
    "total_skills": "number",
    "by_category": {"public": "number", ...},
    "skills_without_description": ["string"]
  },
  "attention_budget": {
    "total_description_tokens": "number",
    "mean_tokens_per_skill": "number",
    "median_tokens_per_skill": "number",
    "max_tokens": "number",
    "min_tokens": "number",
    "skills_above_2x_median": ["string — names"]
  },
  "description_overlaps": [
    {
      "skill_a": "string",
      "skill_b": "string",
      "shared_keywords": ["string"],
      "shared_count": "number"
    }
  ]
}
```

---

## audit-report.json

Output of routing-analyst sub-agent(s). Per-skill routing health report.

```json
{
  "skill_reports": [
    {
      "skill_name": "string",
      "skill_path": "string",
      "description_excerpt": "string — first 100 chars",
      "stats": {
        "total_fires": "number",
        "correct_fires": "number",
        "false_positives": "number",
        "false_negatives": "number",
        "accuracy": "number — 0.0 to 1.0"
      },
      "incidents": [
        {
          "session_id": "string",
          "turn_index": "number",
          "user_message": "string",
          "verdict": "correct | false_negative | false_positive | confused | explicit_invocation",
          "detail": "string",
          "root_cause": {
            "type": "weak_description | overly_broad | semantic_overlap | missing_triggers | null",
            "trigger_words": ["string"],
            "missing_exclusion": "string | null",
            "competing_skill": "string | null"
          },
          "confidence": "high | medium | low"
        }
      ],
      "health_assessment": "string",
      "suggested_fix": "string | null"
    }
  ],
  "skills_never_fired": [
    {
      "skill_name": "string",
      "skill_path": "string",
      "reason": "string"
    }
  ],
  "competition_pairs": [
    {
      "skill_a": "string",
      "skill_b": "string",
      "overlap_description": "string",
      "incidents": "number",
      "boundary_suggestion": "string"
    }
  ],
  "coverage_gaps": [
    {
      "unmet_intent": "string",
      "frequency": "number",
      "related_sessions": ["string"],
      "suggestion": "string"
    }
  ],
  "meta": {
    "sessions_analyzed": "number",
    "turns_analyzed": "number",
    "turns_with_skill_activity": "number",
    "turns_no_skill_needed": "number",
    "skills_in_scope": "number",
    "analyzed_at": "string — ISO 8601"
  }
}
```

---

## portfolio-analysis.json

Output of portfolio-analyst sub-agent.

```json
{
  "attention_budget": {
    "total_tokens": "number",
    "mean_tokens": "number",
    "median_tokens": "number",
    "per_skill": [
      {
        "skill_name": "string",
        "description_tokens": "number",
        "budget_share_pct": "number",
        "fires_in_audit": "number",
        "tokens_per_fire": "number — tokens / fires, Infinity if 0 fires",
        "efficiency_rating": "efficient | acceptable | bloated | unused",
        "trim_suggestion": "string | null"
      }
    ],
    "trim_candidates": ["string — skill names"]
  },
  "competition_matrix": [
    {
      "skill_a": "string",
      "skill_b": "string",
      "relationship": "orthogonal | adjacent | overlapping | nested",
      "evidence": "string",
      "boundary": "string",
      "coordinated_fix_needed": "boolean"
    }
  ],
  "portfolio_health": {
    "overall_score": "healthy | needs_attention | critical",
    "routing_accuracy_avg": "number",
    "token_efficiency": "efficient | acceptable | bloated",
    "competition_conflicts": "number",
    "coverage_gaps": "number",
    "summary": "string — 2-3 sentences"
  }
}
```

---

## improvement-proposals.json

Output of improvement-planner sub-agent.

```json
{
  "patches": [
    {
      "skill_name": "string",
      "skill_path": "string",
      "priority": "high | medium | low",
      "fixes_issues": ["string"],
      "current_description": "string",
      "proposed_description": "string",
      "changes_made": ["string"],
      "cascade_risk": "string",
      "expected_impact": "string",
      "token_delta": "number — positive = added tokens",
      "coordinated_with": "string | null"
    }
  ],
  "no_change_needed": [
    {
      "skill_name": "string",
      "reason": "string"
    }
  ],
  "new_skill_suggestions": [
    {
      "suggested_name": "string",
      "rationale": "string",
      "suggested_description": "string",
      "suggested_body_outline": "string",
      "coverage_gap_incidents": "number",
      "related_sessions": ["string"],
      "overlap_risk": "string"
    }
  ],
  "optimization_summary": {
    "skills_modified": "number",
    "skills_unchanged": "number",
    "new_skills_suggested": "number",
    "total_token_delta": "number",
    "highest_risk_change": "string",
    "estimated_accuracy_improvement": "string"
  }
}
```

---

## Patch Files (patches/*.patch.json)

Each file defines a proposed change to one skill's description.

```json
{
  "skill_name": "string",
  "skill_path": "string",
  "priority": "high | medium | low",
  "fixes_issues": ["string"],
  "current_description": "string",
  "proposed_description": "string",
  "changes_made": ["string"],
  "cascade_risk": "string",
  "expected_impact": "string",
  "token_delta": "number",
  "coordinated_with": "string | null"
}
```

---

## health-history.json

Append-only array of audit snapshots. One entry per run.

```json
[
  {
    "timestamp": "string — ISO 8601",
    "sessions_analyzed": "number",
    "turns_analyzed": "number",
    "portfolio_health": "healthy | needs_attention | critical",
    "routing_accuracy_avg": "number",
    "total_description_tokens": "number",
    "competition_conflicts": "number",
    "coverage_gaps": "number",
    "skills_audited": "number",
    "patches_proposed": "number"
  }
]
```
