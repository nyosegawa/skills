# Methodology Reference

Background, theory, and design decisions behind the Skill Auditor.

---

## The Skill Routing Problem

Claude Code's skill system works by matching user messages against skill
descriptions. This is effectively an **information retrieval** problem:

- **Query**: The user's message
- **Documents**: The skill descriptions
- **Relevance judgment**: Which skill best serves the user's intent

Unlike traditional IR, there's no click-through data, no relevance labels,
and no explicit feedback. The system is flying blind.

### Why This Matters

When a wrong skill is loaded:
- The user gets suboptimal output (wrong template, wrong approach)
- Downstream optimization is wasted — you're optimizing the wrong skill
- The user may not even realize a better skill existed

Skill routing accuracy is the **upstream gate** for all other quality measures.

---

## Attention Competition

Skills don't exist in isolation. They compete for the router's attention.

### The Whack-a-Mole Problem

Improving Skill A's description (adding keywords, broadening scope) can
degrade Skill B's routing accuracy if:
- The new keywords overlap with Skill B's domain
- The broader scope now covers cases that should go to Skill B
- Skill A's description becomes "louder" relative to Skill B

This is why **set-level optimization** is essential. Individual skill
optimization (as done by skill-creator) misses this systemic interaction.

### Competition Structure

For any pair of skills (A, B), their routing relationship is one of:

1. **Orthogonal**: Completely different domains. No competition.
2. **Adjacent**: Related but distinct. Occasional boundary confusion.
3. **Overlapping**: Significant shared territory. Frequent confusion.
4. **Nested**: One skill's scope is a subset of another's.

The audit's competition matrix maps these relationships empirically using
real session transcript evidence.

---

## Detection Method

### How Skills Are Detected in Transcripts

When Claude Code loads a skill, it reads the skill's SKILL.md file. This
appears in the transcript as a Read/view tool call:

```json
{"type": "tool_use", "name": "Read", "input": {"file_path": "...SKILL.md"}}
```

This is a reliable signal because it happens for every skill load and the
path uniquely identifies the skill.

### Limitations

- **System-level skill injection**: Some skills may be loaded by the system
  prompt without a tool call. These are invisible to transcript analysis.
- **Partial reads**: If Claude reads only part of a SKILL.md, detection is
  less reliable.
- **Compacted sessions**: In long sessions, earlier skill loads may be
  summarized away by context compaction.

---

## LLM-as-Judge for Routing Correctness

There is no ground truth for "correct routing." The user didn't label their
intent. We use the LLM itself as a judge, consistent with:

- **Anthropic's guidance**: "Demystifying evals for AI agents" recommends
  model-based graders with rubrics for evaluating agent behavior.
- **Sub-agent approach**: Each analysis sub-agent receives the full data for
  its batch and applies the rubric from agents/routing-analyst.md.

### Calibration

LLM judges can be inconsistent. We mitigate this by:

1. **Structured rubric**: Clear categories and decision criteria
2. **Confidence scores**: Each judgment includes a confidence level
3. **Pattern prioritization**: Single-incident findings are noise; 3+
   incident patterns are signals
4. **Conservative false-negative threshold**: Requests that don't need any
   skill are NOT counted as false negatives

---

## Relationship to skill-creator

| Aspect | skill-creator | skill-auditor |
|--------|--------------|---------------|
| Timing | Pre-deployment | Post-deployment |
| Scope | Individual skill | Full portfolio |
| Data | Synthetic test queries | Real session transcripts |
| Optimization | Single description in isolation | Set-level with cascade checking |
| Key problem | "Is this skill good?" | "Are skills working well together?" |

skill-creator's biggest limitation: it optimizes descriptions by testing with
`claude -p` and only the target skill installed. This misses attention
competition. skill-auditor fills exactly this gap by analyzing the full skill
set as a system.

---

## Optimization Strategy

### Description Editing Principles

1. **Add trigger phrases from user vocabulary**: Look at actual user messages
   that were misrouted. Add the exact words users used.

2. **Add exclusion clauses**: "Do NOT use for X" is more precise than removing
   shared keywords. It preserves breadth while clarifying boundaries.

3. **Front-load distinguishing features**: Put the most differentiating
   keywords early in the description.

4. **Use concrete format markers**: ".docx files" is stronger than "document
   creation." Format-specific markers are less ambiguous.

### Cascade Checking

Before applying any patch:

1. Extract the proposed new keywords
2. Check: Do they appear in any other skill's description?
3. If yes: Will the change cause this skill to "win" in cases where the
   other should win?
4. If uncertain: Propose both patches together
