import os

import pandas as pd
import streamlit as st

import evaluation as ev
from components import charts
from fuzzy_model import OUTPUT_TERMS_ORDER

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUMMY_PATH = os.path.join(APP_DIR, "data", "dummy_survey_data.csv")

st.title("Survey Data & Evaluation")
st.markdown("Kolom CSV yang dibutuhkan: `" + ",".join(ev.REQUIRED_COLUMNS) + "`  \n"
            "`self_reported_fatigue` adalah rating diri 1-10 (acuan subjektif, **bukan** ground truth klinis).")

c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
uploaded = c1.file_uploader("Upload CSV survei", type=["csv"])
use_dummy = c2.toggle("Pakai data DUMMY (hanya untuk uji aplikasi)")

if uploaded is not None:
    raw = pd.read_csv(uploaded)
    source = "uploaded"
elif use_dummy:
    raw = pd.read_csv(DUMMY_PATH)
    source = "dummy"
else:
    st.info("Upload CSV atau aktifkan data dummy.")
    st.stop()

if source == "dummy" or raw.get("student_id", pd.Series(dtype=str)).astype(str).str.startswith("DUMMY").any():
    st.error("DUMMY DATA: dibuat tim untuk menguji aplikasi. Ini BUKAN hasil survei, "
             "dan semua statistik di bawah tidak bermakna sebagai bukti.", icon=":material/error:")

df, problems = ev.validate_survey(raw)
for p in problems:
    st.warning(p)
if df is None or df.empty:
    st.error("Tidak ada baris valid untuk dianalisis.")
    st.stop()
st.success(f"{len(df)} baris valid dimuat.", icon=":material/check_circle:")

scored = ev.run_model(df)
summary = ev.agreement_summary(scored)

tab_desc, tab_agree, tab_data = st.tabs(["Statistik deskriptif", "Kesepakatan", "Data ter-scoring"])

with tab_desc:
    st.dataframe(df[ev.INPUT_COLUMNS + ["self_reported_fatigue"]].describe().round(2), width="stretch")
    cols = st.columns(3)
    for i, col in enumerate(ev.INPUT_COLUMNS + ["self_reported_fatigue"]):
        cols[i % 3].plotly_chart(charts.histogram(df[col], col), width="stretch",
                                 config={"displayModeBar": False})
    st.subheader("Fungsi keanggotaan vs data")
    st.caption("Sanity check saja; parameter tidak diubah otomatis.")
    st.dataframe(ev.mf_vs_data_percentiles(df), hide_index=True, width="stretch")

with tab_agree:
    lo, hi = summary["rho_ci95"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("n", summary["n"], border=True)
    m2.metric("Spearman ρ", f"{summary['spearman_rho']:.2f}", border=True,
              help=f"95% bootstrap CI: [{lo:.2f}, {hi:.2f}]")
    m3.metric("Category agreement", f"{100 * summary['category_agreement']:.0f}%", border=True)
    m4.metric("Cohen's κ", f"{summary['cohen_kappa']:.2f}", border=True)
    st.caption(f"Spearman 95% bootstrap CI: [{lo:.2f}, {hi:.2f}]. Self-report dipetakan ke level dengan "
               "ambang yang sama setelah diskalakan 1-10 → 0-100 (1-4 LOW, 5-6 MODERATE, 7-10 HIGH).")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("**Fuzzy index vs self-report**")
        st.plotly_chart(charts.scatter_index_vs_self(scored), width="stretch",
                        config={"displayModeBar": False})
    with c2:
        st.markdown("**Confusion matrix** (baris = self-report, kolom = fuzzy)")
        st.plotly_chart(charts.confusion_heatmap(ev.confusion_matrix(scored)), width="stretch",
                        config={"displayModeBar": False})
    st.markdown("**Distribusi level fuzzy**")
    st.bar_chart(scored["fuzzy_level"].value_counts().reindex(OUTPUT_TERMS_ORDER, fill_value=0))

with tab_data:
    st.dataframe(scored, hide_index=True, width="stretch")
    st.download_button("Download CSV ter-scoring", scored.to_csv(index=False).encode("utf-8"),
                       file_name="scored_survey.csv", mime="text/csv", icon=":material/download:")
