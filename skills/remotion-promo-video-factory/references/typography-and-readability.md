# Typography and Readability Rules

Use this reference for text sizing decisions in promo videos.
Base composition: `1920x1080`.

## Core Principle

Do not optimize for style before readability.
If text is hard to read on a phone, the cut fails regardless of animation quality.

## Recommended Font Sizes (1920x1080)

These values are validated from production iteration and should be treated as defaults.

- Headline: `100-150px`
- Subtext: `40-72px`
- Mock UI header: `36px`
- Mock UI input: `33px`
- Mock UI small text: `18-27px`
- CTA command text: `42px`
- URL text: `36px`
- Tagline text: `66px`

## Hard Minimums (Do not go below unless explicitly justified)

- Headline: `>= 96px`
- Subtext: `>= 40px`
- Mock UI header: `>= 36px`
- Mock UI input: `>= 33px`
- Mock UI small text: `>= 18px`
- CTA command text: `>= 42px`
- URL text: `>= 36px`
- Tagline text: `>= 60px`

## iOS / Mobile Viewing Guardrails

When the primary audience watches on iPhone/mobile:

1. Assume 16:9 video will be viewed on a small screen first.
2. Keep critical copy in the central safe zone (avoid placing key text near screen edges).
3. Prioritize larger text over visual density.
4. If a caption is not readable in a quick mobile preview, increase size first before changing color/effects.

## Workflow Integration

1. Set font sizes from this table before animation tuning.
2. Capture keyframes with `npx remotion still`.
3. Review readability first, then timing and polish.
4. Log any deliberate exceptions in the final report.

## Optional Utility: fitText for constrained containers

Use official Remotion text measurement when container width is dynamic:

```tsx
import {fitText} from '@remotion/layout-utils';

const {fontSize} = fitText({
  text: headline,
  withinWidth: 1200,
  fontFamily,
  fontWeight: '700',
});

const resolvedFontSize = Math.max(100, Math.min(fontSize, 150));
```

If you measure text dimensions, follow official guidance and ensure fonts are loaded first.

Reference: official Remotion rule `rules/measuring-text.md`.
