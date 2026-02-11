# Official Remotion Skill Integration

This skill is a workflow layer. Official Remotion rules remain the source of truth for API usage and constraints.

## Load Sequence

1. Read `skills/skills/remotion/SKILL.md`
2. Read only the rule files needed for the current stage
3. Read this skill's references
4. Implement, then validate

## Stage-to-Rule Mapping

### Composition Stage
- `rules/compositions.md`
- `rules/parameters.md`
- `rules/calculate-metadata.md`

### Motion Stage
- `rules/animations.md`
- `rules/timing.md`
- `rules/sequencing.md`
- `rules/transitions.md`

### Assets Stage
- `rules/assets.md`
- `rules/images.md`
- `rules/fonts.md`
- `rules/measuring-text.md` (when text containers are dynamic)

### Optional Media Stage
- `rules/audio.md`
- `rules/videos.md`
- `rules/subtitles.md`
- `rules/text-animations.md`

## Priority Rules

1. If guidance conflicts, follow official Remotion rules.
2. Use this skill for production workflow and quality patterns.
3. In final reports, list the official Remotion rules used.

## Report Snippet Example

```text
Official rules used:
- compositions.md
- transitions.md
- images.md
```
