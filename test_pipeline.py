"""Tests for the core statistical and validation functions in pipeline.py."""

import pytest
import numpy as np

from pipeline import (
    bootstrap_ci,
    is_close_call,
    _validate_parsed,
    _seed_for,
    compute_element_attribution,
    cohens_d,
    persona_differentiation,
    segment_recommendations,
    check_position_bias,
    brier_score,
    EvalResult,
)
from creatives import CREATIVE_B


# ── bootstrap_ci ──

class TestBootstrapCI:
    def test_deterministic(self):
        vals = [3.0, 5.0, 7.0, 4.0, 6.0]
        a = bootstrap_ci(vals, rng_seed=99)
        b = bootstrap_ci(vals, rng_seed=99)
        assert a == b

    def test_different_seeds_differ(self):
        vals = list(range(1, 51))  # 50 values — enough variance for seed to matter
        a = bootstrap_ci(vals, rng_seed=1)
        b = bootstrap_ci(vals, rng_seed=2)
        assert a["ci_low"] != b["ci_low"] or a["ci_high"] != b["ci_high"]

    def test_mean_correct(self):
        vals = [2.0, 4.0, 6.0, 8.0, 10.0]
        result = bootstrap_ci(vals)
        assert result["mean"] == pytest.approx(6.0)
        assert result["n"] == 5

    def test_ci_contains_mean(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        result = bootstrap_ci(vals)
        assert result["ci_low"] <= result["mean"] <= result["ci_high"]

    def test_constant_values_zero_width_ci(self):
        vals = [5.0, 5.0, 5.0, 5.0, 5.0]
        result = bootstrap_ci(vals)
        assert result["mean"] == 5.0
        assert result["ci_low"] == 5.0
        assert result["ci_high"] == 5.0

    def test_empty_list(self):
        result = bootstrap_ci([])
        assert result == {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n": 0}

    def test_single_value(self):
        result = bootstrap_ci([7.0])
        assert result["mean"] == 7.0
        assert result["n"] == 1

    def test_ci_width_shrinks_with_more_data(self):
        rng = np.random.default_rng(42)
        small = bootstrap_ci(rng.normal(5, 1, size=10).tolist())
        large = bootstrap_ci(rng.normal(5, 1, size=200).tolist())
        small_width = small["ci_high"] - small["ci_low"]
        large_width = large["ci_high"] - large["ci_low"]
        assert large_width < small_width


# ── is_close_call ──

class TestIsCloseCall:
    def test_identical_distributions_is_close(self):
        samples = np.random.default_rng(42).normal(5, 1, size=1000)
        score = {"mean": 5.0, "ci_low": 4.5, "ci_high": 5.5, "_bootstrap_samples": samples}
        assert is_close_call(score, score) is True

    def test_well_separated_not_close(self):
        rng = np.random.default_rng(42)
        a = {"mean": 3.0, "ci_low": 2.5, "ci_high": 3.5,
             "_bootstrap_samples": rng.normal(3, 0.2, size=1000)}
        b = {"mean": 7.0, "ci_low": 6.5, "ci_high": 7.5,
             "_bootstrap_samples": rng.normal(7, 0.2, size=1000)}
        assert is_close_call(a, b) is False

    def test_overlapping_but_shifted(self):
        rng = np.random.default_rng(42)
        a = {"mean": 5.0, "ci_low": 4.0, "ci_high": 6.0,
             "_bootstrap_samples": rng.normal(5, 0.5, size=1000)}
        b = {"mean": 5.3, "ci_low": 4.3, "ci_high": 6.3,
             "_bootstrap_samples": rng.normal(5.3, 0.5, size=1000)}
        result = is_close_call(a, b)
        assert isinstance(result, bool)

    def test_fallback_without_samples(self):
        a = {"mean": 5.0, "ci_low": 4.0, "ci_high": 6.0}
        b = {"mean": 5.5, "ci_low": 4.5, "ci_high": 6.5}
        assert is_close_call(a, b) is True

    def test_fallback_no_overlap(self):
        a = {"mean": 3.0, "ci_low": 2.0, "ci_high": 4.0}
        b = {"mean": 7.0, "ci_low": 6.0, "ci_high": 8.0}
        assert is_close_call(a, b) is False


# ── _validate_parsed ──

def _valid_parsed():
    """Return a valid parsed dict that passes validation."""
    return {
        "first_impression": "This looks interesting.",
        "element_reactions": [
            {
                "element_id": "B_E1_hook",
                "reaction": "TRIGGER",
                "intensity": 4,
                "reasoning": "The 47-minute detail is specific and relatable.",
            },
        ],
        "missing_information": ["pricing details"],
        "overall_reaction": "resonates",
        "action_likelihood": 7,
        "reaction_drivers": [{"element_or_claim": "hook", "why": "relatable"}],
        "what_would_change": "Add named customers.",
        "chain_of_thought": "The hook grabbed me because it mirrors my experience.",
    }


class TestValidateParsed:
    def test_valid_passes(self):
        _validate_parsed(_valid_parsed())

    def test_missing_field(self):
        d = _valid_parsed()
        del d["action_likelihood"]
        with pytest.raises(ValueError, match="Missing required field"):
            _validate_parsed(d)

    def test_wrong_type_action_likelihood(self):
        d = _valid_parsed()
        d["action_likelihood"] = "seven"
        with pytest.raises(ValueError, match="must be"):
            _validate_parsed(d)

    def test_action_likelihood_too_low(self):
        d = _valid_parsed()
        d["action_likelihood"] = 0
        with pytest.raises(ValueError, match="outside valid range"):
            _validate_parsed(d)

    def test_action_likelihood_too_high(self):
        d = _valid_parsed()
        d["action_likelihood"] = 11
        with pytest.raises(ValueError, match="outside valid range"):
            _validate_parsed(d)

    def test_action_likelihood_boundary_values(self):
        for val in (1, 10, 5.5):
            d = _valid_parsed()
            d["action_likelihood"] = val
            _validate_parsed(d)

    def test_element_reaction_not_dict(self):
        d = _valid_parsed()
        d["element_reactions"] = ["not a dict"]
        with pytest.raises(ValueError, match="expected dict"):
            _validate_parsed(d)

    def test_element_reaction_missing_field(self):
        d = _valid_parsed()
        d["element_reactions"] = [{"element_id": "X", "reaction": "TRIGGER"}]
        with pytest.raises(ValueError, match="missing 'intensity'"):
            _validate_parsed(d)

    def test_invalid_reaction_type(self):
        d = _valid_parsed()
        d["element_reactions"][0]["reaction"] = "LOVE_IT"
        with pytest.raises(ValueError, match="not in"):
            _validate_parsed(d)

    def test_reaction_case_insensitive(self):
        d = _valid_parsed()
        d["element_reactions"][0]["reaction"] = "trigger"
        _validate_parsed(d)

    def test_intensity_not_numeric(self):
        d = _valid_parsed()
        d["element_reactions"][0]["intensity"] = "high"
        with pytest.raises(ValueError, match="must be numeric"):
            _validate_parsed(d)

    def test_first_impression_wrong_type(self):
        d = _valid_parsed()
        d["first_impression"] = 42
        with pytest.raises(ValueError, match="must be"):
            _validate_parsed(d)


# ── _seed_for ──

class TestSeedFor:
    def test_deterministic(self):
        assert _seed_for("alex", "B", 0) == _seed_for("alex", "B", 0)

    def test_different_runs_differ(self):
        assert _seed_for("alex", "B", 0) != _seed_for("alex", "B", 1)

    def test_different_personas_differ(self):
        assert _seed_for("alex", "B", 0) != _seed_for("jordan", "B", 0)

    def test_different_creatives_differ(self):
        assert _seed_for("alex", "A", 0) != _seed_for("alex", "B", 0)

    def test_cross_process_stable(self):
        expected = _seed_for("alex_vp_eng", "B", 3, base_seed=42)
        assert isinstance(expected, int)
        assert _seed_for("alex_vp_eng", "B", 3, base_seed=42) == expected


# ── compute_element_attribution ──

def _make_eval_result(persona_id, creative_id, run_index, reactions):
    return EvalResult(
        persona_id=persona_id,
        creative_id=creative_id,
        run_index=run_index,
        seed=42,
        parsed={
            "first_impression": "test",
            "element_reactions": reactions,
            "missing_information": [],
            "overall_reaction": "resonates",
            "action_likelihood": 5,
            "reaction_drivers": [],
            "what_would_change": "nothing",
            "chain_of_thought": "test",
        },
        prompt_tokens=100,
        cached_tokens=80,
        completion_tokens=200,
    )


class TestComputeElementAttribution:
    def test_all_triggers_score_positive(self):
        reactions = [
            {"element_id": el.id, "reaction": "TRIGGER", "intensity": 4, "reasoning": "good"}
            for el in CREATIVE_B.elements
        ]
        results = [_make_eval_result("p1", "B", 0, reactions)]
        attr = compute_element_attribution(results, CREATIVE_B)
        for el in CREATIVE_B.elements:
            assert attr[el.id]["attribution_score"] > 0
            assert attr[el.id]["trigger_count"] == 1
            assert attr[el.id]["skeptic_count"] == 0

    def test_all_skeptic_score_negative(self):
        reactions = [
            {"element_id": el.id, "reaction": "SKEPTICISM_TRIGGER", "intensity": 3, "reasoning": "bad"}
            for el in CREATIVE_B.elements
        ]
        results = [_make_eval_result("p1", "B", 0, reactions)]
        attr = compute_element_attribution(results, CREATIVE_B)
        for el in CREATIVE_B.elements:
            assert attr[el.id]["attribution_score"] < 0

    def test_mixed_reactions(self):
        reactions = [
            {"element_id": el.id, "reaction": "TRIGGER", "intensity": 4, "reasoning": "good"}
            for el in CREATIVE_B.elements
        ]
        results = [
            _make_eval_result("p1", "B", 0, reactions),
            _make_eval_result("p1", "B", 1, [
                {"element_id": el.id, "reaction": "SKEPTICISM_TRIGGER", "intensity": 4, "reasoning": "bad"}
                for el in CREATIVE_B.elements
            ]),
        ]
        attr = compute_element_attribution(results, CREATIVE_B)
        for el in CREATIVE_B.elements:
            assert attr[el.id]["attribution_score"] == 0.0

    def test_hallucinated_ids_tracked(self):
        reactions = [
            {"element_id": el.id, "reaction": "TRIGGER", "intensity": 3, "reasoning": "ok"}
            for el in CREATIVE_B.elements
        ] + [
            {"element_id": "FAKE_ID", "reaction": "TRIGGER", "intensity": 5, "reasoning": "hallucinated"}
        ]
        results = [_make_eval_result("p1", "B", 0, reactions)]
        attr = compute_element_attribution(results, CREATIVE_B)
        assert "FAKE_ID" not in attr
        assert "_hallucinated_element_ids" in attr
        assert "FAKE_ID" in attr["_hallucinated_element_ids"]

    def test_malformed_reaction_raises(self):
        reactions = [
            {"element_id": CREATIVE_B.elements[0].id, "reaction": "TRIGGER", "intensity": 3, "reasoning": "ok"},
            "not a dict",
        ]
        results = [_make_eval_result("p1", "B", 0, reactions)]
        with pytest.raises(ValueError, match="expected dict"):
            compute_element_attribution(results, CREATIVE_B)

    def test_empty_results(self):
        attr = compute_element_attribution([], CREATIVE_B)
        for el in CREATIVE_B.elements:
            assert attr[el.id]["trigger_count"] == 0
            assert attr[el.id]["attribution_score"] == 0.0

    def test_attribution_ci_present(self):
        reactions = [
            {"element_id": el.id, "reaction": "TRIGGER", "intensity": 4, "reasoning": "good"}
            for el in CREATIVE_B.elements
        ]
        results = [_make_eval_result("p1", "B", 0, reactions)]
        attr = compute_element_attribution(results, CREATIVE_B)
        for el in CREATIVE_B.elements:
            assert "attribution_ci" in attr[el.id]
            ci = attr[el.id]["attribution_ci"]
            assert "mean" in ci and "ci_low" in ci and "ci_high" in ci
            assert ci["ci_low"] <= ci["mean"] <= ci["ci_high"]


# ── cohens_d ──

class TestCohensD:
    def test_identical_groups(self):
        vals = [5.0, 5.0, 5.0, 5.0, 5.0]
        assert cohens_d(vals, vals) == 0.0

    def test_well_separated(self):
        a = [1.0, 1.0, 1.0, 1.0, 1.0]
        b = [10.0, 10.0, 10.0, 10.0, 10.0]
        assert cohens_d(a, b) == float("inf")

    def test_small_effect(self):
        rng = np.random.default_rng(42)
        a = rng.normal(5.0, 1.0, 100).tolist()
        b = rng.normal(5.2, 1.0, 100).tolist()
        d = cohens_d(a, b)
        assert abs(d) < 0.5

    def test_large_effect(self):
        rng = np.random.default_rng(42)
        a = rng.normal(3.0, 1.0, 100).tolist()
        b = rng.normal(6.0, 1.0, 100).tolist()
        d = cohens_d(a, b)
        assert d > 0.8

    def test_direction(self):
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        assert cohens_d(a, b) > 0
        assert cohens_d(b, a) < 0

    def test_too_few_samples(self):
        import math
        assert math.isnan(cohens_d([1.0], [2.0, 3.0]))
        assert math.isnan(cohens_d([1.0, 2.0], [3.0]))


# ── is_close_call with MDE ──

class TestIsCloseCallMDE:
    def test_small_gap_is_close_with_mde(self):
        rng = np.random.default_rng(42)
        a = {"mean": 5.0, "ci_low": 4.5, "ci_high": 5.5,
             "_bootstrap_samples": rng.normal(5.0, 0.3, size=1000)}
        b = {"mean": 5.3, "ci_low": 4.8, "ci_high": 5.8,
             "_bootstrap_samples": rng.normal(5.3, 0.3, size=1000)}
        assert is_close_call(a, b, mde=0.5) is True

    def test_large_gap_not_close_with_mde(self):
        rng = np.random.default_rng(42)
        a = {"mean": 3.0, "ci_low": 2.5, "ci_high": 3.5,
             "_bootstrap_samples": rng.normal(3.0, 0.2, size=1000)}
        b = {"mean": 7.0, "ci_low": 6.5, "ci_high": 7.5,
             "_bootstrap_samples": rng.normal(7.0, 0.2, size=1000)}
        assert is_close_call(a, b, mde=0.5) is False


# ── persona_differentiation ──

class TestPersonaDifferentiation:
    def test_collapsed_when_identical(self):
        reactions = [
            {"element_id": el.id, "reaction": "TRIGGER", "intensity": 4, "reasoning": "good"}
            for el in CREATIVE_B.elements
        ]
        results = [
            _make_eval_result("p1", "B", 0, reactions),
            _make_eval_result("p2", "B", 0, reactions),
        ]
        diff = persona_differentiation(results, CREATIVE_B, persona_ids=["p1", "p2"])
        for el in CREATIVE_B.elements:
            assert diff[el.id]["collapsed"] is True
            assert diff[el.id]["variance"] == 0.0

    def test_not_collapsed_when_divergent(self):
        trigger_reactions = [
            {"element_id": el.id, "reaction": "TRIGGER", "intensity": 5, "reasoning": "good"}
            for el in CREATIVE_B.elements
        ]
        skeptic_reactions = [
            {"element_id": el.id, "reaction": "SKEPTICISM_TRIGGER", "intensity": 5, "reasoning": "bad"}
            for el in CREATIVE_B.elements
        ]
        results = [
            _make_eval_result("p1", "B", 0, trigger_reactions),
            _make_eval_result("p2", "B", 0, skeptic_reactions),
        ]
        diff = persona_differentiation(results, CREATIVE_B, persona_ids=["p1", "p2"])
        for el in CREATIVE_B.elements:
            assert diff[el.id]["collapsed"] is False
            assert diff[el.id]["variance"] > 0

    def test_single_persona_not_collapsed(self):
        reactions = [
            {"element_id": el.id, "reaction": "TRIGGER", "intensity": 4, "reasoning": "good"}
            for el in CREATIVE_B.elements
        ]
        results = [_make_eval_result("p1", "B", 0, reactions)]
        diff = persona_differentiation(results, CREATIVE_B, persona_ids=["p1"])
        for el in CREATIVE_B.elements:
            assert diff[el.id]["collapsed"] is False


# ── segment_recommendations ──

class TestSegmentRecommendations:
    def test_no_recs_when_all_positive(self):
        reactions = [
            {"element_id": el.id, "reaction": "TRIGGER", "intensity": 4, "reasoning": "good"}
            for el in CREATIVE_B.elements
        ]
        results = [_make_eval_result("alex_vp_eng", "B", 0, reactions)]
        attr = compute_element_attribution(results, CREATIVE_B)
        recs = segment_recommendations(results, attr, CREATIVE_B)
        assert recs == []

    def test_recs_for_negative_element(self):
        reactions = [
            {"element_id": el.id, "reaction": "SKEPTICISM_TRIGGER", "intensity": 4, "reasoning": "bad"}
            for el in CREATIVE_B.elements
        ]
        results = [_make_eval_result("alex_vp_eng", "B", 0, reactions)]
        attr = compute_element_attribution(results, CREATIVE_B)
        recs = segment_recommendations(results, attr, CREATIVE_B)
        assert len(recs) == len(CREATIVE_B.elements)
        for rec in recs:
            assert rec["overall_score"] < 0
            assert "alex_vp_eng" in rec["fix_by_segment"]


# ── check_position_bias ──

class TestCheckPositionBias:
    def test_returns_empty_without_order(self):
        reactions = [
            {"element_id": el.id, "reaction": "TRIGGER", "intensity": 4, "reasoning": "good"}
            for el in CREATIVE_B.elements
        ]
        results = [_make_eval_result("p1", "B", i, reactions) for i in range(5)]
        bias = check_position_bias(results, CREATIVE_B)
        assert bias == {}

    def test_returns_results_with_order(self):
        element_ids = [el.id for el in CREATIVE_B.elements]
        results = []
        for i in range(10):
            reactions = [
                {"element_id": el.id, "reaction": "TRIGGER", "intensity": 3, "reasoning": "ok"}
                for el in CREATIVE_B.elements
            ]
            r = _make_eval_result("p1", "B", i, reactions)
            r.element_order = element_ids[:]
            results.append(r)
        bias = check_position_bias(results, CREATIVE_B)
        assert len(bias) > 0
        for eid, b in bias.items():
            assert "spearman_rho" in b
            assert "p_value" in b


# ── brier_score ──

class TestBrierScore:
    def test_perfect(self):
        assert brier_score([1.0, 0.0, 1.0], [1.0, 0.0, 1.0]) == 0.0

    def test_worst(self):
        assert brier_score([1.0, 0.0], [0.0, 1.0]) == 1.0

    def test_random_baseline(self):
        score = brier_score([0.5, 0.5, 0.5, 0.5], [1.0, 0.0, 1.0, 0.0])
        assert score == pytest.approx(0.25)

    def test_empty(self):
        import math
        assert math.isnan(brier_score([], []))

    def test_mismatched_lengths(self):
        import math
        assert math.isnan(brier_score([0.5], [1.0, 0.0]))
