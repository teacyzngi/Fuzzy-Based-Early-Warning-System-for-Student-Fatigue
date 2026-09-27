"""Export report figures to docs/figures/ using the same plotting code as the app.
    python make_figures.py
"""
import os
import sys
import types

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from fuzzy_model import INPUT_VARIABLES, infer  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "figures")


def _load_plot_helpers():
    """Reuse app.py's plot functions without starting Streamlit."""
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"), encoding="utf-8").read()
    start = src.index("def plot_input_mf")
    end = src.index("# ---------------------------------------------------------------------------\n# Pages")
    mod = types.ModuleType("plots")
    exec("import numpy as np\nimport matplotlib.pyplot as plt\n"
         "from fuzzy_model import *\nfrom fuzzy_model import category_thresholds\n"
         "LEVEL_COLOR = {'LOW': '#2e7d32', 'MODERATE': '#ef6c00', 'HIGH': '#c62828'}\n"
         "TERM_COLORS = ['#1f77b4', '#ff7f0e', '#d62728']\n" + src[start:end], mod.__dict__)
    return mod


def main():
    os.makedirs(OUT, exist_ok=True)
    p = _load_plot_helpers()
    ex = {"sleep_hours": 5, "outstanding_assignments": 6, "screen_time_hours": 8, "meals_per_day": 2}
    res = infer(ex)
    fig, axes = plt.subplots(2, 2, figsize=(9, 5))
    plt.close(fig)
    for var in INPUT_VARIABLES:
        f = p.plot_input_mf(var, ex[var])
        f.savefig(os.path.join(OUT, f"mf_{var}.png"), dpi=160)
        plt.close(f)
    f = p.plot_output()
    f.savefig(os.path.join(OUT, "mf_output.png"), dpi=160)
    plt.close(f)
    f = p.plot_output(res)
    f.savefig(os.path.join(OUT, "worked_example_aggregation.png"), dpi=160)
    plt.close(f)
    f = p.plot_gauge(res.fatigue_index, res.fatigue_level)
    f.savefig(os.path.join(OUT, "worked_example_gauge.png"), dpi=160)
    plt.close(f)
    print("Figures written to", OUT)


if __name__ == "__main__":
    sys.exit(main())
