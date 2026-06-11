# Agent Skill Best Practices for Claude and Codex

Last verified: 2026-05-18

This document is the default reference for creating or improving Agent Skills for Claude, Claude Code, Codex CLI, Codex IDE, and the Codex app. Before writing a new `SKILL.md`, read this document first and treat it as the shared design baseline.

## Source Material

- OpenAI Codex Agent Skills: https://developers.openai.com/codex/skills
- OpenAI Codex best practices: https://developers.openai.com/codex/learn/best-practices
- OpenAI Codex "Save workflows as skills": https://developers.openai.com/codex/use-cases/reusable-codex-skills
- Anthropic Skill authoring best practices: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Claude custom skills guide: https://claude.com/docs/skills/how-to
- Anthropic engineering article on Agent Skills: https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Official skill-creator: https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md
- Sakasegawa analysis: https://nyosegawa.com/posts/skill-creator-and-orchestration-skill/

## Core Model

An Agent Skill is a portable folder that teaches an agent a repeatable workflow, not a dumping ground for general project rules.

Use a skill when the knowledge is:

- repeatable across conversations,
- task-specific rather than globally applicable,
- too procedural or domain-specific to rely on model memory,
- useful enough that future agents should not rediscover it,
- easier to validate as a workflow than as a one-off prompt.

Do not create a skill for broad preferences that belong in `AGENTS.md`, `CLAUDE.md`, config, or repo docs.

## Cross-Platform Baseline

Use the open Agent Skills shape unless a target platform requires otherwise:

```text
skill-name/
├── SKILL.md
├── scripts/       # optional deterministic tools
├── references/    # optional docs loaded only when needed
├── assets/        # optional templates and output resources
└── agents/        # optional specialist prompts for orchestration skills
```

`SKILL.md` must begin with YAML frontmatter:

```yaml
---
name: skill-name
description: Clear what/when trigger text.
---
```

For maximum Claude/Codex portability:

- Use lowercase kebab-case for `name`, matching the directory name.
- Keep `description` short, specific, and trigger-oriented.
- Keep `SKILL.md` under 500 lines unless there is a strong reason.
- Put detailed knowledge into `references/`, not the body.
- Use forward slashes in paths.
- Reference files from `SKILL.md` with clear "when to read this" guidance.
- Avoid extra root files like `README.md`, `CHANGELOG.md`, or setup notes unless a platform explicitly requires them.

Claude.ai currently has stricter description limits than the open spec, while Codex may shorten or omit descriptions when many skills are installed. Front-load the most important trigger words.

## Progressive Disclosure

Design every skill around three loading levels:

1. `name` and `description`: always visible to the model.
2. `SKILL.md` body: loaded only after the skill triggers.
3. `scripts/`, `references/`, `assets/`, `agents/`: used only when the body points to them.

The main failure mode is writing a giant `SKILL.md` that crowds out the task. Keep the body as the routing and workflow layer. Put schemas, API docs, examples, rubrics, long style guides, and domain notes in separate files.

Good `SKILL.md` responsibilities:

- decide which workflow path applies,
- name the exact files or scripts to use,
- state critical constraints,
- define completion and validation,
- tell the agent how to recover from common failures.

Poor `SKILL.md` responsibilities:

- full API manuals,
- dozens of examples when three would do,
- long historical background,
- generic advice the model already knows,
- implementation code that belongs in `scripts/`.

## Description Design

The `description` is the skill's trigger surface. The body cannot help if the description fails.

Write descriptions as:

```text
[What the skill does]. Use when the user asks to [trigger contexts], including [nearby phrasing], [file/task types], or [workflow situations]. Do not use for [important boundary] if ambiguity is likely.
```

Rules:

- Include both "what it does" and "when to use it".
- Put all trigger information in `description`, not in a "When to use" section inside the body.
- Be a little assertive for true positives. Skills often under-trigger.
- Add boundaries for adjacent skills so it does not steal attention from better matches.
- Include Japanese and English trigger phrases when the user may ask in both languages.
- Avoid vague descriptions like "helps with docs" or "handles data".
- Avoid descriptions so broad that they become global policy.

Test descriptions with:

- 8-10 realistic should-trigger prompts,
- 8-10 realistic should-not-trigger near misses,
- casual phrasing, typos, file paths, and ambiguous adjacent tasks,
- cases where this skill competes with another skill and should either win or lose.

## Degrees of Freedom

Choose how much freedom the agent should have based on task fragility.

- High freedom: text instructions. Use when judgment matters and several good approaches exist.
- Medium freedom: pseudocode, templates, structured plans. Use when a stable pattern exists but context affects details.
- Low freedom: scripts and strict schemas. Use when correctness depends on exact calculations, file formats, field names, packaging, or validation.

Prefer explaining why a rule exists. Use hard MUST-style constraints only near real cliffs: security, irreversible writes, schema field names, packaging structure, release policy, or data loss risk.

## Scripts

Put deterministic or repeatedly rewritten work into `scripts/`.

Good script candidates:

- validation,
- aggregation and statistics,
- packaging,
- file conversion,
- schema checks,
- parsing,
- mechanical batch operations,
- browser/report generation.

Bad script candidates:

- open-ended judgment,
- reasoning-heavy diagnosis,
- prose synthesis,
- anything that mainly punts the hard work back to the model.

Every script should:

- have one clear job,
- accept file paths and options as arguments,
- avoid hardcoded user-specific paths unless the skill is explicitly private,
- print helpful errors,
- produce structured output when another component consumes it,
- be tested by actually running it.

In `SKILL.md`, say whether the agent should execute a script or read it as reference. Execution is usually better for utility scripts because only the output enters context.

## References and Assets

Use `references/` for knowledge the agent may need to read:

- API docs,
- schemas,
- domain rules,
- evaluation rubrics,
- examples,
- troubleshooting notes,
- platform-specific variants.

Use `assets/` for files the agent should use in outputs:

- templates,
- fonts,
- images,
- boilerplate projects,
- sample documents.

Keep reference files one level deep from `SKILL.md` where possible. For long reference files, include a table of contents near the top.

Organize references by decision point:

```text
references/
├── aws.md
├── gcp.md
└── azure.md
```

Do not force the agent to read all cloud providers to deploy to one provider.

## Schema Contracts

If a skill connects model output to scripts, viewers, downstream tools, or repeated handoff files, design the schema first.

Put schema contracts in `references/schemas.md` or a focused reference file. Include:

- exact field names,
- required vs optional fields,
- example JSON,
- known breakages from wrong names,
- validation command if available.

The official `skill-creator` demonstrates why this matters: its viewer and aggregation scripts expect exact JSON fields such as `text`, `passed`, and `evidence`. Letting the model improvise field names makes downstream tooling fail silently.

## Orchestration Skills

Complex skills should be architected like small software systems, not long prompts.

Use these components intentionally:

- `SKILL.md`: orchestration, routing, control flow.
- `agents/`: specialist prompts for grader, comparator, analyzer, reviewer, planner, etc.
- `references/`: contracts and domain knowledge.
- `scripts/`: deterministic engine.
- `assets/` or UI files: review surfaces, templates, generated viewers.

### Sub-agent Pattern

Use when multiple independent perspectives should run on the same task.

Examples:

- with-skill vs baseline runs,
- independent graders,
- blind A/B comparison,
- analyzer passes,
- parallel research facets.

This is the `skill-creator` pattern: one parent workflow delegates specialized work to subagents and aggregates results.

### Skill Chain Pattern

Use when the workflow has clear sequential phases and each phase is useful independently.

Examples:

- research -> execution -> report,
- triage -> fix -> verify -> PR summary,
- source collection -> synthesis -> QA.

Each phase may be its own skill with its own `SKILL.md`, scripts, and references. This makes nodes reusable and replaceable.

### Hybrid Pattern

Use a skill chain for the main phases, then use subagents inside a phase where parallelism helps. For example, a research skill may spawn subagents by topic, then hand structured findings to a reporting skill.

Choose based on:

- parallel vs sequential structure,
- whether components should be independently invokable,
- how much shared context workers need,
- where human feedback belongs,
- which outputs need machine validation.

## Human Review

For quality-critical work, do not rely on chat-only feedback if the output set is large.

Use an appropriate review surface:

- generated HTML viewer,
- spreadsheet,
- contact sheet,
- diff report,
- rendered document preview,
- structured `feedback.json`.

The `skill-creator` uses `eval-viewer/generate_review.py` to show qualitative outputs and benchmark results, then reads structured feedback for the next iteration. Prefer reusing that pattern over inventing ad hoc review loops.

## Evaluation Workflow

For non-trivial skills, build tests before declaring success.

Minimum loop:

1. Capture intent and examples.
2. Draft or revise the skill.
3. Create 2-3 realistic task prompts.
4. Run with-skill outputs.
5. When possible, run baseline or old-skill outputs.
6. Evaluate qualitative outputs with the user.
7. Add objective assertions only when they are meaningful.
8. Use scripts for assertions that can be checked programmatically.
9. Improve the skill based on observed failures.
10. Repeat until feedback stabilizes.

For description optimization:

- create should-trigger and should-not-trigger prompts,
- include near misses and skill competition cases,
- use train/test splits or held-out prompts when possible,
- choose descriptions by held-out performance, not only by training success.

## Platform Notes

### Claude / Claude Code

- User-wide Claude skills must live at `~/.claude/skills/<name>/`.
- Repo-local Claude skills must live at `<repo>/.claude/skills/<name>/`.
- Do not assume Claude can see `~/.agents/skills` or `<repo>/.agents/skills`; those are Codex-oriented paths unless explicitly bridged.
- Claude.ai may impose shorter description limits.
- Claude.ai may not have subagents or browser surfaces; keep the core workflow but adapt mechanics.
- Validate packaging and referenced files before handing off.

### Codex

- User-wide Codex skills can live in `~/.agents/skills`.
- Repo skills can live under `.agents/skills` in the current directory, parent directories, or repo root.
- Codex in this environment also has `~/.codex/skills` symlinked to `~/.claude/skills`, but portable Codex guidance should still prefer `.agents/skills` unless the user wants Claude visibility too.
- Codex reads skill metadata first and loads full `SKILL.md` only after selection.
- Codex may cap the initial skill list; concise descriptions matter.
- Codex supports plugins as the installable distribution unit for reusable skills and apps.
- Use `AGENTS.md` for durable repo guidance and mandatory skill triggers.

### Cross-runtime Portability

If the skill is intended for both Claude and Codex:

- Keep the core Agent Skills structure standard.
- Avoid platform-only assumptions in the main path.
- Add a "Platform differences" section only when necessary.
- Provide fallbacks when subagents, browser UI, or a specific CLI are unavailable.
- Keep environment-specific commands explicit and isolated.

## Security and Trust

Skills are executable capability bundles. Treat them as supply-chain inputs.

- Do not hardcode secrets, tokens, cookies, or private credentials.
- Do not include hidden exfiltration, remote execution, or surprising network behavior.
- Make any destructive or external side effect explicit.
- Prefer MCP connections or approved CLIs for external service access.
- Review third-party skills before enabling them.
- Keep private paths and organization-specific logic in private or secret skills, not public skills.

## Placement Guidance

Use this decision table:

| Need | Put it in |
| --- | --- |
| Personal skill for Claude | `~/.claude/skills/<name>/` |
| Personal skill for Codex | `~/.agents/skills/<name>/` |
| Personal skill for both Claude and Codex | Prefer `~/.claude/skills/<name>/` when this Codex install can see `~/.codex/skills -> ~/.claude/skills`; otherwise create or sync both `~/.claude/skills/<name>/` and `~/.agents/skills/<name>/` |
| Repo-specific Claude workflow | `<repo>/.claude/skills/<name>/` |
| Repo-specific Codex workflow | `<repo>/.agents/skills/<name>/` |
| Repo-specific workflow for both Claude and Codex | Create or sync both `<repo>/.claude/skills/<name>/` and `<repo>/.agents/skills/<name>/`, or put source in one repo path and use explicit symlinks if the environment supports them |
| Always-on repo rule | `<repo>/AGENTS.md` |
| Always-on Claude rule | `~/.claude/CLAUDE.md` or repo `CLAUDE.md` |
| General project context | `AGENTS.md`, `CLAUDE.md`, README, docs |
| Detailed skill knowledge | `references/` |
| Deterministic repeatable operation | `scripts/` |
| Output template or starter files | `assets/` |

For Codex, `AGENTS.md` should name mandatory skill triggers in short if/then form. Example:

```markdown
## Mandatory skill usage

- Use `$code-change-verification` when runtime code, tests, examples, or build behavior changes.
- Use `$openai-knowledge` for OpenAI API or platform work.
- Use `$pr-draft-summary` when substantial work is ready for review.
```

## Creation Checklist

Before writing:

- Identify the repeatable workflow.
- Gather 2-3 real prompts or examples.
- Decide if this is a skill, repo rule, command, script, or doc.
- Decide Claude-only, Codex-only, or portable.
- Check adjacent skills to avoid trigger conflicts.

While writing:

- Keep `description` trigger-focused.
- Put core workflow in `SKILL.md`.
- Move long knowledge to `references/`.
- Move deterministic work to `scripts/`.
- Add schemas before script/model handoffs.
- Explain why important rules exist.
- Keep hard constraints only where needed.

Before finishing:

- Validate frontmatter and directory name.
- Check every referenced file exists.
- Run representative scripts.
- Run realistic trigger and task tests.
- Test at least one near-miss prompt.
- Record what was not tested.

## Anti-patterns

Avoid:

- "kitchen sink" skills that do many unrelated workflows,
- generic descriptions that compete with everything,
- `SKILL.md` files that contain entire manuals,
- reference files that are never linked from `SKILL.md`,
- scripts without clear inputs, outputs, or error messages,
- strict ALWAYS/NEVER walls where an explanation would work better,
- time-sensitive facts without a freshness note,
- root clutter that makes the skill look like a repo,
- untested packaging,
- creating a skill when a short `AGENTS.md` rule would solve it.

## Recommended Default Workflow for Future Agents

When asked to create or improve an Agent Skill:

1. Read this document first.
2. Inspect any existing skill and adjacent skills.
3. Ask only for missing intent that cannot be inferred.
4. Draft the skill with progressive disclosure.
5. Add scripts, references, assets, or agents only when the workflow justifies them.
6. Run or outline meaningful tests.
7. If using the official `skill-creator`, follow its full loop: draft, eval, benchmark, viewer, feedback, improve, description optimization, package.
8. Report changed paths, validation performed, and remaining risk.
