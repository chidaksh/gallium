"""LLM evaluation pipeline.

Single LLM call evaluates ONE persona reading ONE creative variant.
N runs per (persona, variant) cell give us variance for bootstrap CIs.

Cache strategy: SYSTEM_PROMPT is built once at module import and is
byte-identical across all calls — OpenAI auto-caches prefixes >1024 tokens
reused within ~5 min. We log `cached_tokens` per call to verify hit rate.
"""

from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from openai import OpenAI, APIError, RateLimitError

from dimensions import render_dimensions_for_prompt
from personas import PERSONAS, PORTFOLIO_WEIGHTS, Persona, render_persona_for_prompt
from creatives import CREATIVES, Creative, render_creative_for_prompt


# Schema validation — catches LLM output problems at the source (triggers retry),
# so downstream aggregation code can use direct access instead of silent defaults.

_REQUIRED_FIELDS = {
    "first_impression": str,
    "element_reactions": list,
    "missing_information": list,
    "overall_reaction": str,
    "action_likelihood": (int, float),
    "reaction_drivers": list,
    "what_would_change": str,
    "chain_of_thought": str,
}
_VALID_REACTIONS = frozenset({"TRIGGER", "NON_TRIGGER", "SKEPTICISM_TRIGGER"})


def _validate_parsed(parsed: Dict[str, Any]) -> None:
    """Validate LLM JSON against expected schema. Raises ValueError on violation."""
    for field, expected in _REQUIRED_FIELDS.items():
        if field not in parsed:
            raise ValueError(f"Missing required field: '{field}'")
        if not isinstance(parsed[field], expected):
            raise ValueError(
                f"'{field}' must be {expected}, got {type(parsed[field]).__name__}: {parsed[field]!r}"
            )
    al = parsed["action_likelihood"]
    if not (1 <= al <= 10):
        raise ValueError(f"action_likelihood={al} outside valid range [1, 10]")
    for i, er in enumerate(parsed["element_reactions"]):
        if not isinstance(er, dict):
            raise ValueError(f"element_reactions[{i}] is {type(er).__name__}, expected dict: {er!r}")
        for req in ("element_id", "reaction", "intensity", "reasoning"):
            if req not in er:
                raise ValueError(f"element_reactions[{i}] missing '{req}'")
        if not isinstance(er["reaction"], str):
            raise ValueError(f"element_reactions[{i}].reaction must be str, got {type(er['reaction']).__name__}")
        if er["reaction"].upper() not in _VALID_REACTIONS:
            raise ValueError(f"element_reactions[{i}].reaction='{er['reaction']}' not in {_VALID_REACTIONS}")
        if not isinstance(er["intensity"], (int, float)):
            raise ValueError(f"element_reactions[{i}].intensity must be numeric, got {type(er['intensity']).__name__}")


# Pricing per token (gpt-4o-mini, as published by OpenAI). Used only for cost reporting.
PRICING = {
    "gpt-4o-mini": {
        "input":  0.15 / 1_000_000,
        "cached": 0.075 / 1_000_000,
        "output": 0.60 / 1_000_000,
    },
}


def _build_system_prompt() -> str:
    """Built once at import. Byte-identical across calls — required for caching."""
    return (
        "You are a synthetic marketing-audience evaluator. Your job is to simulate one specific "
        "person's reaction to a marketing creative, given their behavioral profile, and report the "
        "reaction as a strict JSON object.\n"
        "\n"
        "You will be given:\n"
        "1. A behavioral profile (one assignment of audience dimensions)\n"
        "2. A demographic line\n"
        "3. A creative decomposed into labeled elements\n"
        "\n"
        "You must:\n"
        "1. Adopt the persona fully — read everything as if you ARE this person\n"
        "2. React in their voice, with their specific frictions and motivators\n"
        "3. Stay grounded in realistic professional behavior — do not become a caricature "
        "of your assigned dimensions. A high-skeptic still reads the full creative before "
        "judging; a passive scroller still notices genuinely surprising content. React as a "
        "real person in this role would, not as the extreme version of a label.\n"
        "4. Return JSON only (no prose outside the JSON object)\n"
        "\n"
        + render_dimensions_for_prompt()
        + "\n\n"
        "# OUTPUT JSON SCHEMA\n"
        "\n"
        "You MUST return a single JSON object with these exact fields:\n"
        "\n"
        "{\n"
        '  "first_impression": "1-2 sentences in the persona\'s voice describing your gut reaction",\n'
        '  "element_reactions": [\n'
        "    {\n"
        '      "element_id": "<exact ID like A_E1_opener, from the element decomposition>",\n'
        '      "reaction": "TRIGGER | NON_TRIGGER | SKEPTICISM_TRIGGER",\n'
        '      "intensity": <integer 1-5; 5 = strongest>,\n'
        '      "reasoning": "1 sentence in persona\'s voice — must reference SPECIFIC text"\n'
        "    }\n"
        "  ],\n"
        '  "missing_information": ["thing you would want to know", "another"],\n'
        '  "overall_reaction": "resonates | neutral | confusion | skepticism | rejection",\n'
        '  "action_likelihood": <integer 1-10; how likely you are to take the CTA action>,\n'
        '  "reaction_drivers": [{"element_or_claim": "...", "why": "..."}],\n'
        '  "what_would_change": "1 sentence on what edit would most increase action_likelihood",\n'
        '  "chain_of_thought": "free-form 2-4 sentence reasoning trace"\n'
        "}\n"
        "\n"
        "# REACTION SEMANTICS\n"
        "\n"
        "- TRIGGER: this element MOVED you toward the CTA (positive engagement, recognition, trust earned)\n"
        "- NON_TRIGGER: this element passed by — neither helped nor hurt\n"
        "- SKEPTICISM_TRIGGER: this element ACTIVELY raised your guard (vague claim, unsupported stat, overclaim, brand mismatch)\n"
        "\n"
        "Intensity 1 = barely noticeable. Intensity 5 = this is the moment that decided your overall reaction.\n"
        "\n"
        "# JUDGE action_likelihood INDEPENDENTLY\n"
        "\n"
        "action_likelihood (1-10) is your PRIMARY measurement. It is the integer probability "
        "(scaled to 10) that you would take the CTA action right now if you saw this in your feed. "
        "Set it based on your actual assessment of the creative — do NOT bin it from overall_reaction. "
        "overall_reaction is a separate categorical summary; the two fields can disagree if the creative "
        "produces, e.g., a partial-resonance moment that still doesn't move you to act.\n"
        "\n"
        "# QUALITY BAR\n"
        "\n"
        "Your reasoning fields MUST quote or reference specific text from the creative. Generic "
        "statements (\"this is engaging\", \"this builds trust\") are unacceptable. You are simulating "
        "ONE specific person, not summarizing best practices.\n"
        "\n"
        "You MUST emit one element_reactions entry per element shown in the decomposition. Do not skip elements.\n"
    )


# Module-level constant — never recomputed. This is what makes caching work.
SYSTEM_PROMPT = _build_system_prompt()


def build_user_prompt(
    persona: Persona,
    creative: Creative,
    shuffle_seed: Optional[int] = None,
    return_order: bool = False,
) -> str | Tuple[str, List[str]]:
    """User-message half of the prompt. Variable per call (this is the un-cached suffix).

    If `shuffle_seed` is provided, element order in the rendered creative is permuted
    with a deterministic seed — defends against the LLM anchoring on the first element
    listed in the prompt. Element attribution is keyed by element_id, so it is robust
    to order.

    If `return_order` is True, returns (prompt_text, element_id_order) for
    downstream position bias analysis.
    """
    creative_render = render_creative_for_prompt(
        creative, shuffle_seed=shuffle_seed, return_order=return_order,
    )
    if return_order:
        creative_text, order = creative_render
    else:
        creative_text = creative_render

    prompt = (
        f"{render_persona_for_prompt(persona)}\n\n"
        f"{creative_text}\n\n"
        f"# YOUR TASK\n\n"
        f"Return the JSON object now, with one element_reactions entry per element above. "
        f"No prose outside the JSON."
    )
    if return_order:
        return prompt, order
    return prompt


@dataclass
class EvalResult:
    persona_id: str
    creative_id: str
    run_index: int
    seed: int
    parsed: Dict[str, Any]
    prompt_tokens: int
    cached_tokens: int
    completion_tokens: int
    element_order: List[str] = field(default_factory=list)


def _call_llm(client: OpenAI, user_prompt: str, model: str, seed: int) -> Dict[str, Any]:
    """One API call. Returns dict with parsed JSON + token usage.

    `max_tokens=2000` caps output (~3x typical response size) to prevent
    runaway generation, where the model occasionally loops and produces
    tens of thousands of tokens before truncating mid-JSON.
    """
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
        seed=seed,
        max_tokens=2000,
    )
    content = resp.choices[0].message.content
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON (len={len(content)}): {e}") from e
    _validate_parsed(parsed)
    usage = resp.usage
    cached = 0
    details = getattr(usage, "prompt_tokens_details", None)
    if details is not None:
        cached = getattr(details, "cached_tokens", 0) or 0
    return {
        "parsed": parsed,
        "prompt_tokens": usage.prompt_tokens,
        "cached_tokens": cached,
        "completion_tokens": usage.completion_tokens,
    }


# A single LLM-call task: (persona, creative, run_index, seed).
# user_prompt is built per-call inside _do_one_task so element order can be
# shuffled deterministically per call.
_CallTask = Tuple[Persona, Creative, int, int]


def _seed_for(persona_id: str, creative_id: str, run_idx: int, base_seed: int = 42) -> int:
    """Deterministic per-(persona, creative, run) seed for reproducibility.

    Uses hashlib (not Python's built-in hash) so the seed is stable across processes —
    Python's hash() is randomized per-process via PYTHONHASHSEED unless explicitly set.
    """
    digest = hashlib.md5(f"{persona_id}|{creative_id}".encode("utf-8")).digest()
    pc_int = int.from_bytes(digest[:4], "big")
    return base_seed * 100 + run_idx * 13 + (pc_int % 1000)


def _do_one_task(client: OpenAI, task: _CallTask, model: str) -> EvalResult:
    """Execute one call task with one retry on JSON or API errors (fresh seed on retry)."""
    persona, creative, run_idx, seed = task
    user_prompt, element_order = build_user_prompt(
        persona, creative, shuffle_seed=seed, return_order=True,
    )
    try:
        r = _call_llm(client, user_prompt, model, seed)
    except (APIError, RateLimitError, ValueError) as e:
        time.sleep(2)
        retry_seed = seed + 7919
        user_prompt, element_order = build_user_prompt(
            persona, creative, shuffle_seed=retry_seed, return_order=True,
        )
        r = _call_llm(client, user_prompt, model, retry_seed)
    return EvalResult(
        persona_id=persona.id,
        creative_id=creative.id,
        run_index=run_idx,
        seed=seed,
        parsed=r["parsed"],
        prompt_tokens=r["prompt_tokens"],
        cached_tokens=r["cached_tokens"],
        completion_tokens=r["completion_tokens"],
        element_order=element_order,
    )


def _execute_call_tasks(
    client: OpenAI,
    tasks: List[_CallTask],
    model: str,
    max_workers: int = 10,
    verbose: bool = True,
) -> List[EvalResult]:
    """Run a batch of call tasks in parallel using a ThreadPoolExecutor.

    OpenAI calls are I/O-bound (network wait dominates), so threads — not processes —
    are the right tool. The Python OpenAI client is documented thread-safe.

    A single warmup call runs first (sequentially) so the prompt cache is primed
    before the parallel burst — otherwise concurrent calls all race the cache cold
    and we lose ~50% of cache hits.
    """
    if not tasks:
        return []

    results: List[EvalResult] = []
    failures: List[Tuple[_CallTask, Exception]] = []
    n = len(tasks)

    def _log(idx: int, er: EvalResult):
        cache_pct = 100 * er.cached_tokens / max(er.prompt_tokens, 1)
        al = er.parsed["action_likelihood"]
        print(f"    [{idx:>2}/{n}] {er.persona_id:<32} x {er.creative_id} run {er.run_index+1}: "
              f"al={al}  cache={cache_pct:>3.0f}%")

    if verbose:
        print(f"  warming cache (1 sequential call), then dispatching {n - 1} parallel "
              f"({max_workers} workers)...")

    # Warmup: sequential call to prime the prompt cache.
    try:
        first = _do_one_task(client, tasks[0], model)
        results.append(first)
        if verbose:
            _log(1, first)
    except Exception as e:
        failures.append((tasks[0], e))
        if verbose:
            print(f"    WARNING: warmup failed: {e}")

    if n > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_do_one_task, client, t, model): t for t in tasks[1:]}
            done = 1
            for fut in as_completed(futures):
                t = futures[fut]
                try:
                    er = fut.result()
                    results.append(er)
                    done += 1
                    if verbose:
                        _log(done, er)
                except Exception as e:
                    failures.append((t, e))
                    if verbose:
                        print(f"    WARNING: permanent failure: {t[0].id} x {t[1].id} run {t[2]+1}: {e}")

    if failures and verbose:
        print(f"  WARNING: {len(failures)} of {n} tasks failed permanently (kept partial results)")

    # Stable ordering for deterministic downstream reports.
    results.sort(key=lambda r: (r.persona_id, r.creative_id, r.run_index))
    return results


def evaluate_one(
    client: OpenAI,
    persona: Persona,
    creative: Creative,
    n_runs: int,
    model: str = "gpt-4o-mini",
    base_seed: int = 42,
    verbose: bool = True,
    max_workers: int = 5,
) -> List[EvalResult]:
    """Run N evaluations for one (persona, variant) pair, in parallel."""
    tasks: List[_CallTask] = [
        (persona, creative, i, _seed_for(persona.id, creative.id, i, base_seed))
        for i in range(n_runs)
    ]
    return _execute_call_tasks(client, tasks, model, max_workers=max_workers, verbose=verbose)


def build_eval_tasks(
    pairs: List[Tuple[Persona, Creative]],
    n_runs: int,
    base_seed: int = 42,
) -> List[_CallTask]:
    """Build a flat list of call tasks for arbitrary (persona, creative) pairs.

    Used to merge full-eval and minimal-pair work into a single parallel batch
    so we only pay the cache-warmup cost once. user_prompt is built per-call
    inside _do_one_task so element order can be shuffled with the call seed.
    """
    tasks: List[_CallTask] = []
    for persona, creative in pairs:
        for i in range(n_runs):
            tasks.append((persona, creative, i, _seed_for(persona.id, creative.id, i, base_seed)))
    return tasks


def execute_tasks(
    client: OpenAI,
    tasks: List[_CallTask],
    model: str = "gpt-4o-mini",
    max_workers: int = 20,
    verbose: bool = True,
) -> List[EvalResult]:
    """Public wrapper around the parallel dispatcher."""
    return _execute_call_tasks(client, tasks, model, max_workers=max_workers, verbose=verbose)


def run_full_eval(
    client: OpenAI,
    n_runs: int = 5,
    model: str = "gpt-4o-mini",
    persona_ids: Optional[List[str]] = None,
    creative_ids: Optional[List[str]] = None,
    max_workers: int = 10,
    verbose: bool = True,
) -> List[EvalResult]:
    """All requested personas × creatives × n_runs, executed in parallel."""
    persona_ids = persona_ids or list(PERSONAS.keys())
    creative_ids = creative_ids or list(CREATIVES.keys())
    tasks: List[_CallTask] = []
    for pid in persona_ids:
        for cid in creative_ids:
            persona = PERSONAS[pid]
            creative = CREATIVES[cid]
            for i in range(n_runs):
                tasks.append((persona, creative, i, _seed_for(pid, cid, i)))
    return _execute_call_tasks(client, tasks, model, max_workers=max_workers, verbose=verbose)


# ===== Aggregation =====

def bootstrap_ci(values: List[float], n_resamples: int = 1000, ci: float = 0.95,
                 rng_seed: int = 42) -> Dict[str, float]:
    """Bootstrap mean + percentile CI. Deterministic given rng_seed."""
    if not values:
        return {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n": 0}
    arr = np.asarray(values, dtype=float)
    rng = np.random.default_rng(rng_seed)
    n = len(arr)
    means = np.empty(n_resamples)
    for i in range(n_resamples):
        means[i] = rng.choice(arr, size=n, replace=True).mean()
    lo = float(np.percentile(means, (1 - ci) / 2 * 100))
    hi = float(np.percentile(means, (1 + ci) / 2 * 100))
    return {"mean": float(arr.mean()), "ci_low": lo, "ci_high": hi, "n": n}


def cohens_d(vals_a: List[float], vals_b: List[float]) -> float:
    """Pooled-SD Cohen's d. Interpretation: 0.2=small, 0.5=medium, 0.8=large."""
    n_a, n_b = len(vals_a), len(vals_b)
    if n_a < 2 or n_b < 2:
        return float("nan")
    var_a = float(np.var(vals_a, ddof=1))
    var_b = float(np.var(vals_b, ddof=1))
    pooled_sd = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    if pooled_sd == 0:
        return float("inf") if np.mean(vals_b) != np.mean(vals_a) else 0.0
    return float((np.mean(vals_b) - np.mean(vals_a)) / pooled_sd)


def per_persona_scores(results: List[EvalResult]) -> Dict[str, Dict[str, Dict[str, float]]]:
    """Returns {persona_id: {creative_id: {mean, ci_low, ci_high, n}}} for action_likelihood."""
    out: Dict[str, Dict[str, Dict[str, float]]] = {}
    for r in results:
        out.setdefault(r.persona_id, {}).setdefault(r.creative_id, {"_vals": []})["_vals"].append(
            r.parsed["action_likelihood"]
        )
    final: Dict[str, Dict[str, Dict[str, float]]] = {}
    for pid, by_cid in out.items():
        final[pid] = {cid: bootstrap_ci(d["_vals"]) for cid, d in by_cid.items()}
    return final


def portfolio_score(
    results: List[EvalResult],
    n_resamples: int = 1000,
) -> Dict[str, Dict[str, Any]]:
    """Weighted action_likelihood per variant across the persona portfolio.

    Bootstrap design: at each iteration, for each portfolio persona, resample its
    own per-call action_likelihoods with replacement, take that persona's resampled
    mean, then take the portfolio-weighted mean across personas. This propagates
    intra-persona variance — each bootstrap sample feels both the LLM noise within
    a persona AND the population-weight structure.

    Only personas in PORTFOLIO_WEIGHTS contribute; synthetic minimal-pair personas
    are diagnostic and excluded.

    Returns dict keyed by creative_id with mean, ci_low, ci_high, and the raw
    bootstrap samples (used by is_close_call for a paired difference test).
    """
    # Group raw action_likelihoods by (creative_id, persona_id).
    grouped: Dict[str, Dict[str, List[float]]] = {}
    for r in results:
        if r.persona_id not in PORTFOLIO_WEIGHTS:
            continue
        grouped.setdefault(r.creative_id, {}).setdefault(r.persona_id, []).append(
            float(r.parsed["action_likelihood"])
        )

    out: Dict[str, Dict[str, Any]] = {}
    for cid, by_persona in grouped.items():
        pids = sorted(by_persona.keys())
        weights = np.asarray([PORTFOLIO_WEIGHTS[pid] for pid in pids], dtype=float)
        weights = weights / weights.sum()
        # Point estimate: weighted mean of per-persona means
        persona_means = np.asarray([np.mean(by_persona[pid]) for pid in pids])
        weighted_mean = float((weights * persona_means).sum())
        # Bootstrap with intra-persona resampling — deterministic seed per creative
        cid_seed = int.from_bytes(hashlib.md5(cid.encode("utf-8")).digest()[:4], "big") % 10_000
        rng = np.random.default_rng(42 + cid_seed)
        per_persona_arrays = [np.asarray(by_persona[pid]) for pid in pids]
        boot = np.empty(n_resamples)
        for i in range(n_resamples):
            resampled_means = np.array([
                rng.choice(arr, size=len(arr), replace=True).mean()
                for arr in per_persona_arrays
            ])
            boot[i] = (weights * resampled_means).sum()
        out[cid] = {
            "mean": weighted_mean,
            "ci_low": float(np.percentile(boot, 2.5)),
            "ci_high": float(np.percentile(boot, 97.5)),
            "_bootstrap_samples": boot,
        }
    return out


def is_close_call(
    score_a: Dict[str, Any],
    score_b: Dict[str, Any],
    ci: float = 0.95,
    mde: float = 0.5,
) -> bool:
    """Paired bootstrap test with minimum detectable effect (Kohavi et al. 2020).

    True if we cannot conclude |mean_B - mean_A| >= mde with confidence `ci`.
    mde=0.5 means gaps smaller than 0.5 points on the 1-10 scale are not
    operationally meaningful for creative selection.

    Uses the per-creative bootstrap sample arrays produced by portfolio_score.
    Falls back to CI overlap if samples aren't present (e.g., manually constructed
    score dicts).
    """
    a_samples = score_a.get("_bootstrap_samples")
    b_samples = score_b.get("_bootstrap_samples")
    if a_samples is not None and b_samples is not None:
        diffs = np.asarray(b_samples) - np.asarray(a_samples)
        lo = float(np.percentile(diffs, (1 - ci) / 2 * 100))
        hi = float(np.percentile(diffs, (1 + ci) / 2 * 100))
        return lo < mde and hi > -mde
    # Fallback: marginal CI overlap (loose, but better than nothing)
    return not (score_a["ci_high"] < score_b["ci_low"] or score_b["ci_high"] < score_a["ci_low"])


def compute_element_attribution(results: List[EvalResult], creative: Creative) -> Dict[str, Dict[str, Any]]:
    """Per element_id: trigger/skeptic counts, attribution score, CI on per-call signed intensity,
    plus top reasoning quotes for qualitative context.

    Defensive against schema drift: the model occasionally emits a non-dict entry
    (a bare string, a list, etc.) inside element_reactions. Malformed entries and
    hallucinated element_ids are counted ONCE per occurrence (scanned in a single
    pre-pass), not once per element iteration.
    """
    out: Dict[str, Dict[str, Any]] = {}
    creative_results = [r for r in results if r.creative_id == creative.id]
    valid_ids = {el.id for el in creative.elements}

    # Pre-pass: scan every element_reactions entry once. Build a per-element index.
    # No silent skipping — malformed entries raise immediately.
    reactions_by_eid: Dict[str, List[Dict[str, Any]]] = {el.id: [] for el in creative.elements}
    hallucinated: set[str] = set()
    for r in creative_results:
        for i, er in enumerate(r.parsed["element_reactions"]):
            if not isinstance(er, dict):
                raise ValueError(
                    f"element_reactions[{i}] in {r.persona_id} x {r.creative_id} "
                    f"run {r.run_index} is {type(er).__name__}, expected dict: {er!r}"
                )
            eid = er["element_id"]
            if eid in valid_ids:
                reactions_by_eid[eid].append(er)
            else:
                hallucinated.add(eid)

    for el in creative.elements:
        trigger = skeptic = non = 0
        intensities: List[float] = []
        signed_per_call: List[float] = []
        direction_per_call: List[float] = []
        trigger_quotes: List[str] = []
        skeptic_quotes: List[str] = []
        non_quotes: List[str] = []
        for er in reactions_by_eid[el.id]:
            reaction = er["reaction"].upper()
            intensity = int(er["intensity"])
            reasoning = str(er["reasoning"]).strip()
            intensities.append(intensity)
            if reaction == "TRIGGER":
                trigger += 1
                signed_per_call.append(float(intensity))
                direction_per_call.append(1.0)
                if reasoning:
                    trigger_quotes.append(reasoning)
            elif reaction == "SKEPTICISM_TRIGGER":
                skeptic += 1
                signed_per_call.append(-float(intensity))
                direction_per_call.append(-1.0)
                if reasoning:
                    skeptic_quotes.append(reasoning)
            else:
                non += 1
                signed_per_call.append(0.0)
                direction_per_call.append(0.0)
                if reasoning:
                    non_quotes.append(reasoning)
        total = trigger + skeptic + non
        attr_score = (trigger - skeptic) / max(total, 1) * 100
        ci = bootstrap_ci(signed_per_call) if signed_per_call else {"mean": 0, "ci_low": 0, "ci_high": 0, "n": 0}
        attr_seed = int.from_bytes(hashlib.md5(el.id.encode("utf-8")).digest()[:4], "big") % 10_000
        attr_ci_raw = bootstrap_ci(direction_per_call, rng_seed=attr_seed) if direction_per_call else {"mean": 0, "ci_low": 0, "ci_high": 0, "n": 0}
        attr_ci = {
            "mean": attr_ci_raw["mean"] * 100,
            "ci_low": attr_ci_raw["ci_low"] * 100,
            "ci_high": attr_ci_raw["ci_high"] * 100,
            "n": attr_ci_raw["n"],
        }
        out[el.id] = {
            "element_type": el.element_type,
            "trigger_count": trigger,
            "skeptic_count": skeptic,
            "non_trigger_count": non,
            "trigger_pct": 100 * trigger / max(total, 1),
            "skeptic_pct": 100 * skeptic / max(total, 1),
            "attribution_score": attr_score,
            "attribution_ci": attr_ci,
            "intensity_mean": float(np.mean(intensities)) if intensities else 0.0,
            "signed_intensity_ci": ci,
            "trigger_quotes": trigger_quotes,
            "skeptic_quotes": skeptic_quotes,
            "non_trigger_quotes": non_quotes,
        }
    if hallucinated:
        out["_hallucinated_element_ids"] = sorted(hallucinated)
    return out


def persona_differentiation(
    results: List[EvalResult],
    creative: Creative,
    persona_ids: Optional[List[str]] = None,
    collapse_threshold: float = 0.5,
) -> Dict[str, Dict[str, Any]]:
    """Between-persona variance on signed intensity per element.

    Low variance = personas are reacting identically = potential faithfulness
    failure (Argyle et al. 2023, "Out of One, Many"). Elements with variance
    below `collapse_threshold` are flagged as potentially collapsed.

    The right threshold depends on persona count and intensity scale. Default
    0.5 is calibrated for 3-5 personas on a ±5 signed intensity scale.

    Returns {element_id: {variance, per_persona_means, collapsed}}.
    """
    pids = persona_ids or list(PORTFOLIO_WEIGHTS.keys())
    creative_results = [r for r in results if r.creative_id == creative.id]
    valid_ids = {el.id for el in creative.elements}

    scores: Dict[str, Dict[str, Any]] = {}
    for el in creative.elements:
        per_persona_means: Dict[str, float] = {}
        for pid in pids:
            signed: List[float] = []
            for r in creative_results:
                if r.persona_id != pid:
                    continue
                for er in r.parsed["element_reactions"]:
                    if not isinstance(er, dict) or er.get("element_id") != el.id:
                        continue
                    reaction = er["reaction"].upper()
                    intensity = float(er["intensity"])
                    if reaction == "TRIGGER":
                        signed.append(intensity)
                    elif reaction == "SKEPTICISM_TRIGGER":
                        signed.append(-intensity)
                    else:
                        signed.append(0.0)
            if signed:
                per_persona_means[pid] = float(np.mean(signed))

        means_list = list(per_persona_means.values())
        variance = float(np.var(means_list)) if len(means_list) >= 2 else 0.0
        scores[el.id] = {
            "element_type": el.element_type,
            "variance": variance,
            "per_persona_means": per_persona_means,
            "collapsed": variance < collapse_threshold and len(means_list) >= 2,
        }
    return scores


def segment_recommendations(
    results: List[EvalResult],
    attribution: Dict[str, Dict[str, Any]],
    creative: Creative,
    threshold: float = -20.0,
) -> List[Dict[str, Any]]:
    """Per-segment targeted edits for weak elements.

    For each element with attribution_score below `threshold`, collects
    which persona segments drive the skepticism and what each would change.
    """
    creative_results = [r for r in results if r.creative_id == creative.id]
    recs: List[Dict[str, Any]] = []

    for el in creative.elements:
        attr = attribution.get(el.id)
        if attr is None or attr["attribution_score"] >= threshold:
            continue

        by_segment: Dict[str, Dict[str, Any]] = {}
        for pid in PORTFOLIO_WEIGHTS:
            persona_runs = [r for r in creative_results if r.persona_id == pid]
            if not persona_runs:
                continue
            signed: List[float] = []
            for r in persona_runs:
                for er in r.parsed["element_reactions"]:
                    if not isinstance(er, dict) or er.get("element_id") != el.id:
                        continue
                    reaction = er["reaction"].upper()
                    intensity = float(er["intensity"])
                    if reaction == "TRIGGER":
                        signed.append(intensity)
                    elif reaction == "SKEPTICISM_TRIGGER":
                        signed.append(-intensity)
                    else:
                        signed.append(0.0)
            edits = [r.parsed["what_would_change"].strip() for r in persona_runs
                     if r.parsed["what_would_change"].strip()]
            if signed:
                by_segment[pid] = {
                    "mean_signed_intensity": float(np.mean(signed)),
                    "suggested_edits": edits,
                }

        recs.append({
            "element_id": el.id,
            "element_type": el.element_type,
            "overall_score": attr["attribution_score"],
            "attribution_ci": attr["attribution_ci"],
            "fix_by_segment": by_segment,
        })

    return recs


def compute_cost(results: List[EvalResult], model: str = "gpt-4o-mini") -> Dict[str, float]:
    if model not in PRICING:
        raise ValueError(
            f"No pricing entry for model '{model}'. Add it to PRICING in pipeline.py "
            f"(known: {sorted(PRICING.keys())})."
        )
    p = PRICING[model]
    total_cost = 0.0
    total_prompt = total_cached = total_completion = 0
    for r in results:
        fresh = max(r.prompt_tokens - r.cached_tokens, 0)
        total_cost += (fresh * p["input"]
                       + r.cached_tokens * p["cached"]
                       + r.completion_tokens * p["output"])
        total_prompt += r.prompt_tokens
        total_cached += r.cached_tokens
        total_completion += r.completion_tokens
    cache_hit_rate = (total_cached / total_prompt * 100) if total_prompt else 0.0
    return {
        "total_cost_usd": total_cost,
        "calls": len(results),
        "prompt_tokens": total_prompt,
        "cached_tokens": total_cached,
        "completion_tokens": total_completion,
        "cache_hit_rate_pct": cache_hit_rate,
    }


def check_position_bias(
    results: List[EvalResult],
    creative: Creative,
) -> Dict[str, Dict[str, float]]:
    """Test for residual position bias after element-order shuffling.

    For each element, computes Spearman correlation between its position in the
    shuffled prompt and its signed intensity. Significant correlation = the
    shuffle mitigation is insufficient for that element (Zheng et al. 2023).

    Returns {element_id: {spearman_rho, p_value}} for elements with >= 5
    observations. Falls back gracefully if scipy is not installed.
    """
    try:
        from scipy.stats import spearmanr
    except ImportError:
        return {}

    bias_report: Dict[str, Dict[str, float]] = {}
    creative_results = [r for r in results if r.creative_id == creative.id]

    for el in creative.elements:
        positions: List[float] = []
        intensities: List[float] = []
        for r in creative_results:
            if not r.element_order or el.id not in r.element_order:
                continue
            pos = r.element_order.index(el.id)
            for er in r.parsed["element_reactions"]:
                if not isinstance(er, dict) or er.get("element_id") != el.id:
                    continue
                reaction = er["reaction"].upper()
                intensity = float(er["intensity"])
                signed = intensity if reaction == "TRIGGER" else (
                    -intensity if reaction == "SKEPTICISM_TRIGGER" else 0.0
                )
                positions.append(float(pos))
                intensities.append(signed)
        if len(positions) >= 5:
            rho, pval = spearmanr(positions, intensities)
            bias_report[el.id] = {
                "spearman_rho": float(rho),
                "p_value": float(pval),
            }
    return bias_report


def llm_self_consistency(
    results: List[EvalResult],
    creative_id: str,
    persona_ids: Optional[List[str]] = None,
) -> Dict[str, float]:
    """Krippendorff's alpha on element intensities across runs per cell.

    Measures LLM self-consistency (not true inter-rater reliability — runs are
    repeated samples from the same stochastic process, not independent human
    coders). Use as a diagnostic flag, not a hard gate.

    Interpretation (standard Krippendorff thresholds, applied conservatively):
      > 0.80 — consistent
      0.67–0.80 — tentative
      < 0.67 — flag as noisy

    Falls back gracefully if the `krippendorff` package is not installed.
    """
    try:
        from krippendorff import alpha as kripp_alpha
    except ImportError:
        return {}

    pids = persona_ids or list(PORTFOLIO_WEIGHTS.keys())
    cell_alphas: Dict[str, float] = {}

    for pid in pids:
        runs = [r for r in results
                if r.persona_id == pid and r.creative_id == creative_id]
        if len(runs) < 3:
            continue
        intensities_by_run = []
        for r in runs:
            row = [float(er["intensity"]) for er in r.parsed["element_reactions"]
                   if isinstance(er, dict)]
            intensities_by_run.append(row)
        max_len = max(len(row) for row in intensities_by_run)
        min_len = min(len(row) for row in intensities_by_run)
        if min_len == 0:
            continue
        if min_len < max_len:
            import warnings
            warnings.warn(
                f"llm_self_consistency: persona={pid} creative={creative_id} — "
                f"trimming element_reactions from {max_len} to {min_len} across "
                f"{len(runs)} runs (some runs returned fewer elements)",
                stacklevel=2,
            )
        trimmed = [row[:min_len] for row in intensities_by_run]
        try:
            a = kripp_alpha(
                reliability_data=trimmed,
                level_of_measurement="ordinal",
            )
            cell_alphas[pid] = float(a)
        except Exception:
            continue

    return cell_alphas


def serialize_results(results: List[EvalResult]) -> List[Dict[str, Any]]:
    """Convert to plain dicts for JSON dumping."""
    return [asdict(r) for r in results]


# ===== Calibration (stub — activated when real engagement data is available) =====

@dataclass
class CalibrationRecord:
    """One row of predicted-vs-actual for calibration scoring.

    Populated when real engagement data becomes available. Enables Brier
    score + rank correlation vs. predicted portfolio scores.
    """
    creative_id: str
    predicted_score: float
    actual_ctr: Optional[float] = None
    actual_conversion_rate: Optional[float] = None
    actual_winner: Optional[str] = None


def brier_score(predictions: List[float], outcomes: List[float]) -> float:
    """Brier score for probabilistic calibration (Gneiting & Raftery 2007).

    Lower = better calibrated. Perfect = 0.0. Random = 0.25.
    Proper scoring rule — cannot be gamed by hedging.
    """
    if not predictions or len(predictions) != len(outcomes):
        return float("nan")
    return float(np.mean([(p - o) ** 2 for p, o in zip(predictions, outcomes)]))


def rank_correlation(predicted_ranks: List[str], actual_ranks: List[str]) -> float:
    """Spearman rho between predicted and actual variant ranking.

    Falls back gracefully if scipy is not installed.
    """
    try:
        from scipy.stats import spearmanr
    except ImportError:
        return float("nan")
    all_ids = sorted(set(predicted_ranks + actual_ranks))
    p_nums = [all_ids.index(x) for x in predicted_ranks]
    a_nums = [all_ids.index(x) for x in actual_ranks]
    rho, _ = spearmanr(p_nums, a_nums)
    return float(rho)
