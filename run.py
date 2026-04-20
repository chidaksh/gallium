"""CLI entry point for CreativeIQ.

Modes:
  --mode quick          1 persona × 2 variants × 1 run (smoke test, ~$0.001)
  --mode full           All personas × all variants × N runs + both minimal pairs
  --mode minimal-pair   Just one minimal-pair run (use --pair skepticism|pain)
  --preview-prompt      Print the system + user prompt for one combo, no API call

Output:
  results/eval_{timestamp}.json   raw evaluation data
  results/report_{timestamp}.md   human-readable report
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

from dotenv import load_dotenv

from personas import PERSONAS, PORTFOLIO_WEIGHTS
from creatives import CREATIVES
from pipeline import (
    SYSTEM_PROMPT, build_user_prompt,
    run_full_eval, evaluate_one,
    build_eval_tasks, execute_tasks,
    per_persona_scores, portfolio_score, is_close_call, cohens_d,
    compute_element_attribution, persona_differentiation, segment_recommendations,
    check_position_bias, llm_self_consistency,
    compute_cost, serialize_results, EvalResult,
)
from minimal_pairs import BUILT_IN_PAIRS, run_minimal_pair, make_paired_personas, compare_minimal_pair
from evaluators import evaluate_channel_fit


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "results"


def _make_client():
    """Lazy import of OpenAI so --preview-prompt works without an API key."""
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit(
            "ERROR: OPENAI_API_KEY not set. Add it to "
            f"{SCRIPT_DIR / '.env'} (gitignored) and re-run."
        )
    return OpenAI(api_key=api_key)


# ===== Markdown report generator =====

def _fmt_ci(stats: Dict[str, float]) -> str:
    return f"{stats['mean']:.2f} [{stats['ci_low']:.2f}, {stats['ci_high']:.2f}]"


def _group_by_cell(results: List[EvalResult]) -> Dict[Tuple[str, str], List[EvalResult]]:
    """Group results by (persona_id, creative_id). Runs within a cell are ordered by run_index."""
    cells: Dict[Tuple[str, str], List[EvalResult]] = {}
    for r in results:
        cells.setdefault((r.persona_id, r.creative_id), []).append(r)
    for k in cells:
        cells[k].sort(key=lambda r: r.run_index)
    return cells


def _cell_summary(runs: List[EvalResult]) -> Dict[str, Any]:
    """Aggregate the raw runs of one (persona, creative) cell into a digestible block."""
    als = [r.parsed["action_likelihood"] for r in runs]
    overall = Counter(r.parsed["overall_reaction"] for r in runs)
    missing = Counter()
    for r in runs:
        for item in r.parsed["missing_information"]:
            missing[item.strip()] += 1
    return {
        "n_runs": len(runs),
        "action_likelihood": {
            "mean": (sum(als) / len(als)) if als else 0.0,
            "min": min(als) if als else 0,
            "max": max(als) if als else 0,
            "values": als,
        },
        "overall_reaction_counts": dict(overall),
        "missing_information_top": missing.most_common(5),
    }


def _render_cell_detail(
    persona_id: str,
    creative_id: str,
    runs: List[EvalResult],
) -> List[str]:
    """Intera-style per-cell narrative: first impressions, element reasoning, drivers, edits."""
    persona_label = PERSONAS[persona_id].label if persona_id in PERSONAS else persona_id
    creative = CREATIVES[creative_id]
    summary = _cell_summary(runs)
    al = summary["action_likelihood"]

    lines: List[str] = [
        "",
        f"### {persona_label}  ×  Variant {creative_id}",
        "",
        f"_n_runs = {summary['n_runs']}_  |  "
        f"**action_likelihood**: mean {al['mean']:.2f}, range [{al['min']}–{al['max']}]  |  "
        f"overall: {summary['overall_reaction_counts']}",
        "",
        "**First impressions (verbatim per run):**",
    ]
    for r in runs:
        fi = r.parsed["first_impression"].strip()
        if fi:
            lines.append(f"- _Run {r.run_index + 1}_: {fi}")

    # Element attribution restricted to this cell (persona-specific view).
    attr = compute_element_attribution(runs, creative)
    element_rows = [(eid, a) for eid, a in attr.items() if not eid.startswith("_")]
    if element_rows:
        element_rows.sort(key=lambda kv: -kv[1]["attribution_score"])
        lines += [
            "",
            "**Element attribution (this persona only):**",
            "",
            "| Element | Type | Trigger % | Skeptic % | Score | Score CI | Avg intensity |",
            "|---|---|---|---|---|---|---|",
        ]
        for eid, a in element_rows:
            lines.append(
                f"| `{eid}` | {a['element_type']} | {a['trigger_pct']:.0f}% | "
                f"{a['skeptic_pct']:.0f}% | {a['attribution_score']:+.0f} | "
                f"[{a['attribution_ci']['ci_low']:+.0f}, {a['attribution_ci']['ci_high']:+.0f}] | "
                f"{a['intensity_mean']:.1f} |"
            )

        # Reasoning quotes: show triggers and skeptic triggers (the ones that moved the score).
        has_quotes = any(a.get("trigger_quotes") or a.get("skeptic_quotes") for _, a in element_rows)
        if has_quotes:
            lines += ["", "**Reasoning quotes per element** (top 3):"]
            for eid, a in element_rows:
                trig_q = a["trigger_quotes"][:3]
                skep_q = a["skeptic_quotes"][:3]
                if not (trig_q or skep_q):
                    continue
                lines.append(f"\n`{eid}` ({a['element_type']}):")
                for q in trig_q:
                    lines.append(f"  - TRIGGER — {q}")
                for q in skep_q:
                    lines.append(f"  - SKEPTIC — {q}")

    # Missing information tally (what the persona wanted but didn't get).
    if summary["missing_information_top"]:
        lines += ["", "**Missing information (most cited):**"]
        for item, count in summary["missing_information_top"]:
            lines.append(f"- [{count}×] {item}")

    # Reaction drivers per run (what the LLM flagged as top drivers).
    drivers_seen = False
    for r in runs:
        drv = r.parsed["reaction_drivers"]
        if drv:
            if not drivers_seen:
                lines += ["", "**Reaction drivers (per run):**"]
                drivers_seen = True
            lines.append(f"- _Run {r.run_index + 1}_:")
            for d in drv:
                lines.append(f"  - `{d['element_or_claim']}` — {d['why']}")

    # Proposed edits (what_would_change) per run.
    edits = [(r.run_index + 1, r.parsed["what_would_change"].strip()) for r in runs]
    edits = [(i, e) for i, e in edits if e]
    if edits:
        lines += ["", "**Proposed edits (what_would_change per run):**"]
        for i, e in edits:
            lines.append(f"- _Run {i}_: {e}")

    return lines


def render_report(
    results: List[EvalResult],
    minimal_pair_outputs: Dict[str, Dict[str, Any]] | None = None,
    model: str = "gpt-4o-mini",
) -> str:
    """Build the human-readable markdown report from raw eval results.

    Structure:
      1. Headline (close-call aware) + portfolio rollup
      2. Per-persona cross-variant comparison table
      3. Per-variant element attribution (portfolio aggregate)
      4. Per-(persona, variant) cell detail — first impressions, reasoning quotes, drivers, edits
      5. Causal sensitivity (minimal pairs)
      6. Channel-fit heuristic flags
      7. Cost + cache audit
      8. Data quality
      9. Known limitations
    """
    pp = per_persona_scores(results)
    portfolio = portfolio_score(results)
    present_cids = sorted({r.creative_id for r in results})

    cell_counts: Dict[Tuple[str, str], int] = {}
    for r in results:
        cell_counts[(r.persona_id, r.creative_id)] = cell_counts.get((r.persona_id, r.creative_id), 0) + 1
    min_n = min(cell_counts.values()) if cell_counts else 0

    # Raw action_likelihood values grouped by (persona_id, creative_id) for Cohen's d.
    raw_al: Dict[Tuple[str, str], List[float]] = {}
    for r in results:
        raw_al.setdefault((r.persona_id, r.creative_id), []).append(
            float(r.parsed["action_likelihood"])
        )

    parts: List[str] = [
        "# CreativeIQ Report — Relay LinkedIn Post",
        "",
        f"_Generated {datetime.now():%Y-%m-%d %H:%M:%S}_  |  Model: `{model}`",
        "",
    ]

    # ----- 1. Headline + portfolio -----
    if portfolio:
        cids = sorted(portfolio.keys())
        ordered_means = sorted(cids, key=lambda c: -portfolio[c]["mean"])
        close_call = (
            len(ordered_means) >= 2
            and is_close_call(portfolio[ordered_means[0]], portfolio[ordered_means[1]])
        )
        parts += ["## Headline", ""]
        if close_call:
            parts += [
                f"**NO SIGNIFICANT WINNER** between Variant {ordered_means[0]} and "
                f"Variant {ordered_means[1]} — paired bootstrap CI on the difference "
                f"overlaps MDE=0.5. Recommend more samples.",
                "",
            ]
            for i, cid in enumerate(ordered_means):
                parts.append(f"- Variant {cid} (#{i+1}): {_fmt_ci(portfolio[cid])}")
        else:
            winner_cid = ordered_means[0]
            parts += [f"**WINNER: Variant {winner_cid}**", ""]
            for i, cid in enumerate(ordered_means):
                label = "winner" if i == 0 else f"#{i+1}"
                parts.append(f"- Variant {cid} ({label}): {_fmt_ci(portfolio[cid])}")
        if len(ordered_means) >= 2:
            top_cid, runner_cid = ordered_means[0], ordered_means[1]
            all_top = [v for pid in PORTFOLIO_WEIGHTS for v in raw_al.get((pid, top_cid), [])]
            all_runner = [v for pid in PORTFOLIO_WEIGHTS for v in raw_al.get((pid, runner_cid), [])]
            d = cohens_d(all_runner, all_top)
            d_label = "small" if abs(d) < 0.5 else ("medium" if abs(d) < 0.8 else "large")
            parts.append(
                f"- **Effect size (Cohen's d, {top_cid} vs {runner_cid}):** {d:+.2f} ({d_label})"
            )
        parts += [
            "",
            "_Scores are weighted action_likelihood (1-10) across the audience portfolio. "
            "CIs are 95% bootstrap intervals from intra-persona resampling weighted by "
            "portfolio weights. Close-call test uses MDE=0.5 (Kohavi et al. 2020): gaps "
            "< 0.5 points are not operationally meaningful._",
            "",
            "## Portfolio Score by Persona",
            "",
        ]
        variant_cols = " | ".join(f"Variant {cid}" for cid in present_cids)
        parts.append(f"| Persona | Weight | {variant_cols} | Per-persona winner |")
        parts.append("|" + "---|" * (3 + len(present_cids)))
        for pid, p in PERSONAS.items():
            if pid not in pp:
                continue
            w = PORTFOLIO_WEIGHTS[pid]
            scores = pp[pid]
            score_strs = [_fmt_ci(scores[cid]) if cid in scores else "—" for cid in present_cids]
            available = {cid: scores[cid]["mean"] for cid in present_cids if cid in scores}
            if len(available) >= 2:
                winner_cid = max(available, key=available.get)
                winner = f"**{winner_cid}**"
            else:
                winner = "—"
            cells = " | ".join(score_strs)
            parts.append(f"| {p.label} | {w:.0%} | {cells} | {winner} |")
    else:
        parts += [
            "_No real-persona results in this run (likely a minimal-pair-only invocation). "
            "Skipping portfolio rollup; see Causal Sensitivity below._",
        ]

    # ----- 2. Per-variant element attribution (portfolio aggregate) -----
    hallucinations: Dict[str, List[str]] = {}
    attribution_by_cid: Dict[str, Dict[str, Any]] = {}
    for cid in present_cids:
        attribution = compute_element_attribution(results, CREATIVES[cid])
        attribution_by_cid[cid] = attribution
        rows = [(eid, a) for eid, a in attribution.items() if not eid.startswith("_")]
        rows.sort(key=lambda kv: -kv[1]["attribution_score"])
        parts += [
            "",
            f"## Element Attribution — Variant {cid} (all personas)",
            "",
            "| Element | Type | Trigger % | Skeptic % | Score | Score CI | Signed-intensity CI |",
            "|---|---|---|---|---|---|---|",
        ]
        for eid, a in rows:
            parts.append(
                f"| `{eid}` | {a['element_type']} | {a['trigger_pct']:.0f}% | "
                f"{a['skeptic_pct']:.0f}% | {a['attribution_score']:+.0f} | "
                f"[{a['attribution_ci']['ci_low']:+.0f}, {a['attribution_ci']['ci_high']:+.0f}] | "
                f"{_fmt_ci(a['signed_intensity_ci'])} |"
            )
        if "_hallucinated_element_ids" in attribution:
            hallucinations[cid] = attribution["_hallucinated_element_ids"]

    # ----- 2b. Persona differentiation (collapse detection) -----
    real_pids_present = [pid for pid in PERSONAS if any(
        r.persona_id == pid for r in results
    )]
    if len(real_pids_present) >= 2:
        for cid in present_cids:
            diff = persona_differentiation(
                results, CREATIVES[cid], persona_ids=real_pids_present,
            )
            collapsed = [(eid, d) for eid, d in diff.items() if d["collapsed"]]
            parts += [
                "",
                f"## Persona Differentiation — Variant {cid}",
                "",
                "_Between-persona variance on signed intensity per element. "
                "Low variance = personas reacting identically = potential "
                "faithfulness failure (Argyle et al. 2023)._",
                "",
                "| Element | Type | Variance | Collapsed? |",
                "|---|---|---|---|",
            ]
            for eid in [el.id for el in CREATIVES[cid].elements]:
                d = diff[eid]
                flag = "**YES**" if d["collapsed"] else "no"
                parts.append(
                    f"| `{eid}` | {d['element_type']} | {d['variance']:.2f} | {flag} |"
                )
            if collapsed:
                parts += [
                    "",
                    f"**{len(collapsed)} element(s) flagged as collapsed** — "
                    "all personas reacted near-identically. These scores may reflect "
                    "LLM default behavior rather than persona-specific simulation.",
                ]

    # ----- 3. Per-(persona, variant) cell detail -----
    cells = _group_by_cell(results)
    if cells:
        parts += [
            "",
            "## Per-Cell Detail — first impressions, reasoning quotes, drivers",
            "",
            "_One subsection per (persona, variant) cell. Use this to audit specific reactions, "
            "spot hallucinated reasoning, and see the qualitative signal behind the aggregate scores._",
        ]
        # Stable ordering: iterate PERSONAS dict order (real personas first, then any synthetic),
        # then creatives in id order.
        real_pids = [pid for pid in PERSONAS if any(k[0] == pid for k in cells)]
        synthetic_pids = sorted({k[0] for k in cells} - set(PERSONAS))
        ordered_pids = real_pids + synthetic_pids
        for pid in ordered_pids:
            cids_for_pid = sorted({k[1] for k in cells if k[0] == pid})
            for cid in cids_for_pid:
                runs = cells[(pid, cid)]
                parts.extend(_render_cell_detail(pid, cid, runs))

    # ----- 3b. Segment-aware recommendations -----
    seg_recs_by_cid: Dict[str, list] = {}
    for cid in present_cids:
        recs = segment_recommendations(
            results, attribution_by_cid[cid], CREATIVES[cid],
        )
        seg_recs_by_cid[cid] = recs
        if recs:
            parts += [
                "",
                f"## Segment-Aware Recommendations — Variant {cid}",
                "",
                "_Elements with attribution score < -20, broken down by which "
                "persona segments drive the skepticism and what they'd change._",
            ]
            for rec in recs:
                parts += [
                    "",
                    f"### `{rec['element_id']}` ({rec['element_type']}) — "
                    f"score {rec['overall_score']:+.0f} "
                    f"[{rec['attribution_ci']['ci_low']:+.0f}, "
                    f"{rec['attribution_ci']['ci_high']:+.0f}]",
                    "",
                ]
                for pid, seg in rec["fix_by_segment"].items():
                    persona_label = PERSONAS[pid].label if pid in PERSONAS else pid
                    mean_si = seg["mean_signed_intensity"]
                    parts.append(
                        f"**{persona_label}** (mean signed intensity: {mean_si:+.1f}):"
                    )
                    if seg["suggested_edits"]:
                        for edit in seg["suggested_edits"][:2]:
                            parts.append(f"  - _{edit}_")
                    else:
                        parts.append("  - _(no specific edit suggested)_")
                    parts.append("")

    # Minimal-pair causal sensitivity
    if minimal_pair_outputs:
        parts += ["", "## Causal Sensitivity (Minimal Pair Analysis)", ""]
        for pair_name, output in minimal_pair_outputs.items():
            spec = output["spec"]
            cmp = output["comparison"]
            parts += [
                f"### `{pair_name}`: `{spec['dimension']}` "
                f"({spec['low_level']} → {spec['high_level']}) on Variant {cmp['creative_id']}",
                "",
                f"_Rationale_: {spec['rationale']}",
                "",
                f"- Action likelihood ({spec['low_level']}):  {_fmt_ci(cmp['low_action_likelihood'])}",
                f"- Action likelihood ({spec['high_level']}): {_fmt_ci(cmp['high_action_likelihood'])}",
                f"- **Δ action_likelihood** ({spec['high_level']} − {spec['low_level']}): "
                f"**{cmp['delta_action_likelihood']:+.2f}**",
                "",
                "**Element-level deltas** (sorted by absolute movement):",
                "",
                "| Element | Type | Low score | High score | Δ |",
                "|---|---|---|---|---|",
            ]
            for ed in cmp["element_deltas"]:
                parts.append(
                    f"| `{ed['element_id']}` | {ed['element_type']} | "
                    f"{ed['low_score']:+.0f} | {ed['high_score']:+.0f} | "
                    f"**{ed['delta']:+.0f}** |"
                )

    # Channel-fit (only for variants with results)
    parts += ["", "## Channel-Fit Heuristics (rule-based, no LLM)", ""]
    for cid in present_cids:
        flags = evaluate_channel_fit(CREATIVES[cid])
        if not flags:
            parts.append(f"- **Variant {cid}**: 0 flags")
            continue
        parts.append(f"- **Variant {cid}**: {len(flags)} flag(s)")
        for f in flags:
            parts.append(f"  - `[{f['severity']}] {f['code']}` — {f['message']}")

    # Cost
    cost = compute_cost(results, model=model)
    parts += [
        "",
        "## Cost & Cache Performance",
        "",
        f"- Total API spend: **${cost['total_cost_usd']:.4f}** ({cost['calls']} calls)",
        f"- Prompt tokens:  {cost['prompt_tokens']:,}  (cached: {cost['cached_tokens']:,})",
        f"- Completion tokens: {cost['completion_tokens']:,}",
        f"- **Cache hit rate: {cost['cache_hit_rate_pct']:.1f}%** "
        f"_(target ≥ 80% to confirm caching is working)_",
    ]

    # Data Quality section — surfaces things a reviewer should know before trusting numbers.
    parts += ["", "## Data Quality", ""]
    if min_n < 10 and min_n > 0:
        parts.append(
            f"- **Small-n CIs**: minimum n_runs per (persona, variant) cell = **{min_n}**. "
            f"Bootstrap CIs over fewer than ~10 samples are bounded by the empirical range and "
            f"should be read as descriptive, not inferential. Re-run with `--runs 30` for tighter "
            f"intervals."
        )
    else:
        parts.append(f"- n_runs per cell = {min_n}")
    if hallucinations:
        for cid, hids in hallucinations.items():
            parts.append(
                f"- **Hallucinated element IDs (Variant {cid})**: model referenced "
                f"unknown IDs {hids}. These reactions were excluded from attribution but "
                f"still consumed completion tokens."
            )
    else:
        parts.append("- No hallucinated element IDs")
    parts.append(
        "- Element order is randomized per call via deterministic seed — defends against "
        "intra-prompt anchoring on the first listed element."
    )

    # Position bias verification
    for cid in present_cids:
        bias = check_position_bias(results, CREATIVES[cid])
        if bias:
            flagged = {eid: b for eid, b in bias.items() if abs(b["spearman_rho"]) > 0.3}
            if flagged:
                parts += [
                    "",
                    f"### Position Bias — Variant {cid}",
                    "",
                    "_Spearman correlation between element position in the shuffled prompt "
                    "and signed intensity. |ρ| > 0.3 = residual bias the shuffle didn't eliminate._",
                    "",
                    "| Element | ρ | p-value | Verdict |",
                    "|---|---|---|---|",
                ]
                for eid, b in flagged.items():
                    verdict = "**biased**" if b["p_value"] < 0.05 else "suspect (not sig.)"
                    parts.append(
                        f"| `{eid}` | {b['spearman_rho']:+.2f} | {b['p_value']:.3f} | {verdict} |"
                    )
            else:
                parts.append(
                    f"- **Position bias (Variant {cid})**: no elements with |ρ| > 0.3 — "
                    f"shuffle mitigation appears effective"
                )
        else:
            parts.append(
                f"- **Position bias (Variant {cid})**: not computed "
                f"(requires scipy and element_order data)"
            )

    # LLM self-consistency (Krippendorff's alpha)
    for cid in present_cids:
        alphas = llm_self_consistency(results, cid, persona_ids=real_pids_present if len(real_pids_present) >= 2 else None)
        if alphas:
            parts += [
                "",
                f"### LLM Self-Consistency — Variant {cid} (Krippendorff's α)",
                "",
                "_Ordinal alpha on element intensities across runs. Measures whether "
                "repeated calls produce consistent judgments, not true inter-rater "
                "reliability. > 0.80 = consistent, 0.67–0.80 = tentative, < 0.67 = noisy._",
                "",
                "| Persona | α | Verdict |",
                "|---|---|---|",
            ]
            for pid, a_val in alphas.items():
                if a_val >= 0.80:
                    verdict = "consistent"
                elif a_val >= 0.67:
                    verdict = "tentative"
                else:
                    verdict = "**noisy**"
                label = PERSONAS[pid].label if pid in PERSONAS else pid
                parts.append(f"| {label} | {a_val:.2f} | {verdict} |")
        else:
            parts.append(
                f"- **LLM self-consistency (Variant {cid})**: not computed "
                f"(requires `krippendorff` package)"
            )

    parts += [
        "",
        "## Known Limitations",
        "",
        "- LLM-as-judge has documented biases (Zheng et al. 2023, *Judging LLM-as-a-Judge*). "
        "We mitigate via (a) hashlib-derived per-call seeds, (b) multi-run averaging with bootstrap "
        "CIs, (c) per-call element-order randomization, (d) paired-bootstrap close-call flagging on "
        "the difference of variant means (not marginal CI overlap).",
        "- OpenAI's `seed` parameter is best-effort and depends on `system_fingerprint`; identical "
        "(seed, prompt) pairs are not strictly guaranteed to return identical outputs.",
        "- Persona behavioral rules and channel-fit heuristics are derived from public best-practice "
        "guidance, not validated against historical CTR data. Predictions should be calibrated against "
        "real outcomes before production use.",
        "- Single-creative-per-call evaluation sidesteps pairwise position bias. Element-order "
        "randomization addresses the intra-prompt analogue.",
    ]

    return "\n".join(parts)


# ===== CLI entry =====

def cmd_preview_prompt():
    persona = PERSONAS["alex_vp_eng"]
    creative = CREATIVES["B"]
    print("=" * 80)
    print("SYSTEM PROMPT")
    print("=" * 80)
    print(SYSTEM_PROMPT)
    print()
    print("=" * 80)
    print("USER PROMPT")
    print("=" * 80)
    print(build_user_prompt(persona, creative))
    print()
    print("=" * 80)
    print(f"Sizes: system={len(SYSTEM_PROMPT)} chars (~{len(SYSTEM_PROMPT)//4} tokens), "
          f"user={len(build_user_prompt(persona, creative))} chars")


def cmd_quick(client, model: str, output_dir: Path):
    cids = list(CREATIVES.keys())
    print(f"MODE: quick (1 persona x {len(cids)} variants x 1 run)")
    results = run_full_eval(
        client, n_runs=1, model=model,
        persona_ids=["alex_vp_eng"], creative_ids=cids,
    )
    _save_outputs(results, None, model, output_dir, prefix="quick_eval")


def cmd_full(client, model: str, output_dir: Path, n_runs: int):
    """Unified-batch full eval.

    All full-eval AND minimal-pair calls are merged into one task list and
    dispatched in a single parallel pool with one shared warmup. This avoids
    paying the ~15-20s sequential cache-warmup cost once per sub-batch
    (5 sub-batches in the old design = 75-100s of pure serialization).
    """
    print(f"MODE: full ({len(PERSONAS)} personas x {len(CREATIVES)} variants x {n_runs} runs + minimal pairs)")

    # 1) Full-eval pairs
    full_pairs = [(PERSONAS[pid], CREATIVES[cid]) for pid in PERSONAS for cid in CREATIVES]
    full_tasks = build_eval_tasks(full_pairs, n_runs)

    # 2) Minimal-pair synthetic personas (always evaluated on Variant B)
    paired: Dict[str, tuple] = {}  # pair_name -> (p_low, p_high)
    mp_pairs: List[tuple] = []
    creative_b = CREATIVES["B"]
    for pname, spec in BUILT_IN_PAIRS.items():
        base = PERSONAS[spec["base_persona_id"]]
        p_low, p_high = make_paired_personas(
            base, spec["dimension"], spec["low_level"], spec["high_level"],
        )
        paired[pname] = (p_low, p_high)
        mp_pairs.append((p_low, creative_b))
        mp_pairs.append((p_high, creative_b))
    mp_tasks = build_eval_tasks(mp_pairs, n_runs)

    all_tasks = full_tasks + mp_tasks
    print(f"  unified batch: {len(all_tasks)} calls "
          f"({len(full_tasks)} full + {len(mp_tasks)} minimal-pair) — "
          f"1 warmup, then parallel")
    all_results = execute_tasks(client, all_tasks, model=model, max_workers=20)

    # 3) Split results back by persona id
    real_pids = set(PERSONAS.keys())
    full_results = [r for r in all_results if r.persona_id in real_pids]

    mp_outputs: Dict[str, Dict[str, Any]] = {}
    for pname, (p_low, p_high) in paired.items():
        res_low = [r for r in all_results if r.persona_id == p_low.id]
        res_high = [r for r in all_results if r.persona_id == p_high.id]
        mp_outputs[pname] = {
            "spec": BUILT_IN_PAIRS[pname],
            "comparison": compare_minimal_pair(res_low, res_high, creative_b),
            "results_low": res_low,
            "results_high": res_high,
        }

    _save_outputs(full_results, mp_outputs, model, output_dir, prefix="full_eval")


def cmd_minimal_pair(client, model: str, output_dir: Path, n_runs: int, pair: str, creative_id: str):
    print(f"MODE: minimal-pair  pair={pair}  creative={creative_id}  runs={n_runs}")
    output = run_minimal_pair(client, pair, creative_id=creative_id, n_runs=n_runs, model=model)
    # Combine the two persona's results so the report has element_attribution context
    all_results = output["results_low"] + output["results_high"]
    _save_outputs(all_results, {pair: output}, model, output_dir, prefix=f"mp_{pair}")


def _build_summary_block(results: List[EvalResult], model: str) -> Dict[str, Any]:
    """Derived aggregates so the JSON is browsable without rerunning the pipeline.

    Everything here is deterministic given `results`, so it's safe to regenerate
    at any time from the raw list. We include:
      - portfolio: weighted rollup with CI and close-call flag per pair
      - per_persona_scores: per-cell CI on action_likelihood
      - per_variant_element_attribution: portfolio-aggregate element scores
      - cost: token spend + cache hit rate
    Bootstrap samples from portfolio_score are dropped before serialization
    (numpy arrays, not JSON-friendly, and re-derivable).
    """
    pp = per_persona_scores(results)
    portfolio = portfolio_score(results)
    present_cids = sorted({r.creative_id for r in results})

    portfolio_clean: Dict[str, Dict[str, float]] = {}
    for cid, stats in portfolio.items():
        portfolio_clean[cid] = {k: v for k, v in stats.items() if k != "_bootstrap_samples"}

    close_call = None
    if len(portfolio) >= 2:
        ordered = sorted(portfolio.keys(), key=lambda c: -portfolio[c]["mean"])
        top_two = ordered[:2]
        close_call = {
            "variants": top_two,
            "is_close_call": bool(is_close_call(portfolio[top_two[0]], portfolio[top_two[1]])),
        }

    attr_by_cid: Dict[str, Dict[str, Any]] = {}
    diff_by_cid: Dict[str, Dict[str, Any]] = {}
    bias_by_cid: Dict[str, Dict[str, Any]] = {}
    consistency_by_cid: Dict[str, Dict[str, float]] = {}
    seg_recs_by_cid: Dict[str, list] = {}
    real_pids = [pid for pid in PERSONAS if any(r.persona_id == pid for r in results)]
    for cid in present_cids:
        creative = CREATIVES[cid]
        attr = compute_element_attribution(results, creative)
        attr_by_cid[cid] = attr
        if len(real_pids) >= 2:
            diff_by_cid[cid] = persona_differentiation(results, creative, persona_ids=real_pids)
        bias_by_cid[cid] = check_position_bias(results, creative)
        consistency_by_cid[cid] = llm_self_consistency(results, cid, persona_ids=real_pids or None)
        seg_recs_by_cid[cid] = segment_recommendations(results, attr, creative)

    effect_sizes = {}
    if len(portfolio) >= 2:
        from pipeline import PORTFOLIO_WEIGHTS as _PW
        ordered = sorted(portfolio.keys(), key=lambda c: -portfolio[c]["mean"])
        top_cid, runner_cid = ordered[0], ordered[1]
        all_top = [float(r.parsed["action_likelihood"]) for r in results
                   if r.persona_id in _PW and r.creative_id == top_cid]
        all_runner = [float(r.parsed["action_likelihood"]) for r in results
                      if r.persona_id in _PW and r.creative_id == runner_cid]
        effect_sizes["portfolio"] = {
            "cohens_d": cohens_d(all_runner, all_top),
            "variants": [top_cid, runner_cid],
        }

    return {
        "portfolio": portfolio_clean,
        "close_call": close_call,
        "effect_sizes": effect_sizes,
        "per_persona_scores": pp,
        "per_variant_element_attribution": attr_by_cid,
        "persona_differentiation": diff_by_cid,
        "position_bias": bias_by_cid,
        "llm_self_consistency": consistency_by_cid,
        "segment_recommendations": seg_recs_by_cid,
        "cost": compute_cost(results, model=model) if results else None,
    }


def _build_results_by_cell(results: List[EvalResult]) -> Dict[str, List[Dict[str, Any]]]:
    """Group raw results by '<persona_id>__<creative_id>' for easy inspection."""
    cells = _group_by_cell(results)
    out: Dict[str, List[Dict[str, Any]]] = {}
    for (pid, cid), runs in cells.items():
        out[f"{pid}__{cid}"] = serialize_results(runs)
    return out


def _save_outputs(results, mp_outputs, model, output_dir: Path, prefix: str):
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{prefix}.json"

    report = render_report(results, mp_outputs, model=model)

    payload: Dict[str, Any] = {
        "model": model,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "report": report,
        "summary": _build_summary_block(results, model),
        "results_by_cell": _build_results_by_cell(results),
        "results": serialize_results(results),
    }
    if mp_outputs:
        payload["minimal_pairs"] = {
            name: {
                "spec": out["spec"],
                "comparison": out["comparison"],
                "results_low":  serialize_results(out["results_low"]),
                "results_high": serialize_results(out["results_high"]),
            }
            for name, out in mp_outputs.items()
        }
    json_path.write_text(json.dumps(payload, indent=2, default=str))

    print(f"\n{'=' * 80}")
    print(report)
    print(f"{'=' * 80}")
    print(f"\nSaved to: {json_path}")


def main():
    load_dotenv(SCRIPT_DIR / ".env")

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mode", choices=["quick", "full", "minimal-pair", "preview-prompt"], required=True)
    p.add_argument("--runs", type=int, default=5, help="N runs per (persona, variant) cell")
    p.add_argument("--model", default="gpt-4o-mini")
    p.add_argument("--pair", choices=list(BUILT_IN_PAIRS.keys()), default="skepticism",
                   help="Which minimal pair to use in --mode minimal-pair")
    p.add_argument("--creative-id", choices=list(CREATIVES.keys()), default="B",
                   help="Which variant to evaluate in --mode minimal-pair")
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = p.parse_args()

    output_dir = Path(args.output_dir)

    if args.mode == "preview-prompt":
        cmd_preview_prompt()
        return

    client = _make_client()
    if args.mode == "quick":
        cmd_quick(client, args.model, output_dir)
    elif args.mode == "full":
        cmd_full(client, args.model, output_dir, args.runs)
    elif args.mode == "minimal-pair":
        cmd_minimal_pair(client, args.model, output_dir, args.runs, args.pair, args.creative_id)


if __name__ == "__main__":
    main()
