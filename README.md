# CreativeIQ — Pre-Flight Creative Evaluation

LLM-as-judge framework that evaluates marketing creative variants against synthetic personas defined by behavioral dimensions. Outputs segment-dependent winners with element-level attribution, causal sensitivity analysis, bootstrap confidence intervals, and data quality diagnostics.

Built as a generalization of [MedCreatives](https://github.com/chidaksh/MedCreatives) (pharma persona evaluation), adapted to B2B SaaS marketing for Gallium's multi-agent pipeline.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
OPENAI_API_KEY=sk-...
```

## Files

| File | Purpose |
|------|---------|
| `dimensions.py` | 5 behavioral dimensions (buying stage, skepticism, decision driver, pain awareness, attention mode) |
| `personas.py` | 4 weighted personas + portfolio weights |
| `creatives.py` | 3 variants (ROI-led, story-driven, social proof-led), each decomposed into labeled elements with semantic properties |
| `pipeline.py` | LLM calls, JSON validation, bootstrap CIs, Cohen's d, portfolio rollup, element attribution, persona differentiation, position bias, LLM self-consistency (Krippendorff's alpha), calibration stub |
| `minimal_pairs.py` | Causal sensitivity — flip one dimension, measure the delta |
| `evaluators.py` | Rule-based channel-fit heuristics (no LLM) |
| `run.py` | CLI runner + markdown report generation |
| `test_pipeline.py` | 57 tests covering statistical functions, validation, and diagnostics |

## Usage

```bash
# Full evaluation — 4 personas x 3 variants x 5 runs + minimal pairs (~$0.04)
python run.py --mode full --runs 5

# Quick smoke test — 1 persona x 3 variants x 1 run (~$0.002)
python run.py --mode quick

# Single minimal-pair causal test
python run.py --mode minimal-pair --pair skepticism --runs 5
python run.py --mode minimal-pair --pair pain --runs 5

# Preview prompt without calling API
python run.py --mode preview-prompt
```

## CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--mode` | required | `quick`, `full`, `minimal-pair`, or `preview-prompt` |
| `--runs N` | `5` | Runs per (persona, variant) cell |
| `--model` | `gpt-4o-mini` | OpenAI model |
| `--pair` | `skepticism` | Which minimal pair (`skepticism` or `pain`) |
| `--creative-id` | `B` | Variant for minimal-pair mode (`A`, `B`, or `C`) |
| `--output-dir` | `./results` | Output directory |

## Output

Results are saved to `results/`:
- `full_eval.json` — raw data + embedded markdown report + summary aggregates
- `findings.md` — human-readable analysis of key results

## Personas

| Persona | Role | Weight | Profile |
|---------|------|--------|---------|
| Alex | VP Engineering, Series B | 30% | consideration, high skepticism, ROI-focused, acute pain, passive scroll |
| Jordan | Head of Remote, scale-up | 25% | decision, medium skepticism, trust-focused, acute pain, active research |
| Sam | Founder/CEO, early-stage | 20% | awareness, low skepticism, identity-driven, latent pain, passive scroll |
| Taylor | Senior Engineer IC | 25% | consideration, high skepticism, pain-driven, latent pain, warm network |

## Creative Variants

**Relay** — async video messaging for distributed teams. Three LinkedIn organic post variants, each designed to activate a different decision driver:

| Variant | Strategy | Activates | Hook |
|---------|----------|-----------|------|
| **A** | ROI-led, analytical | Alex (ROI-focused) | "3 recurring syncs. 30 minutes each. 8 people on every call." |
| **B** | Story-driven, tension-first | Taylor (pain-driven) + Sam (identity-driven) | "Our last 'quick sync' took 47 minutes." |
| **C** | Social proof-led, peer-validation | Jordan (trust-focused) | "Linear, Vercel, Lattice — all made the same change last year." |

## Key Result

**Variant C wins globally** at 7.15 [6.99, 7.32] (Cohen's d = +0.90 vs A), but the finding is segment-dependent — no variant wins every persona. Jordan ties between A and C (7.80); Sam shows the largest spread (A: 4.80, C: 7.00). The minimal-pair analysis confirms B_E5 social proof as B's key vulnerability: skepticism high→low swings it from +60 to -100. See `results/findings.md` for the full analysis.

## Statistical Apparatus

- Bootstrap CIs (1000 resamples, percentile method) with deterministic seeds
- Paired bootstrap close-call detection with MDE = 0.5 (Kohavi et al. 2020)
- Cohen's d (pooled-SD) for effect size
- Element-level attribution with direction-based bootstrap CIs
- Persona differentiation via between-persona variance (collapse detection)
- Position bias verification via Spearman correlation on shuffled element order
- LLM self-consistency via Krippendorff's alpha (ordinal)
- Segment-aware recommendations for underperforming elements
- Calibration stub (Brier score, rank correlation) for future real-data validation
- Unified batch dispatch with OpenAI prompt caching (72%+ cache hit rate)
