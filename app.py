"""
app.py - Streamlit user interface.

Only presentation code lives here. The algorithmic core is in:
    fuzzy_model.py      Mamdani fuzzy inference (fatigue index)
    recommendation.py   forward-chaining knowledge base (recommended actions)
    evaluation.py       survey validation and agreement statistics

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

import evaluation as ev  # noqa: E402
from fuzzy_model import (INPUT_VARIABLES, OUTPUT_TERMS_ORDER, OUTPUT_UNIVERSE,  # noqa: E402
                         OUTPUT_VARIABLE, RULES, category_thresholds, infer, rule_to_text, trapmf)
from recommendation import KB_RULES, main_contributing_factors, recommend  # noqa: E402

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DUMMY_PATH = os.path.join(APP_DIR, "data", "dummy_survey_data.csv")
DISCLAIMER = "This system is an academic prototype and is not a medical diagnostic tool."
PAGES = ["Home", "Fatigue Assessment", "Result", "How the Model Works", "Survey Data"]
LEVEL_COLOR = {"LOW": "#2e7d32", "MODERATE": "#ef6c00", "HIGH": "#c62828"}
TERM_COLORS = ["#1f77b4", "#ff7f0e", "#d62728"]
DEFAULT_INPUT = {"sleep_hours": 7.0, "outstanding_assignments": 3,
                 "screen_time_hours": 3.0, "meals_per_day": 3}

st.set_page_config(page_title="Student Fatigue Early Warning", page_icon="🧭", layout="wide")

# ---------------------------------------------------------------------------
# Session state and navigation
# ---------------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "assessed" not in st.session_state:
    st.session_state.assessed = None


def go_to(page):
    st.session_state.page = page


def analyze_callback():
    """Runs when 'Analyze Fatigue' is pressed (before the next rerun)."""
    st.session_state.assessed = {
        "sleep_hours": float(st.session_state.in_sleep),
        "outstanding_assignments": float(st.session_state.in_assign),
        "screen_time_hours": float(st.session_state.in_screen),
        "meals_per_day": float(st.session_state.in_meals),
    }
    st.session_state.page = "Result"


st.sidebar.title("Navigation")
st.sidebar.radio("Go to", PAGES, key="page")
st.sidebar.markdown("---")
st.sidebar.caption(DISCLAIMER)

# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------


def plot_input_mf(var, value=None):
    spec = INPUT_VARIABLES[var]
    lo, hi = spec["range"]
    xs = np.linspace(lo, hi, 400)
    fig, ax = plt.subplots(figsize=(4.2, 2.3))
    for (term, params), color in zip(spec["terms"].items(), TERM_COLORS):
        ax.plot(xs, trapmf(xs, *params), label=term, color=color)
    if value is not None:
        ax.axvline(value, color="black", linestyle="--", linewidth=1)
        for (term, params), color in zip(spec["terms"].items(), TERM_COLORS):
            d = trapmf(value, *params)
            if d > 0:
                ax.plot([value], [d], "o", color=color)
                ax.annotate(f"{d:.2f}", (value, d), textcoords="offset points", xytext=(5, 3), fontsize=8)
    ax.set_title(spec["label"], fontsize=10)
    ax.set_xlabel(spec["unit"], fontsize=8)
    ax.set_ylim(-0.05, 1.15)
    ax.legend(fontsize=7, loc="center right")
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    return fig


def plot_output(result=None):
    fig, ax = plt.subplots(figsize=(7, 2.8))
    for (term, params), color in zip(OUTPUT_VARIABLE["terms"].items(), TERM_COLORS):
        ax.plot(OUTPUT_UNIVERSE, trapmf(OUTPUT_UNIVERSE, *params), "--", color=color, label=term, linewidth=1)
    if result is not None:
        ax.fill_between(OUTPUT_UNIVERSE, result.aggregated, color="grey", alpha=0.45, label="aggregated output")
        ax.axvline(result.fatigue_index, color="black", linewidth=2)
        ax.annotate(f"centroid = {result.fatigue_index:.1f}", (result.fatigue_index, 1.05),
                    xytext=(5, 0), textcoords="offset points", fontsize=9)
    ax.set_xlabel("Fatigue Index")
    ax.set_ylabel("membership")
    ax.set_ylim(-0.05, 1.2)
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    return fig


def plot_gauge(index, level):
    t_low, t_high = category_thresholds()
    fig, ax = plt.subplots(figsize=(7, 1.1))
    ax.barh(0, t_low, color=LEVEL_COLOR["LOW"], alpha=0.35)
    ax.barh(0, t_high - t_low, left=t_low, color=LEVEL_COLOR["MODERATE"], alpha=0.35)
    ax.barh(0, 100 - t_high, left=t_high, color=LEVEL_COLOR["HIGH"], alpha=0.35)
    ax.plot([index], [0], marker="v", markersize=16, color=LEVEL_COLOR[level])
    ax.set_xlim(0, 100)
    ax.set_yticks([])
    ax.set_xticks([0, t_low, t_high, 100])
    ax.set_xticklabels(["0", f"{t_low:.1f}", f"{t_high:.1f}", "100"])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


def page_home():
    st.title("Fuzzy-Based Early Warning System for Student Fatigue")
    st.write(
        "Sistem prototype untuk memperkirakan tingkat kelelahan mahasiswa berdasarkan "
        "beberapa indikator aktivitas harian: durasi tidur, jumlah tugas yang belum selesai, "
        "screen time non-akademik, dan frekuensi makan."
    )
    st.warning(DISCLAIMER)
    c1, c2, c3 = st.columns(3)
    c1.markdown("**1. Fuzzy inference (Mamdani)**  \n4 inputs → fuzzification → 11 IF-THEN rules → "
                "aggregation → centroid → Fatigue Index 0-100")
    c2.markdown("**2. Knowledge base (forward chaining)**  \nFatigue level + risk facts → "
                "Horn-clause rules → recommended actions, with an inference trace")
    c3.markdown("**3. Survey evaluation**  \nUpload survey CSV → compare the fuzzy index with "
                "self-reported fatigue (rank correlation, category agreement)")
    st.button("Start assessment →", on_click=go_to, args=("Fatigue Assessment",))


def page_assessment():
    st.title("Fatigue Assessment")
    st.caption("Answer for a typical day in the last 7 days.")
    prev = st.session_state.assessed or DEFAULT_INPUT
    with st.form("assessment_form"):
        c1, c2 = st.columns(2)
        c1.number_input("Sleep duration (hours per day)", min_value=0.0, max_value=24.0,
                        value=float(prev["sleep_hours"]), step=0.5, key="in_sleep")
        c2.number_input("Outstanding assignments (due in the next 7 days)", min_value=0, max_value=50,
                        value=int(prev["outstanding_assignments"]), step=1, key="in_assign")
        c1.number_input("Active non-academic screen time (hours per day)", min_value=0.0, max_value=24.0,
                        value=float(prev["screen_time_hours"]), step=0.5, key="in_screen",
                        help="Entertainment, social media, games - not studying.")
        c2.number_input("Meals per day", min_value=0, max_value=10,
                        value=int(prev["meals_per_day"]), step=1, key="in_meals")
        st.form_submit_button("Analyze Fatigue", type="primary", on_click=analyze_callback)
    st.caption("Values outside the model range are clipped: sleep 0-12 h, assignments 0-15, "
               "screen time 0-16 h, meals 0-6.")


def page_result():
    st.title("Result")
    if st.session_state.assessed is None:
        st.info("No assessment yet. Please fill in the form first.")
        st.button("Go to Fatigue Assessment", on_click=go_to, args=("Fatigue Assessment",))
        return

    res = infer(st.session_state.assessed)
    rec = recommend(res.fatigue_level, res.risk_degrees)

    c1, c2 = st.columns(2)
    c1.metric("Fatigue Index", f"{res.fatigue_index:.1f} / 100")
    c2.markdown(
        f"**Fatigue Level**<br><span style='font-size:2rem;font-weight:700;color:{LEVEL_COLOR[res.fatigue_level]}'>"
        f"{res.fatigue_level}</span>", unsafe_allow_html=True)
    st.pyplot(plot_gauge(res.fatigue_index, res.fatigue_level))
    plt.close("all")

    left, right = st.columns(2)
    with left:
        st.subheader("Main contributing factors")
        factors = main_contributing_factors(res.risk_degrees)
        if factors:
            fdf = pd.DataFrame(factors, columns=["factor", "risk membership"]).set_index("factor")
            st.bar_chart(fdf)
        else:
            st.write("No risk factor is active (all risk memberships are 0).")
    with right:
        st.subheader("Recommendation")
        for _, text in rec.actions:
            st.markdown(f"- {text}")
        st.caption("General well-being suggestions, not medical advice.")

    st.subheader("How this result was computed")
    st.markdown("**Step 1 - Fuzzification** (degree of membership of each input)")
    rows = []
    for var, degs in res.memberships.items():
        row = {"input": INPUT_VARIABLES[var]["label"], "value": res.inputs[var]}
        row.update({k: round(v, 3) for k, v in degs.items()})
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), hide_index=True)
    cols = st.columns(4)
    for col, var in zip(cols, INPUT_VARIABLES):
        col.pyplot(plot_input_mf(var, res.inputs[var]))
    plt.close("all")

    st.markdown("**Step 2 - Rule evaluation** (rules with firing strength > 0; AND = min, OR = bounded sum)")
    fired = [r for r in res.rule_strengths if r["strength"] > 0]
    st.dataframe(pd.DataFrame([{"rule": r["id"], "strength": round(r["strength"], 3),
                                "then fatigue is": r["then"], "rule text": r["text"]} for r in fired]),
                 hide_index=True)

    st.markdown("**Step 3-5 - Implication (clip), aggregation (max), defuzzification (centroid)**")
    st.write("Clip level per output label: " + ", ".join(
        f"{t} = {res.output_levels[t]:.2f}" for t in OUTPUT_TERMS_ORDER))
    st.pyplot(plot_output(res))
    plt.close("all")

    with st.expander("Recommendation reasoning (forward chaining trace)"):
        st.write("Initial facts:", ", ".join(rec.initial_facts))
        st.dataframe(pd.DataFrame(rec.trace), hide_index=True)
        st.caption("A risk fact is added when its membership is ≥ 0.5.")

    st.button("← New assessment", on_click=go_to, args=("Fatigue Assessment",))


def page_model():
    st.title("How the Model Works")
    st.markdown("Mamdani fuzzy inference: **AND = min**, **OR (within one input) = bounded sum**, "
                "**implication = min (clipping)**, **aggregation = max**, **defuzzification = centroid**.")
    st.subheader("Membership functions")
    cols = st.columns(2)
    for i, var in enumerate(INPUT_VARIABLES):
        cols[i % 2].pyplot(plot_input_mf(var))
    st.pyplot(plot_output())
    plt.close("all")
    t_low, t_high = category_thresholds()
    st.caption(f"Fatigue level = output label with the highest membership at the index "
               f"→ LOW < {t_low:.2f} ≤ MODERATE < {t_high:.2f} ≤ HIGH.")

    st.subheader(f"Fuzzy rule base ({len(RULES)} rules)")
    st.dataframe(pd.DataFrame([{"id": r["id"], "rule": rule_to_text(r), "reason": r["why"]} for r in RULES]),
                 hide_index=True)

    st.subheader(f"Recommendation knowledge base ({len(KB_RULES)} Horn clauses)")
    st.dataframe(pd.DataFrame([{"id": r["id"], "IF": " AND ".join(r["if"]), "THEN": r["then"]}
                               for r in KB_RULES]), hide_index=True)

    st.subheader("Sensitivity (one input varied, others fixed)")
    base = st.session_state.assessed or {k: float(v) for k, v in DEFAULT_INPUT.items()}
    st.caption("Baseline: " + ", ".join(f"{k} = {v:g}" for k, v in base.items()))
    var = st.selectbox("Input to vary", list(INPUT_VARIABLES),
                       format_func=lambda v: INPUT_VARIABLES[v]["label"])
    sweep = ev.sensitivity_sweep(base, var)
    st.line_chart(sweep.set_index(var))


def page_survey():
    st.title("Survey Data")
    st.markdown("Expected CSV columns: `" + ",".join(ev.REQUIRED_COLUMNS) + "`  \n"
                "`self_reported_fatigue` is a 1-10 self-rating (a subjective reference, **not** clinical ground truth).")
    uploaded = st.file_uploader("Upload survey CSV", type=["csv"])
    use_dummy = st.checkbox("Use the DUMMY dataset instead (for testing the app only)")

    if uploaded is not None:
        raw = pd.read_csv(uploaded)
        source = "uploaded"
    elif use_dummy:
        raw = pd.read_csv(DUMMY_PATH)
        source = "dummy"
    else:
        st.info("Upload a CSV or tick the dummy-dataset box.")
        return

    if source == "dummy" or raw.get("student_id", pd.Series(dtype=str)).astype(str).str.startswith("DUMMY").any():
        st.error("DUMMY DATA - invented by the team to test the app. These are NOT survey results, "
                 "and any statistic below is meaningless as evidence.")

    df, problems = ev.validate_survey(raw)
    for p in problems:
        st.warning(p)
    if df is None or df.empty:
        st.error("No valid rows to analyse.")
        return

    st.subheader(f"Preview ({len(df)} valid rows)")
    st.dataframe(df, hide_index=True)
    st.subheader("Basic statistics")
    st.dataframe(df[ev.INPUT_COLUMNS + ["self_reported_fatigue"]].describe().round(2))

    st.subheader("Distribution of inputs")
    fig, axes = plt.subplots(1, 5, figsize=(14, 2.6))
    for ax, col in zip(axes, ev.INPUT_COLUMNS + ["self_reported_fatigue"]):
        ax.hist(df[col], bins=8, color="#4c72b0", edgecolor="white")
        ax.set_title(col, fontsize=9)
        ax.tick_params(labelsize=8)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close("all")

    st.subheader("Membership functions vs data (sanity check, parameters are not changed)")
    st.dataframe(ev.mf_vs_data_percentiles(df), hide_index=True)

    st.subheader("Fuzzy index vs self-reported fatigue")
    scored = ev.run_model(df)
    summary = ev.agreement_summary(scored)
    lo, hi = summary["rho_ci95"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("n", summary["n"])
    m2.metric("Spearman ρ", f"{summary['spearman_rho']:.2f}", help=f"95% bootstrap CI: [{lo:.2f}, {hi:.2f}]")
    m3.metric("Category agreement", f"{100 * summary['category_agreement']:.0f}%")
    m4.metric("Cohen's κ", f"{summary['cohen_kappa']:.2f}")
    st.caption(f"Spearman 95% bootstrap CI: [{lo:.2f}, {hi:.2f}]. Self-report mapped to levels with the same "
               "thresholds after rescaling 1-10 → 0-100 (1-4 LOW, 5-6 MODERATE, 7-10 HIGH).")

    c1, c2 = st.columns(2)
    with c1:
        fig, ax = plt.subplots(figsize=(5, 3.6))
        ax.scatter(scored["self_reported_fatigue"], scored["fuzzy_index"], color="#4c72b0")
        ax.set_xlabel("self-reported fatigue (1-10)")
        ax.set_ylabel("fuzzy fatigue index (0-100)")
        ax.set_xlim(0.5, 10.5)
        ax.set_ylim(0, 100)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close("all")
    with c2:
        st.write("Confusion matrix (rows = self-report level, columns = fuzzy level)")
        st.dataframe(ev.confusion_matrix(scored))
        st.write("Distribution of fuzzy levels")
        st.bar_chart(scored["fuzzy_level"].value_counts().reindex(OUTPUT_TERMS_ORDER, fill_value=0))

    st.subheader("Scored data")
    st.dataframe(scored, hide_index=True)
    st.download_button("Download scored CSV", scored.to_csv(index=False).encode("utf-8"),
                       file_name="scored_survey.csv", mime="text/csv")


PAGE_FUNCS = {
    "Home": page_home,
    "Fatigue Assessment": page_assessment,
    "Result": page_result,
    "How the Model Works": page_model,
    "Survey Data": page_survey,
}
PAGE_FUNCS[st.session_state.page]()
