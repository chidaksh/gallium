# CreativeIQ Dashboard — UI Kit

A polished, executive-ready web dashboard for CreativeIQ evaluation results. Built to showcase the tool to Gallium's CEO, co-founders, and founding engineers.

## Quick start

Open `index.html` in any browser — no build step, no server required. Works directly via `file://`.

## What's in here

- `index.html` — self-contained dashboard (CSS, all React components, and app logic inlined for `file://` compatibility)
- `data.js` — real pipeline output from `results/full_eval.json` (scores, attribution, minimal pairs, diagnostics)
- `components.jsx`, `components2.jsx` — original component source files (kept for reference; not imported at runtime)

## Data

All values in `data.js` are sourced from actual pipeline runs, not mocks:
- Portfolio scores: C = 7.15, A = 6.25, B = 6.06
- Per-persona heatmap scores from 5-run evaluation
- Element attribution scores (-100 to +100)
- Minimal-pair causal experiments (skepticism, pain awareness)
- Diagnostics: self-consistency 0.72, persona differentiation 0.68, 1 position bias flag

## Design notes

- Variant color language from `dashboard.py`: `#4361ee` (A), `#f72585` (B), `#06d6a0` (C)
- Typography: Inter + JetBrains Mono via Google Fonts, tabular numerics throughout
- Interactive: click persona rows to filter heatmap, switch between minimal-pair experiments, expand diagnostics panel
- Sections: Hero, Who Prefers What (heatmap), Element Attribution, Causal Sensitivity, Recommendations, Diagnostics
