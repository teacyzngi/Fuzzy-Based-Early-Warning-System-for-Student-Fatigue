import pandas as pd
import streamlit as st

import evaluation as ev
from components import charts
from components.ui import WORKED_EXAMPLE, current_input, level_badge
from fuzzy_model import INPUT_VARIABLES, OUTPUT_TERMS_ORDER, RULES, category_thresholds, infer, rule_to_text
from recommendation import KB_RULES, recommend

st.title("How the Model Works")
st.markdown("Mamdani fuzzy inference: **AND = min**, **OR (dalam satu input) = bounded sum**, "
            "**implikasi = min (clipping)**, **agregasi = max**, **defuzzifikasi = centroid**.")

tabs = st.tabs(["Membership functions", "Fuzzy rules", "KB rules", "Sensitivity", "Worked example"])

with tabs[0]:
    cols = st.columns(2)
    for i, var in enumerate(INPUT_VARIABLES):
        cols[i % 2].plotly_chart(charts.input_mf(var), width="stretch", config={"displayModeBar": False})
    st.plotly_chart(charts.output_mf(), width="stretch", config={"displayModeBar": False})
    t_low, t_high = category_thresholds()
    st.caption(f"Level = label output dengan keanggotaan tertinggi pada indeks "
               f"→ LOW < {t_low:.2f} ≤ MODERATE < {t_high:.2f} ≤ HIGH.")

with tabs[1]:
    st.caption(f"{len(RULES)} aturan. R1-R4 tabel dasar tidur × beban tugas, R5-R11 eskalasi oleh "
               "screen time tinggi dan frekuensi makan rendah.")
    for r in RULES:
        with st.container(border=True):
            st.markdown(f"**{r['id']}** &nbsp; `{rule_to_text(r)}`")
            st.caption(r["why"])

with tabs[2]:
    st.caption(f"{len(KB_RULES)} Horn clause. Kesimpulan berawalan `act_` adalah rekomendasi.")
    st.dataframe(pd.DataFrame([{"id": r["id"], "IF": " AND ".join(r["if"]), "THEN": r["then"]}
                               for r in KB_RULES]), hide_index=True, width="stretch")

with tabs[3]:
    base = current_input()
    st.caption("Satu input divariasikan, input lain tetap pada baseline "
               "(input assessment terakhir, atau nilai default).")
    st.caption("Baseline: " + ", ".join(f"{INPUT_VARIABLES[k]['label']} = {v:g}" for k, v in base.items()))
    var = st.selectbox("Input yang divariasikan", list(INPUT_VARIABLES),
                       format_func=lambda v: INPUT_VARIABLES[v]["label"])
    sweep = ev.sensitivity_sweep(base, var)
    st.plotly_chart(charts.sensitivity(sweep, var, base[var]), width="stretch",
                    config={"displayModeBar": False})

with tabs[4]:
    ex = infer(WORKED_EXAMPLE)
    ex_rec = recommend(ex.fatigue_level, ex.risk_degrees)
    st.markdown("Input: " + ", ".join(f"{INPUT_VARIABLES[k]['label']} = {v:g}"
                                      for k, v in WORKED_EXAMPLE.items()))
    fired = [r for r in ex.rule_strengths if r["strength"] > 0]
    steps = [
        ("Fuzzifikasi", "; ".join(
            f"{INPUT_VARIABLES[v]['label']}: " + ", ".join(f"{t} = {d:.2f}" for t, d in degs.items() if d > 0)
            for v, degs in ex.memberships.items())),
        ("Aturan aktif", ", ".join(f"{r['id']} = {r['strength']:.2f} → {r['then']}" for r in fired)),
        ("Agregasi", ", ".join(f"{t} {ex.output_levels[t]:.2f}" for t in OUTPUT_TERMS_ORDER)),
        ("Centroid", f"{ex.fatigue_index:.2f} → {ex.fatigue_level}"),
        ("Rekomendasi", "; ".join(a for a, _ in ex_rec.actions)),
    ]
    st.dataframe(pd.DataFrame(steps, columns=["langkah", "hasil"]), hide_index=True, width="stretch")
    st.markdown(f"Hasil: {level_badge(ex.fatigue_level, '1.1rem')}", unsafe_allow_html=True)
    st.plotly_chart(charts.output_mf(ex), width="stretch", config={"displayModeBar": False})
    st.caption("Dihitung langsung oleh fuzzy_model.infer(); sama dengan contoh di README dan docs/DESIGN.md.")
