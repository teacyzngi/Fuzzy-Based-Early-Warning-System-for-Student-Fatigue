"""Run the 8+ scenario test cases through the ACTUAL implemented model and
print a Markdown table. Results in docs/DESIGN.md Part 13 were produced by
this script - rerun it after any change to the rules or MFs.

    python run_test_cases.py
"""
from fuzzy_model import infer
from recommendation import recommend

CASES = [
    ("1. Very healthy routine", dict(sleep_hours=8, outstanding_assignments=1, screen_time_hours=1.5, meals_per_day=3)),
    ("2. Low sleep", dict(sleep_hours=4.5, outstanding_assignments=2, screen_time_hours=2, meals_per_day=3)),
    ("3. High workload", dict(sleep_hours=7.5, outstanding_assignments=10, screen_time_hours=2, meals_per_day=3)),
    ("4. High screen time", dict(sleep_hours=7.5, outstanding_assignments=3, screen_time_hours=9, meals_per_day=3)),
    ("5. Low meal frequency", dict(sleep_hours=7.5, outstanding_assignments=3, screen_time_hours=2, meals_per_day=1)),
    ("6. Multiple risk factors", dict(sleep_hours=5, outstanding_assignments=9, screen_time_hours=8, meals_per_day=1)),
    ("7a. Borderline (sleep 6.5 h)", dict(sleep_hours=6.5, outstanding_assignments=5, screen_time_hours=5, meals_per_day=3)),
    ("7b. Borderline (workload 7)", dict(sleep_hours=7.5, outstanding_assignments=7, screen_time_hours=7, meals_per_day=2)),
    ("8a. Extreme - worst", dict(sleep_hours=2, outstanding_assignments=15, screen_time_hours=14, meals_per_day=0)),
    ("8b. Extreme - out of range input", dict(sleep_hours=12, outstanding_assignments=30, screen_time_hours=0, meals_per_day=6)),
    ("9. Worked example (DESIGN Part 5)", dict(sleep_hours=5, outstanding_assignments=6, screen_time_hours=8, meals_per_day=2)),
]

SHORT = {"sleep_hours": "S", "outstanding_assignments": "A", "screen_time_hours": "C", "meals_per_day": "M"}


def main():
    print("| Case | Input (S h, A, C h, M) | Rules fired (strength -> output) | Output clip levels L/M/H | Index | Level | Recommended actions |")
    print("|---|---|---|---|---|---|---|")
    for name, inp in CASES:
        r = infer(inp)
        fired = ", ".join(f"{x['id']} {x['strength']:.2f}->{x['then'][0]}" for x in r.rule_strengths if x["strength"] > 0)
        lv = "/".join(f"{r.output_levels[t]:.2f}" for t in ("LOW", "MODERATE", "HIGH"))
        rec = recommend(r.fatigue_level, r.risk_degrees)
        acts = ", ".join(a.replace("act_", "") for a, _ in rec.actions)
        inp_s = ", ".join(str(inp[k]) for k in SHORT)
        print(f"| {name} | {inp_s} | {fired} | {lv} | {r.fatigue_index:.2f} | {r.fatigue_level} | {acts} |")


if __name__ == "__main__":
    main()
