# QA Checklist

## Keyframe Capture Coverage

Capture at least:
1. Scene starts
2. Primary interaction moments
3. Scene endings
4. Transition overlap points

## Suggested Frame Set (30fps, ~30s)

- Opening: `0, 20, 60, 72`
- Transition A: `65, 70, 75`
- Main section early: `100, 160, 220`
- Main section mid: `300, 360, 430`
- Main section late: `520, 580, 650`
- Finale: `720, 780, 840`

## Visual QA

1. Readability on small screens (use typography minimums)
2. Layer ordering and occlusion
3. Crossfade leftovers
4. Edge seams and 1px artifacts
5. Color consistency
6. Information density per frame

## Typography QA (1920x1080)

Check against `references/typography-and-readability.md`:

1. Headline is `>= 96px` (recommended `100-150px`)
2. Subtext is `>= 40px` (recommended `40-72px`)
3. Mock UI header is `>= 36px`
4. Mock UI input is `>= 33px`
5. Mock UI small text is `>= 18px` (recommended `18-27px`)
6. CTA command text is `>= 42px`
7. URL text is `>= 36px`
8. Tagline text is `>= 60px` (recommended `66px`)

## Motion QA

1. Typing speed readability
2. Processing state display duration
3. Hold time for complex result views
4. Transition smoothness across phases

## Timing Budget QA (30fps)

1. Headline visible for `>= 36f` (`>= 1.2s`)
2. Subtext visible for `>= 45f` (`>= 1.5s`)
3. Phase overlays visible for `45-75f` (`1.5-2.5s`)
4. Processing states visible for `15-30f` (`0.5-1.0s`)
5. Complex result/modal sections held for `>= 60f` (`>= 2.0s`)
6. Transition overlaps are in practical range (`8-15f` unless justified)

## Debug Evidence QA (Required)

1. Keep a frame-by-frame pass/fail log
2. Include at least one failed checkpoint and its fix when iteration occurred
3. No `UNVERIFIED` checkpoints in final report
4. Do not claim final quality without evidence log

## Build QA

1. `npx tsc --noEmit`
2. `npm run -s build`
3. `npm run -s build:gif` if available
4. Verify runtime and output file size
5. Verify final key timestamps against expected scene behavior
