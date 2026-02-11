# Timing And Debug Loop

Use this reference to prevent weak timing decisions and shallow visual validation.

## Timing Budgets (30fps baseline)

These are practical defaults for promo videos.

- Headline readability window: `>= 1.2s` (`>= 36f`)
- Subtext readability window: `>= 1.5s` (`>= 45f`)
- Mode/phase overlay display: `1.5-2.5s` (`45-75f`)
- Processing state display: `0.5-1.0s` (`15-30f`)
- Complex result/modal hold: `>= 2.0s` (`>= 60f`)
- Crossfade transition: `8-15f` typical

If timing is outside these ranges, document why.

## Typewriter Timing

- Default typing speed: `0.8 chars/frame`
- Avoid `>= 1.0` except for short emphasis bursts

## Debug Loop (Required)

Run this loop after any substantial change:

1. Capture checkpoints with `npx remotion still`
2. Inspect each image for readability and layout correctness
3. Fill the debug evidence log (pass/fail + notes)
4. Fix only failed checkpoints
5. Re-capture and re-check

Do not skip steps 2-3.

## Required Checkpoint Types

- Scene start frames
- Primary interaction frames
- Scene end frames
- Transition overlap frames
- Any frame where a key message first appears

## Debug Evidence Log Template

Use this format in your report:

| Frame | Time(s) | Expected | Observed | Status | Action |
|---|---:|---|---|---|---|
| 120 | 4.0 | Hook text fully readable | Subtext too small on mobile | FAIL | Increase subtext size 40->48 |
| 160 | 5.3 | Problem visual + caption aligned | Alignment correct | PASS | None |

## Failure Handling

If screenshot reads fail or return empty/no-content:

1. Re-render the frame
2. Verify file path and file size
3. Retry image inspection
4. Mark checkpoint as `UNVERIFIED` until inspection succeeds

Never treat `UNVERIFIED` as `PASS`.

## Final-Stage Gate

Before claiming completion:

1. All critical checkpoints must be `PASS`
2. No `UNVERIFIED` checkpoints
3. Runtime, resolution, and file size verified
4. Any commit/push/task completion requires explicit user approval
