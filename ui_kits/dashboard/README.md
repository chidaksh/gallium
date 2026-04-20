# CreativeIQ Dashboard — UI Kit

A recreation of the CreativeIQ Streamlit dashboard, re-imagined as a polished executive-ready web experience. Built to showcase the tool to Gallium's CEO, co-founders, and founding engineers.

## What's in here

- `index.html` — full interactive dashboard
- `components.jsx` — React components (Header, Sidebar, Hero, Heatmap, Attribution, MinimalPair, Recommendations)
- `data.js` — realistic mock data mirroring `results/full_eval.json` shape

## Design notes

- Keeps the variant color language from `dashboard.py` (`#4361ee`, `#f72585`, `#06d6a0`)
- Upgrades: proper typographic hierarchy, tabular numerics, a two-column exec layout, connected-dot deltas instead of text tables
- Interactive — click persona rows to filter, switch between the two minimal-pair experiments, expand the Under-the-Hood diagnostics
