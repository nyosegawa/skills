# Timeline And Motion Patterns

## Base Helpers

```tsx
const frame = useCurrentFrame();
const {fps} = useVideoConfig();
const sec = (s: number) => Math.round(s * fps);
```

Use second-based constants for phase control.

```tsx
const PHASE_A = 2;
const PHASE_B = 8;
const PHASE_C = 15;
const END = 30;
```

## Trapezoid Fade Pattern

```tsx
const opacity = interpolate(
  frame,
  [startIn, endIn, startOut, endOut],
  [0, 1, 1, 0],
  {extrapolateLeft: "clamp", extrapolateRight: "clamp"},
);
```

This keeps text and key visuals readable longer than simple 2-point fades.

## Typewriter Pattern

```tsx
const chars = Math.max(0, Math.floor((frame - sec(2)) * 0.8));
const visible = text.slice(0, Math.min(chars, text.length));
```

Recommended speed:
- `0.8` for readable narration pace
- `1.0+` for short burst moments only

## TransitionSeries Overlap Control

Use per-scene exit fade to prevent crossfade artifacts:

```tsx
const exitOpacity = interpolate(frame, [sec(END - 0.5), sec(END)], [1, 0], {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
});
```

Multiply key element opacity by `exitOpacity`.

## Overlay Timing Rule

Avoid stacking entry fades immediately after a crossfade cut.

Use:
1. Strong starting visibility for context overlays
2. Controlled fade-out for handoff

## Duration Rule

`totalFrames = sum(scene frames) - sum(transition overlap frames)`

Use `calculateMetadata` to compute this dynamically.

## Practical Timing Budget (30fps)

Apply these defaults before final polish:

- Headline readable hold: `>= 36f` (`>= 1.2s`)
- Subtext readable hold: `>= 45f` (`>= 1.5s`)
- Overlay title blocks: `45-75f` (`1.5-2.5s`)
- Processing states: `15-30f` (`0.5-1.0s`)
- Complex result/modal views: `>= 60f` (`>= 2.0s`)

If you deviate, document the reason in the report.

## Spring Heuristics

- `damping: 200`: stable and subtle
- `damping: 10-14, mass: 0.2, stiffness: 300+`: punchy entrances
- `damping: 28, mass: 0.4, stiffness: 120`: natural pointer-like movement

## Effect Budget

1. Put complex effects in one focal section.
2. Avoid repeating the same flashy effect across every scene.
3. Prefer clarity over novelty in conversion-oriented promos.
