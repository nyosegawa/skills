# App-Type Blueprints

Choose one blueprint before implementation. Do not mix multiple blueprints unless there is a clear narrative reason.

## 1. UI-Centric App (Web/Mobile/SaaS)

### Best for
- UX and visual interaction are the main value

### 30s Structure
1. Hook (0-4s)
2. Problem or friction (4-9s)
3. Guided interaction demo (9-22s)
4. Result and proof (22-27s)
5. CTA (27-30s)

### Visual Strategy
- Device or browser frames
- Cursor and highlights
- Context overlays during phase changes

### Mobile/iOS Readability Notes
- Assume many viewers will watch on iPhone-sized screens.
- Keep key copy in center-safe zones; avoid edge-hugging text.
- Use `references/typography-and-readability.md` size ranges before motion polish.

## 2. API/SDK Product

### Best for
- Integration speed and reliability matter more than UI

### 30s Structure
1. Hook with concrete benefit (0-4s)
2. Setup flow (4-10s)
3. Request/response walkthrough (10-21s)
4. Reliability indicators (21-27s)
5. CTA (27-30s)

### Visual Strategy
- Terminal and code cards
- Request/response panels
- JSON diffs and status badges

## 3. Developer Tool / Infrastructure

### Best for
- DX, performance, observability, or stability improvements

### 30s Structure
1. Baseline pain (0-3s)
2. Existing workflow baseline (3-8s)
3. Tool in action (8-20s)
4. Quantified impact (20-27s)
5. CTA (27-30s)

### Visual Strategy
- Terminal/log timelines
- Before/after split
- Metric cards and tiny charts

## 4. AI / Automation Product

### Best for
- Input-to-output transformation is core value

### 30s Structure
1. Hook with transformation statement (0-4s)
2. Input context (4-9s)
3. Plan/execute flow (9-20s)
4. Output quality and controls (20-27s)
5. CTA (27-30s)

### Visual Strategy
- Prompt/result panels
- Task checklist timeline
- Variant picker and comparison cards

## Duration Variants

- 15s: Hook -> Core mechanism -> CTA
- 30s: Hook -> Problem -> Mechanism -> Proof -> CTA
- 45s: 30s flow + one deeper proof block
- 60s: 45s flow + short case-style evidence

## Selection Heuristic

Prioritize in this order:
1. What proof best supports the core promise
2. What artifacts are available now (UI, logs, code, metrics)
3. Who the viewer is (end user vs. builder)
