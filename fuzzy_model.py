"""
fuzzy_model.py - Algorithmic core of the Fuzzy-Based Early Warning System
for Student Fatigue.

Method: Mamdani fuzzy inference system, implemented from scratch with NumPy
so that every step (fuzzification -> rule evaluation -> implication ->
aggregation -> defuzzification) is visible and can be explained in an oral
defense. No UI code lives in this file.

Operators used (fixed, see docs/DESIGN.md Part 5):
    AND between variables       : min
    OR between labels of 1 var  : bounded sum  min(1, a + b)
    Implication                 : min (clipping)
    Aggregation                 : max
    Defuzzification             : centroid over a discretised output universe

Every parameter below is tagged with its source:
    [REFERENCE-DERIVED]  - supported by a published reference
    [DATA-DERIVED]       - estimated from our own survey data (none yet)
    [DESIGN ASSUMPTION]  - a decision made by our team, NOT a medical fact
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# ---------------------------------------------------------------------------
# 1. MEMBERSHIP FUNCTION
# ---------------------------------------------------------------------------


def trapmf(x, a: float, b: float, c: float, d: float):
    """Trapezoidal membership function with corners a <= b <= c <= d.

    - rises linearly from a to b,
    - equals 1 between b and c,
    - falls linearly from c to d.
    A triangle is the special case b == c. A left "shoulder" uses a == b,
    a right "shoulder" uses c == d.
    Works for a scalar (returns float) or a NumPy array (returns array).
    """
    x_arr = np.asarray(x, dtype=float)
    y = np.zeros_like(x_arr)

    # Plateau (degree 1)
    y[(x_arr >= b) & (x_arr <= c)] = 1.0
    # Rising edge
    if b > a:
        rising = (x_arr > a) & (x_arr < b)
        y[rising] = (x_arr[rising] - a) / (b - a)
    # Falling edge
    if d > c:
        falling = (x_arr > c) & (x_arr < d)
        y[falling] = (d - x_arr[falling]) / (d - c)

    if np.ndim(x) == 0:
        return float(y)
    return y


# ---------------------------------------------------------------------------
# 2. LINGUISTIC VARIABLES (INPUTS)
# ---------------------------------------------------------------------------
# Every input uses a *Ruspini partition*: at any value at most two adjacent
# labels are active and their degrees sum to 1. This keeps the model easy to
# explain ("5.5 hours of sleep is 0.5 LOW and 0.5 NORMAL").

INPUT_VARIABLES = {
    "sleep_hours": {
        "label": "Sleep duration",
        "unit": "hours/day (average of last 7 days)",
        "range": (0.0, 12.0),
        "terms": {
            # Core of NORMAL = 7-9 h  [REFERENCE-DERIVED]
            #   (Hirshkowitz et al., 2015, National Sleep Foundation
            #    recommendation for young adults 18-25 y).
            # Slope widths (1 h) and LOW/HIGH plateaus [DESIGN ASSUMPTION].
            "LOW": (0.0, 0.0, 6.0, 7.0),
            "NORMAL": (6.0, 7.0, 9.0, 10.0),
            "HIGH": (9.0, 10.0, 12.0, 12.0),
        },
    },
    "outstanding_assignments": {
        "label": "Outstanding assignments",
        "unit": "assignments due in the next 7 days",
        "range": (0.0, 15.0),
        "terms": {
            # All breakpoints [DESIGN ASSUMPTION]; to be checked against the
            # survey distribution (see evaluation.mf_vs_data_percentiles).
            "FEW": (0.0, 0.0, 2.0, 4.0),
            "MODERATE": (2.0, 4.0, 6.0, 8.0),
            "MANY": (6.0, 8.0, 15.0, 15.0),
        },
    },
    "screen_time_hours": {
        "label": "Non-academic screen time",
        "unit": "hours/day (entertainment, social media, games)",
        "range": (0.0, 16.0),
        "terms": {
            # All breakpoints [DESIGN ASSUMPTION]. No clinical cut-off for
            # adults is claimed.
            "LOW": (0.0, 0.0, 2.0, 4.0),
            "MODERATE": (2.0, 4.0, 6.0, 8.0),
            "HIGH": (6.0, 8.0, 16.0, 16.0),
        },
    },
    "meals_per_day": {
        "label": "Meals per day",
        "unit": "main meals/day",
        "range": (0.0, 6.0),
        "terms": {
            # Centre of ADEQUATE = 3 meals/day [DESIGN ASSUMPTION]
            # (common daily routine, not a nutritional claim).
            "LOW": (0.0, 0.0, 1.0, 3.0),
            "ADEQUATE": (1.0, 3.0, 3.0, 5.0),
            "HIGH": (3.0, 5.0, 6.0, 6.0),
        },
    },
}

# ---------------------------------------------------------------------------
# 3. OUTPUT VARIABLE
# ---------------------------------------------------------------------------
# Fatigue Index on 0-100. All breakpoints [DESIGN ASSUMPTION].
OUTPUT_VARIABLE = {
    "label": "Fatigue Index",
    "range": (0.0, 100.0),
    "terms": {
        "LOW": (0.0, 0.0, 20.0, 45.0),
        "MODERATE": (30.0, 50.0, 50.0, 70.0),
        "HIGH": (55.0, 80.0, 100.0, 100.0),
    },
}
OUTPUT_TERMS_ORDER = ["LOW", "MODERATE", "HIGH"]

# Discretised output universe used for aggregation and centroid.
# Step 0.1 -> 1001 points [DESIGN ASSUMPTION: numerical resolution].
OUTPUT_UNIVERSE = np.linspace(0.0, 100.0, 1001)
# Output membership functions sampled once on the universe (speed only).
OUTPUT_MF_SAMPLED = {t: trapmf(OUTPUT_UNIVERSE, *p) for t, p in OUTPUT_VARIABLE["terms"].items()}

# ---------------------------------------------------------------------------
# 4. RULE BASE (11 rules)
# ---------------------------------------------------------------------------
# Antecedent format: {variable: [labels]}
#   - several labels of ONE variable are joined with OR  -> bounded sum
#     min(1, a + b). Because each input is a Ruspini partition,
#     "FEW or MODERATE" then equals exactly "NOT MANY" (= 1 - mu_MANY).
#     Plain max would dip to 0.5 at the crossover (see DESIGN.md Part 5).
#   - different variables are joined with AND -> min
# All rules are [DESIGN ASSUMPTION] written by our team; see DESIGN.md Part 4.
#
# Structure:
#   R1-R4  : base decision table  sleep x workload. R4 (-> LOW) additionally
#            requires screen time not HIGH and meals not LOW, so LOW is only
#            concluded when all four indicators are fine.
#   R5-R7  : escalation by high non-academic screen time (+1 level, never lower)
#   R8-R10 : escalation by low meal frequency           (+1 level, never lower)
#   R11    : both secondary risk factors together
# Rules that share a consequent on neighbouring labels are merged with OR,
# otherwise max-aggregation creates a dip at the label crossover.

NH = ["NORMAL", "HIGH"]        # sleep is NORMAL or HIGH  (= not LOW)
FM = ["FEW", "MODERATE"]       # assignments FEW or MODERATE (= not MANY)

RULES = [
    # --- Base decision table: sleep x outstanding assignments ---------------
    {"id": "R1", "if": {"sleep_hours": ["LOW"], "outstanding_assignments": ["MODERATE", "MANY"]},
     "then": "HIGH",
     "why": "Short sleep plus a non-trivial workload leaves little room for recovery."},
    {"id": "R2", "if": {"sleep_hours": ["LOW"], "outstanding_assignments": ["FEW"]},
     "then": "MODERATE",
     "why": "Short sleep alone is a warning sign even when the workload is light."},
    {"id": "R3", "if": {"sleep_hours": NH, "outstanding_assignments": ["MANY"]},
     "then": "MODERATE",
     "why": "Enough sleep, but a heavy workload is still a load."},
    {"id": "R4", "if": {"sleep_hours": NH, "outstanding_assignments": FM,
                        "screen_time_hours": ["LOW", "MODERATE"],
                        "meals_per_day": ["ADEQUATE", "HIGH"]},
     "then": "LOW",
     "why": "LOW only when ALL four indicators are fine: enough sleep, light-to-typical "
            "workload, screen time not high, meals not low."},
    # --- Escalation: high non-academic screen time -------------------------
    {"id": "R5", "if": {"screen_time_hours": ["HIGH"], "sleep_hours": NH,
                        "outstanding_assignments": FM},
     "then": "MODERATE",
     "why": "High screen time lifts an otherwise LOW situation (R4) one level."},
    {"id": "R6", "if": {"screen_time_hours": ["HIGH"], "outstanding_assignments": ["MANY"]},
     "then": "HIGH",
     "why": "High screen time on top of a heavy workload."},
    {"id": "R7", "if": {"screen_time_hours": ["HIGH"], "sleep_hours": ["LOW"]},
     "then": "HIGH",
     "why": "High screen time together with short sleep."},
    # --- Escalation: low meal frequency -------------------------------------
    {"id": "R8", "if": {"meals_per_day": ["LOW"], "sleep_hours": NH,
                        "outstanding_assignments": FM},
     "then": "MODERATE",
     "why": "Skipping meals lifts an otherwise LOW situation (R4) one level."},
    {"id": "R9", "if": {"meals_per_day": ["LOW"], "outstanding_assignments": ["MANY"]},
     "then": "HIGH",
     "why": "Skipping meals on top of a heavy workload."},
    {"id": "R10", "if": {"meals_per_day": ["LOW"], "sleep_hours": ["LOW"]},
     "then": "HIGH",
     "why": "Skipping meals together with short sleep."},
    # --- Both secondary risk factors -----------------------------------------
    {"id": "R11", "if": {"screen_time_hours": ["HIGH"], "meals_per_day": ["LOW"]},
     "then": "HIGH",
     "why": "Two lifestyle risk factors at the same time."},
]

# Which label of each input represents "risk" (used for contributing factors
# and for the knowledge-base facts in recommendation.py).
RISK_TERMS = {
    "sleep_hours": "LOW",
    "outstanding_assignments": "MANY",
    "screen_time_hours": "HIGH",
    "meals_per_day": "LOW",
}


def rule_to_text(rule: dict) -> str:
    """Human-readable IF-THEN text of a rule."""
    parts = []
    for var, labels in rule["if"].items():
        parts.append(f"{var} is {' or '.join(labels)}")
    return "IF " + " AND ".join(parts) + f" THEN fatigue is {rule['then']}"


# ---------------------------------------------------------------------------
# 5. INFERENCE PIPELINE
# ---------------------------------------------------------------------------


@dataclass
class FuzzyResult:
    inputs: dict                      # clamped crisp inputs
    memberships: dict                 # {var: {label: degree}}   (fuzzification)
    rule_strengths: list              # [{id, text, then, strength}] (rule evaluation)
    output_levels: dict               # {LOW/MODERATE/HIGH: max strength}
    aggregated: np.ndarray            # aggregated output fuzzy set over OUTPUT_UNIVERSE
    fatigue_index: float              # centroid (defuzzification)
    fatigue_level: str                # LOW / MODERATE / HIGH
    risk_degrees: dict = field(default_factory=dict)


def clamp_inputs(inputs: dict) -> dict:
    """Clip every input into its universe of discourse."""
    clamped = {}
    for var, spec in INPUT_VARIABLES.items():
        if var not in inputs:
            raise KeyError(f"Missing input: {var}")
        lo, hi = spec["range"]
        clamped[var] = float(np.clip(float(inputs[var]), lo, hi))
    return clamped


def fuzzify(inputs: dict) -> dict:
    """STEP 1 - Fuzzification: crisp value -> degree of membership per label."""
    memberships = {}
    for var, spec in INPUT_VARIABLES.items():
        x = inputs[var]
        memberships[var] = {term: trapmf(x, *params) for term, params in spec["terms"].items()}
    return memberships


def evaluate_rules(memberships: dict) -> list:
    """STEP 2 - Rule evaluation: firing strength of every rule.

    OR inside one variable = bounded sum min(1, a + b); AND across variables = min.
    """
    results = []
    for rule in RULES:
        per_variable = []
        for var, labels in rule["if"].items():
            per_variable.append(min(1.0, sum(memberships[var][lab] for lab in labels)))  # OR
        strength = min(per_variable)                                           # AND
        results.append({
            "id": rule["id"],
            "text": rule_to_text(rule),
            "then": rule["then"],
            "strength": float(strength),
        })
    return results


def implicate_and_aggregate(rule_strengths: list):
    """STEP 3+4 - Implication (min / clipping) and aggregation (max).

    Each rule clips its consequent set at its firing strength; the clipped
    sets of all rules are merged with max into one output fuzzy set.
    """
    aggregated = np.zeros_like(OUTPUT_UNIVERSE)
    output_levels = {term: 0.0 for term in OUTPUT_TERMS_ORDER}
    for r in rule_strengths:
        if r["strength"] <= 0.0:
            continue
        consequent_mf = OUTPUT_MF_SAMPLED[r["then"]]
        clipped = np.fmin(r["strength"], consequent_mf)     # implication (min)
        aggregated = np.fmax(aggregated, clipped)           # aggregation (max)
        output_levels[r["then"]] = max(output_levels[r["then"]], r["strength"])
    return aggregated, output_levels


def defuzzify_centroid(aggregated: np.ndarray) -> float:
    """STEP 5 - Centroid: sum(y * mu(y)) / sum(mu(y)) over the output universe."""
    area = float(np.sum(aggregated))
    if area == 0.0:
        # Cannot happen with this rule base (R1-R11 together cover every
        # input combination - see tests/test_model.py), but guard anyway.
        raise ValueError("No rule fired - rule base is incomplete for this input.")
    return float(np.sum(OUTPUT_UNIVERSE * aggregated) / area)


def categorize(index: float) -> str:
    """STEP 6 - Fatigue level = output label with the highest membership at
    the crisp index. Ties go to the more severe label (early-warning choice).
    """
    best_term, best_deg = None, -1.0
    for term in OUTPUT_TERMS_ORDER:  # LOW -> MODERATE -> HIGH
        deg = trapmf(index, *OUTPUT_VARIABLE["terms"][term])
        if deg >= best_deg:
            best_term, best_deg = term, deg
    return best_term


def category_thresholds() -> tuple:
    """Crossover points of the output MFs, i.e. where categorize() switches.
    Derived from OUTPUT_VARIABLE (not chosen separately)."""
    grid = np.linspace(0, 100, 100001)
    labels = np.array([categorize(v) for v in grid[::100]])  # coarse pass
    fine = []
    for i in range(1, len(labels)):
        if labels[i] != labels[i - 1]:
            lo, hi = grid[(i - 1) * 100], grid[i * 100]
            seg = np.linspace(lo, hi, 2001)
            seg_labels = [categorize(v) for v in seg]
            for j in range(1, len(seg)):
                if seg_labels[j] != seg_labels[j - 1]:
                    fine.append(round(float(seg[j]), 2))
                    break
    return tuple(fine)


def infer(inputs: dict) -> FuzzyResult:
    """Run the complete Mamdani pipeline on one student's inputs."""
    x = clamp_inputs(inputs)
    memberships = fuzzify(x)                                   # 1 fuzzification
    rule_strengths = evaluate_rules(memberships)               # 2 rule evaluation
    aggregated, levels = implicate_and_aggregate(rule_strengths)  # 3-4 implication + aggregation
    index = defuzzify_centroid(aggregated)                     # 5 defuzzification
    level = categorize(index)                                  # 6 category
    risk = {var: memberships[var][term] for var, term in RISK_TERMS.items()}
    return FuzzyResult(
        inputs=x,
        memberships=memberships,
        rule_strengths=rule_strengths,
        output_levels=levels,
        aggregated=aggregated,
        fatigue_index=index,
        fatigue_level=level,
        risk_degrees=risk,
    )


def fatigue_index(sleep_hours, outstanding_assignments, screen_time_hours, meals_per_day) -> float:
    """Convenience wrapper returning only the crisp index."""
    return infer({
        "sleep_hours": sleep_hours,
        "outstanding_assignments": outstanding_assignments,
        "screen_time_hours": screen_time_hours,
        "meals_per_day": meals_per_day,
    }).fatigue_index


if __name__ == "__main__":
    example = {"sleep_hours": 5, "outstanding_assignments": 6,
               "screen_time_hours": 8, "meals_per_day": 2}
    res = infer(example)
    print("Inputs:", res.inputs)
    for var, degs in res.memberships.items():
        print(f"  {var}: {degs}")
    for r in res.rule_strengths:
        if r["strength"] > 0:
            print(f"  {r['id']}: {r['strength']:.3f} -> {r['then']}")
    print("Output levels:", res.output_levels)
    print(f"Fatigue index: {res.fatigue_index:.2f} -> {res.fatigue_level}")
    print("Category thresholds:", category_thresholds())
