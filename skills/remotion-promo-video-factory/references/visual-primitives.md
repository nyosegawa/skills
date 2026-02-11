# Visual Primitives

Reusable visual blocks that work across app categories.

## Layer Model

1. Background layer: gradients, noise, abstract shapes
2. Content layer: UI, code, logs, charts, responses
3. Guidance layer: labels, callouts, arrows, highlights
4. Context layer: phase title, metric chips, mode labels

## Primitive Set

### Product Surface Primitives
- Browser frame
- Device frame
- App card
- Overlay panel

### Builder Primitives
- Terminal card
- Code snippet card
- Request/response card
- Diff card

### Proof Primitives
- Metric chips
- Tiny chart card
- Progress timeline
- Pass/fail badge

## Composition Pattern

```tsx
<AbsoluteFill>
  <BackgroundLayer />
  <ContentLayer />
  <GuidanceLayer />
  <ContextLayer />
</AbsoluteFill>
```

## Reuse Rules

1. Keep components prop-driven (`state`, `label`, `accent`, `variant`).
2. Keep time logic in scene orchestration, not primitive components.
3. Use product-neutral names to enable reuse.

## Placement Rules

1. Prefer `AbsoluteFill` with explicit absolute coordinates.
2. Store key coordinates in constants.
3. Validate `Sequence` layout behavior when introducing premounting.

