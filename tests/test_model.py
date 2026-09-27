"""Unit tests. Run with:  python -m pytest -q   (or)   python tests/test_model.py"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuzzy_model import (INPUT_VARIABLES, OUTPUT_VARIABLE, RULES, category_thresholds,  # noqa: E402
                         evaluate_rules, fuzzify, infer, trapmf)
from recommendation import forward_chain, recommend  # noqa: E402


def test_trapmf_shapes():
    assert trapmf(5, 0, 0, 6, 7) == 1.0          # left shoulder plateau
    assert abs(trapmf(6.5, 0, 0, 6, 7) - 0.5) < 1e-12
    assert trapmf(7, 0, 0, 6, 7) == 0.0
    assert trapmf(3, 1, 3, 3, 5) == 1.0          # triangle peak
    assert abs(trapmf(2, 1, 3, 3, 5) - 0.5) < 1e-12


def test_inputs_are_ruspini_partitions():
    """At every value the degrees of one input sum to 1."""
    for var, spec in INPUT_VARIABLES.items():
        lo, hi = spec["range"]
        for x in np.linspace(lo, hi, 401):
            s = sum(trapmf(x, *p) for p in spec["terms"].values())
            assert abs(s - 1.0) < 1e-9, (var, x, s)


def test_rule_base_is_complete():
    """At least one rule fires for every input combination on a grid."""
    grids = [np.linspace(*INPUT_VARIABLES[v]["range"], 13) for v in INPUT_VARIABLES]
    names = list(INPUT_VARIABLES)
    for s in grids[0]:
        for a in grids[1]:
            for c in grids[2]:
                for m in grids[3]:
                    mem = fuzzify(dict(zip(names, (s, a, c, m))))
                    assert max(r["strength"] for r in evaluate_rules(mem)) > 0


def _analytic_centroid(levels):
    """Independent check: integrate the aggregated set with scipy.quad."""
    from scipy.integrate import quad

    def mu(y):
        return max([min(levels[t], trapmf(y, *OUTPUT_VARIABLE["terms"][t])) for t in levels] + [0.0])

    brk = sorted({p for t in OUTPUT_VARIABLE["terms"].values() for p in t})
    num = quad(lambda y: y * mu(y), 0, 100, points=brk, limit=200)[0]
    den = quad(mu, 0, 100, points=brk, limit=200)[0]
    return num / den


def test_centroid_matches_numerical_integration():
    cases = [
        dict(sleep_hours=5, outstanding_assignments=6, screen_time_hours=8, meals_per_day=2),
        dict(sleep_hours=6.5, outstanding_assignments=7, screen_time_hours=5, meals_per_day=3),
        dict(sleep_hours=8, outstanding_assignments=1, screen_time_hours=1, meals_per_day=3),
        dict(sleep_hours=7, outstanding_assignments=3, screen_time_hours=7, meals_per_day=2),
    ]
    for c in cases:
        r = infer(c)
        assert abs(r.fatigue_index - _analytic_centroid(r.output_levels)) < 0.1, c


def test_category_thresholds():
    lo, hi = category_thresholds()
    assert abs(lo - 36.67) < 0.02 and abs(hi - 63.33) < 0.02


def test_directional_sanity():
    good = infer(dict(sleep_hours=8, outstanding_assignments=1, screen_time_hours=1, meals_per_day=3))
    bad = infer(dict(sleep_hours=4, outstanding_assignments=12, screen_time_hours=10, meals_per_day=1))
    assert good.fatigue_level == "LOW" and bad.fatigue_level == "HIGH"
    assert good.fatigue_index < 25 < 75 < bad.fatigue_index


def test_rule_ids_unique():
    ids = [r["id"] for r in RULES]
    assert len(ids) == len(set(ids))


def test_forward_chaining_multi_step():
    res = forward_chain({"level_high", "short_sleep", "heavy_workload"})
    iters = {s["derived"]: s["iteration"] for s in res.trace}
    assert iters["elevated_fatigue"] == 1
    assert iters["act_protect_sleep"] == 2       # needs elevated_fatigue first
    assert iters["act_seek_support"] == 2        # needs multiple_risk_factors first
    assert "act_deadline_extension" in dict(res.actions)


def test_low_level_only_maintain():
    res = recommend("LOW", {"sleep_hours": 0, "outstanding_assignments": 0,
                            "screen_time_hours": 0, "meals_per_day": 0})
    assert [a for a, _ in res.actions] == ["act_maintain_routine"]


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"{len(tests)} tests passed")
