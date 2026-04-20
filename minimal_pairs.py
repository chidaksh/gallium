"""Causal sensitivity analysis via minimal-pair persona comparison.

A minimal pair = two personas identical on every dimension EXCEPT one.
Running both on the same creative isolates the causal effect of that one
dimension on action_likelihood and per-element reactions.

This is the methodological centerpiece of the demo: it converts the
LLM-as-judge from "trust the score" into "show me how scores move when
you flip one audience attribute."
"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Any

from openai import OpenAI

from personas import PERSONAS, Persona
from creatives import CREATIVES, Creative
from pipeline import (
    EvalResult, evaluate_one, bootstrap_ci, compute_element_attribution,
)


# Built-in minimal pairs. Each = (base persona to clone, dimension to flip, low level, high level).
BUILT_IN_PAIRS: Dict[str, Dict[str, str]] = {
    "skepticism": {
        "base_persona_id": "alex_vp_eng",
        "dimension": "skepticism_level",
        "low_level": "low",
        "high_level": "high",
        "rationale": (
            "Tests whether 'B_E5_social_proof' (\"14,000 teams... 60%\") survives skeptic scrutiny. "
            "Hypothesis: high-skeptic drops sharply on this element vs. low-skeptic."
        ),
    },
    "pain": {
        "base_persona_id": "alex_vp_eng",
        "dimension": "pain_awareness",
        "low_level": "latent",
        "high_level": "acute",
        "rationale": (
            "Tests whether story-led copy (\"47 minutes\") needs acute pain to land. "
            "Hypothesis: latent-pain reads it as someone else's story; acute reads it as theirs."
        ),
    },
}


def make_paired_personas(base: Persona, dimension: str, low_level: str, high_level: str) -> tuple[Persona, Persona]:
    """Create two persona variants that differ only on `dimension`."""
    if dimension not in base.dimensions:
        raise ValueError(f"Dimension '{dimension}' not present in base persona '{base.id}'")
    low_dims = {**base.dimensions, dimension: low_level}
    high_dims = {**base.dimensions, dimension: high_level}
    p_low = replace(
        base,
        id=f"{base.id}__{dimension}={low_level}",
        label=f"{base.label} [{dimension}={low_level}]",
        dimensions=low_dims,
    )
    p_high = replace(
        base,
        id=f"{base.id}__{dimension}={high_level}",
        label=f"{base.label} [{dimension}={high_level}]",
        dimensions=high_dims,
    )
    return p_low, p_high


def compare_minimal_pair(
    results_low: List[EvalResult],
    results_high: List[EvalResult],
    creative: Creative,
) -> Dict[str, Any]:
    """Compute action_likelihood deltas and per-element deltas between paired personas."""
    al_low = [r.parsed["action_likelihood"] for r in results_low]
    al_high = [r.parsed["action_likelihood"] for r in results_high]
    al_low_ci = bootstrap_ci(al_low)
    al_high_ci = bootstrap_ci(al_high)
    delta_al = al_high_ci["mean"] - al_low_ci["mean"]

    attr_low = compute_element_attribution(results_low, creative)
    attr_high = compute_element_attribution(results_high, creative)

    element_deltas = []
    for el in creative.elements:
        eid = el.id
        a_low = attr_low[eid]
        a_high = attr_high[eid]
        element_deltas.append({
            "element_id": eid,
            "element_type": el.element_type,
            "low_score": a_low["attribution_score"],
            "high_score": a_high["attribution_score"],
            "delta": a_high["attribution_score"] - a_low["attribution_score"],
            "low_skeptic_pct": a_low["skeptic_pct"],
            "high_skeptic_pct": a_high["skeptic_pct"],
        })
    # Sort by absolute delta magnitude — biggest mover first.
    element_deltas.sort(key=lambda d: -abs(d["delta"]))

    return {
        "creative_id": creative.id,
        "low_action_likelihood":  al_low_ci,
        "high_action_likelihood": al_high_ci,
        "delta_action_likelihood": delta_al,
        "element_deltas": element_deltas,
    }


def run_minimal_pair(
    client: OpenAI,
    pair_name: str,
    creative_id: str = "B",
    n_runs: int = 5,
    model: str = "gpt-4o-mini",
    verbose: bool = True,
) -> Dict[str, Any]:
    """End-to-end: build paired personas, evaluate both on `creative_id`, return comparison."""
    if pair_name not in BUILT_IN_PAIRS:
        raise ValueError(f"Unknown pair '{pair_name}'. Available: {list(BUILT_IN_PAIRS)}")
    spec = BUILT_IN_PAIRS[pair_name]
    base = PERSONAS[spec["base_persona_id"]]
    p_low, p_high = make_paired_personas(
        base, spec["dimension"], spec["low_level"], spec["high_level"],
    )
    creative = CREATIVES[creative_id]

    if verbose:
        print(f"\n  minimal pair: {spec['dimension']} "
              f"({spec['low_level']} vs {spec['high_level']}) on variant {creative_id}")
        print(f"  rationale: {spec['rationale']}")
        print(f"  low ({spec['low_level']})")
    res_low = evaluate_one(client, p_low, creative, n_runs, model, verbose=verbose)
    if verbose:
        print(f"  high ({spec['high_level']})")
    res_high = evaluate_one(client, p_high, creative, n_runs, model, verbose=verbose)

    comparison = compare_minimal_pair(res_low, res_high, creative)
    return {
        "spec": spec,
        "comparison": comparison,
        "results_low": res_low,
        "results_high": res_high,
    }
