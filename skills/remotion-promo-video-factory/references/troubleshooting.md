# Troubleshooting

## "No Remotion entrypoint was found"

Check that `src/index.ts` registers root via `registerRoot()`.

## Sequence layout/premount mismatch

If `layout="none"` and `premountFor` conflict:
1. Remove `premountFor`, or
2. Use default sequence layout, or
3. Simplify to plain timing shift when premounting is unnecessary

## Transition overlap artifacts

If previous scene elements linger during cuts:
1. Add `exitOpacity` near scene end
2. Apply it to major foreground elements
3. Inspect 10-20 frames around transition boundaries

## 1px seam artifacts

For full-screen overlays with edge seams, use `inset: -1`.

## Fonts not applied

Load fonts at module scope. Avoid loading via `useEffect`.

## Layout collapse inside AbsoluteFill

If wrappers from `Sequence` break flex assumptions:
1. Switch to absolute coordinate layout
2. Keep wrapper-sensitive sections isolated

## Timing drift after FPS changes

Replace frame literals with second-based helpers (`sec()` or equivalent).

## False confidence from Studio preview

Do not rely on live preview alone. Always validate with still captures.

