---
name: remotion-promo-video-factory
description: Build high-quality Remotion promo and intro videos for any app type (web, mobile, API/SDK, developer tool, AI product) using app-type blueprints, timeline patterns, and frame-capture QA. Use when users ask to create a product promo, teaser, app intro, UX flow video, or Remotion-based demo video.
metadata:
  tags: remotion, promo, teaser, intro-video, app-demo, animation, timeline, qa
---

# Remotion Promo Video Factory

Use this skill to produce repeatable, high-quality app introduction videos in Remotion.
This skill is intentionally app-agnostic and works for UI-heavy products and non-UI products.

## Core Rules

1. Use official Remotion skill rules as primary authority.
2. Drive all motion via `useCurrentFrame()` with `interpolate()` and `spring()`.
3. Design time in seconds, then convert with `sec()`.
4. Pick an app-type blueprint first; do not default to UI-only demos.
5. Prefer reusable visual primitives over one-off recorded footage.
6. Apply typography sizing rules before animation polish.
7. Validate every major edit with frame captures, then run typecheck and render.
8. Do not claim quality success without frame-by-frame evidence.
9. Never commit, push, or mark tasks done without explicit user approval.

## Official Skill Interop

Always read `references/official-skill-integration.md` first.

Required official rule groups by stage:
1. Composition stage: `compositions`, `parameters`, `calculate-metadata`
2. Motion stage: `animations`, `timing`, `sequencing`, `transitions`
3. Asset stage: `assets`, `images`, `fonts`
4. Optional stage: `audio`, `videos`, `subtitles`, `text-animations`

## References

- App-type selection and scene templates: `references/app-type-blueprints.md`
- Official Remotion rule mapping: `references/official-skill-integration.md`
- Timeline and motion patterns: `references/timeline-and-motion.md`
- Timing budgets and debug loop: `references/timing-and-debug-loop.md`
- Typography and readability rules: `references/typography-and-readability.md`
- Reusable visual building blocks: `references/visual-primitives.md`
- QA checklist: `references/qa-checklist.md`
- Troubleshooting guide: `references/troubleshooting.md`

## Workflow

### Step 1: Collect Inputs

Collect from local project context (README, docs, landing page, existing UI, CLI/API examples):
1. Target audience
2. Core promise in one sentence
3. Proof assets available (UI, code, logs, metrics, testimonials)
4. Media assets available (logo, screenshots, clips, audio)

### Step 2: Select App-Type Blueprint

Read `references/app-type-blueprints.md` and select one:
1. UI-centric app
2. API/SDK app
3. Developer tool / infrastructure app
4. AI/automation app

Create a shot list based on the selected blueprint.

### Step 3: Narrative and Duration

1. Define the story arc: `Hook -> Problem -> Mechanism -> Proof -> CTA`
2. Choose target length: `15s`, `30s`, `45s`, or `60s`
3. Assign scene durations before implementation

### Step 4: Composition Setup

1. Define `Composition` in `src/Root.tsx`
2. Add `schema` and `defaultProps`
3. Compute duration in `calculateMetadata`
4. Connect scenes in `src/Video.tsx` using `TransitionSeries`

### Step 5: Scene Construction

1. Build reusable components first in `src/components`
2. Assemble scenes in `src/scenes` using those components
3. Use absolute positioning with constants for layout and timing
4. Keep scene files focused on orchestration, not low-level UI details

### Step 6: Typography Pass

Read `references/typography-and-readability.md` and set all major text sizes first.

1. Apply the recommended size ranges for `1920x1080`
2. Respect hard minimums unless explicitly justified
3. Confirm mobile/iOS readability before animation polish

### Step 7: Motion Pass

1. Use trapezoid fades for readability
2. Use springs for entrances and cursor-like movement
3. Add per-scene `exitOpacity` to avoid overlap artifacts during transitions
4. Use overlays/captions to make phase changes explicit

### Step 8: Timing Sanity Pass

Read `references/timing-and-debug-loop.md` and validate timing budgets:

1. Check text dwell time and reading windows
2. Check processing and result hold durations
3. Check transition overlap and handoff timing
4. Fix timeline constants before polish work

### Step 9: QA Loop (Evidence Required)

1. Capture key frames after each substantial change
2. Review visual clarity, timing, overlap, and composition balance
3. Record pass/fail evidence in a debug log
4. Iterate until all critical checkpoints pass

Use `scripts/capture-frames.sh` when useful.

If image read tools fail or return no useful content, recapture and retry. Do not proceed with unverifiable checks.

### Step 10: Final Validation

1. `npx tsc --noEmit`
2. `npm run -s build`
3. `npm run -s build:gif` if available
4. Render final mp4 and verify runtime and output size
5. Re-check key timestamps against intended scene behavior

Use `scripts/verify-build.sh` when useful.

### Step 11: Handoff and Approval

1. Report evidence-based QA summary (what passed/failed and why)
2. List known compromises or residual risks
3. Ask for explicit approval before commit/push/task completion

## Output Format

When reporting work, include:
1. Selected app type and blueprint
2. Scene structure and final duration
3. Main components implemented
4. Key animation decisions
5. Timing budget checks and results
6. Validation commands and outcomes
7. Remaining risks or follow-ups

## Guardrails

1. Use `Img + staticFile()` for local images.
2. Load fonts at module scope, not inside effects.
3. Keep `Sequence` layout and premount settings compatible.
4. Use typography hard minimums from `references/typography-and-readability.md`.
5. Concentrate complex effects in one focal area.
6. Do not optimize for too many goals in one cut; keep a single primary message.
7. Never describe output as "perfect" without explicit evidence.
8. Do not skip QA evidence even when render commands succeed.
