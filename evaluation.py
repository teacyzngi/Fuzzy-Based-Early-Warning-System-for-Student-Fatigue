"""
evaluation.py - Survey handling and evaluation utilities (no UI code).

The survey is used to EVALUATE the fuzzy system (does the fuzzy fatigue index
move in the same direction as students' self-reported fatigue?), not to
"train" it. See docs/DESIGN.md Part 6 and Part 14.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from fuzzy_model import INPUT_VARIABLES, OUTPUT_TERMS_ORDER, category_thresholds, infer

INPUT_COLUMNS = list(INPUT_VARIABLES.keys())
REQUIRED_COLUMNS = ["student_id"] + INPUT_COLUMNS + ["self_reported_fatigue"]
SELF_REPORT_RANGE = (1, 10)


# ---------------------------------------------------------------------------
# Data validation
# ---------------------------------------------------------------------------
def validate_survey(df: pd.DataFrame):
    """Return (clean_df, problems). Rows with missing / non-numeric /
    out-of-range values are dropped and reported, never silently fixed."""
    problems = []
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return None, [f"Missing column(s): {', '.join(missing)}"]

    clean = df[REQUIRED_COLUMNS].copy()
    for col in INPUT_COLUMNS + ["self_reported_fatigue"]:
        clean[col] = pd.to_numeric(clean[col], errors="coerce")

    bad = clean[INPUT_COLUMNS + ["self_reported_fatigue"]].isna().any(axis=1)
    if bad.any():
        problems.append(f"{int(bad.sum())} row(s) with missing or non-numeric values removed.")
    clean = clean[~bad]

    ranges = {c: INPUT_VARIABLES[c]["range"] for c in INPUT_COLUMNS}
    ranges["self_reported_fatigue"] = SELF_REPORT_RANGE
    out_of_range = pd.Series(False, index=clean.index)
    for col, (lo, hi) in ranges.items():
        out_of_range |= (clean[col] < lo) | (clean[col] > hi)
    if out_of_range.any():
        problems.append(
            f"{int(out_of_range.sum())} row(s) outside the allowed ranges removed "
            f"({', '.join(f'{c}: {lo}-{hi}' for c, (lo, hi) in ranges.items())})."
        )
    clean = clean[~out_of_range].reset_index(drop=True)
    return clean, problems


# ---------------------------------------------------------------------------
# Run the model on every row
# ---------------------------------------------------------------------------
def self_report_to_index(score):
    """Linear rescaling 1..10 -> 0..100 so both use the same scale.
    [DESIGN ASSUMPTION] - assumes the self-report scale is roughly interval."""
    lo, hi = SELF_REPORT_RANGE
    return (np.asarray(score, dtype=float) - lo) / (hi - lo) * 100.0


def self_report_to_level(score) -> str:
    """Map a 1-10 self-report to LOW/MODERATE/HIGH with the SAME thresholds as
    the fuzzy output (after rescaling). With thresholds 36.67 / 63.33 this
    gives 1-4 = LOW, 5-6 = MODERATE, 7-10 = HIGH."""
    t_low, t_high = category_thresholds()
    v = float(self_report_to_index(score))
    if v >= t_high:
        return "HIGH"
    if v >= t_low:
        return "MODERATE"
    return "LOW"


def run_model(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    idx, lvl = [], []
    for _, row in df.iterrows():
        r = infer({c: row[c] for c in INPUT_COLUMNS})
        idx.append(round(r.fatigue_index, 2))
        lvl.append(r.fatigue_level)
    out["fuzzy_index"] = idx
    out["fuzzy_level"] = lvl
    out["self_report_level"] = [self_report_to_level(s) for s in df["self_reported_fatigue"]]
    return out


# ---------------------------------------------------------------------------
# Agreement statistics
# ---------------------------------------------------------------------------
def _rank(x):
    return pd.Series(x).rank(method="average").to_numpy()


def spearman(x, y) -> float:
    """Spearman rank correlation = Pearson correlation of the ranks."""
    rx, ry = _rank(x), _rank(y)
    if np.std(rx) == 0 or np.std(ry) == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def bootstrap_ci(x, y, n_boot: int = 2000, seed: int = 42, alpha: float = 0.05):
    """Percentile bootstrap CI for Spearman rho (useful with small samples)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        i = rng.integers(0, len(x), len(x))
        r = spearman(x[i], y[i])
        if not np.isnan(r):
            vals.append(r)
    if not vals:
        return float("nan"), float("nan")
    return float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2))


def confusion_matrix(df: pd.DataFrame) -> pd.DataFrame:
    cm = pd.crosstab(df["self_report_level"], df["fuzzy_level"])
    return cm.reindex(index=OUTPUT_TERMS_ORDER, columns=OUTPUT_TERMS_ORDER, fill_value=0)


def cohen_kappa(df: pd.DataFrame) -> float:
    cm = confusion_matrix(df).to_numpy(dtype=float)
    n = cm.sum()
    if n == 0:
        return float("nan")
    po = np.trace(cm) / n
    pe = float((cm.sum(axis=0) * cm.sum(axis=1)).sum()) / n**2
    return float("nan") if pe == 1 else float((po - pe) / (1 - pe))


def agreement_summary(df: pd.DataFrame) -> dict:
    n = len(df)
    rho = spearman(df["fuzzy_index"], df["self_reported_fatigue"])
    lo, hi = bootstrap_ci(df["fuzzy_index"], df["self_reported_fatigue"]) if n >= 5 else (float("nan"),) * 2
    exact = float((df["fuzzy_level"] == df["self_report_level"]).mean()) if n else float("nan")
    mae = float(np.mean(np.abs(df["fuzzy_index"] - self_report_to_index(df["self_reported_fatigue"])))) if n else float("nan")
    return {
        "n": n,
        "spearman_rho": rho,
        "rho_ci95": (lo, hi),
        "category_agreement": exact,
        "cohen_kappa": cohen_kappa(df),
        "mae_index_vs_rescaled_self_report": mae,
    }


# ---------------------------------------------------------------------------
# Membership-function sanity check against the data (Approach A, light)
# ---------------------------------------------------------------------------
def mf_vs_data_percentiles(df: pd.DataFrame) -> pd.DataFrame:
    """Compare the MF crossover points with the survey tertiles.
    This is only a sanity check; parameters are NOT changed automatically."""
    rows = []
    for var in INPUT_COLUMNS:
        terms = list(INPUT_VARIABLES[var]["terms"].values())
        # crossover between term1-term2 and term2-term3 (midpoint of shared slope)
        cross_1 = (terms[0][2] + terms[0][3]) / 2
        cross_2 = (terms[1][2] + terms[1][3]) / 2
        rows.append({
            "variable": var,
            "MF crossover 1": cross_1,
            "MF crossover 2": cross_2,
            "data P33": round(float(df[var].quantile(1 / 3)), 2),
            "data P67": round(float(df[var].quantile(2 / 3)), 2),
            "data min": float(df[var].min()),
            "data max": float(df[var].max()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Sensitivity and monotonicity (model checks, need no survey data)
# ---------------------------------------------------------------------------
def sensitivity_sweep(baseline: dict, var: str, n: int = 121) -> pd.DataFrame:
    """Vary one input over its whole range, keep the others at baseline."""
    lo, hi = INPUT_VARIABLES[var]["range"]
    xs = np.linspace(lo, hi, n)
    ys = []
    for x in xs:
        inp = dict(baseline)
        inp[var] = x
        ys.append(infer(inp).fatigue_index)
    return pd.DataFrame({var: xs, "fatigue_index": ys})


# Direction in which each input becomes "riskier" and the part of its range
# where that direction is meaningful (sleep above 8 h and meals above 3 are
# treated as neutral by the rule base, so they are excluded).
RISK_DIRECTION = {
    "sleep_hours": ("decreasing", 0.0, 8.0),
    "outstanding_assignments": ("increasing", 0.0, 15.0),
    "screen_time_hours": ("increasing", 0.0, 16.0),
    "meals_per_day": ("decreasing", 0.0, 3.0),
}


def _context_grid(var: str) -> np.ndarray:
    """Values of one input used as fixed context: every MF breakpoint, the
    quarter points inside every slope (where two labels overlap), and the
    range ends. Transition zones are where Mamdani artefacts appear, so a
    plain even grid would hide them."""
    lo, hi = INPUT_VARIABLES[var]["range"]
    pts = {lo, hi}
    for a, b, c, d in INPUT_VARIABLES[var]["terms"].values():
        for s, e in ((a, b), (c, d)):
            if e > s:
                pts.update(np.linspace(s, e, 5).tolist())
    return np.array(sorted(pts))


def monotonicity_check(step: float = 0.25) -> pd.DataFrame:
    """For each input, walk in the 'riskier' direction with the other inputs
    fixed on a context grid and count how often the index goes DOWN.
    Also counts how often the fatigue LEVEL goes down."""
    order = {t: i for i, t in enumerate(OUTPUT_TERMS_ORDER)}
    grids = {v: _context_grid(v) for v in INPUT_COLUMNS}
    rows = []
    for var, (direction, lo, hi) in RISK_DIRECTION.items():
        path = np.arange(lo, hi + 1e-9, step)
        if direction == "decreasing":
            path = path[::-1]
        others = [v for v in INPUT_COLUMNS if v != var]
        steps, drops, level_drops, max_drop = 0, 0, 0, 0.0
        for ctx in itertools.product(*(grids[o] for o in others)):
            base = dict(zip(others, ctx))
            res = [infer({**base, var: x}) for x in path]
            vals = np.array([r.fatigue_index for r in res])
            lv = np.array([order[r.fatigue_level] for r in res])
            d = np.diff(vals)
            steps += len(d)
            drops += int((d < -0.01).sum())
            level_drops += int((np.diff(lv) < 0).sum())
            if d.min() < 0:
                max_drop = max(max_drop, float(-d.min()))
        rows.append({
            "input (riskier direction)": f"{var} ({direction})",
            "steps checked": steps,
            "index fell > 0.01": drops,
            "% of steps": round(100 * drops / steps, 3),
            "largest fall (points)": round(max_drop, 2),
            "level went down": level_drops,
        })
    return pd.DataFrame(rows)
