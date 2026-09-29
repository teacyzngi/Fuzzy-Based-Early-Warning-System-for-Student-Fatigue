import pandas as pd
import streamlit as st

from components import charts
from components.ui import LEVEL_COLOR, current_input, level_badge
from fuzzy_model import INPUT_VARIABLES, OUTPUT_TERMS_ORDER, category_thresholds, infer
from recommendation import FACT_ALPHA_CUT, main_contributing_factors, recommend

st.title("Fatigue Assessment")
st.caption("Isi berdasarkan rata-rata hari biasa dalam 7 hari terakhir.")

prev = current_input()
with st.form("assessment_form", border=True):
    c1, c2 = st.columns(2, gap="large")
    sleep = c1.slider(":material/bedtime: Durasi tidur (jam per hari)", 0.0, 12.0,
                      float(prev["sleep_hours"]), step=0.5)
    assign = c2.slider(":material/assignment: Tugas belum selesai (tenggat 7 hari ke depan)", 0, 15,
                       int(prev["outstanding_assignments"]), step=1)
    screen = c1.slider(":material/smartphone: Screen time non-akademik (jam per hari)", 0.0, 16.0,
                       float(prev["screen_time_hours"]), step=0.5,
                       help="Hiburan, media sosial, game. Bukan untuk belajar.")
    meals = c2.slider(":material/restaurant: Makan utama per hari", 0.0, 6.0,
                      float(prev["meals_per_day"]), step=0.5)
    submitted = st.form_submit_button("Analisis sekarang", type="primary", icon=":material/search:")

if submitted:
    st.session_state.assessed = {"sleep_hours": float(sleep), "outstanding_assignments": float(assign),
                                 "screen_time_hours": float(screen), "meals_per_day": float(meals)}

if st.session_state.assessed is None:
    st.info("Atur nilai input di atas lalu tekan **Analisis sekarang**.")
    st.stop()

res = infer(st.session_state.assessed)
rec = recommend(res.fatigue_level, res.risk_degrees)
t_low, t_high = category_thresholds()

tab_sum, tab_fuzzy, tab_kb = st.tabs([":material/speed: Hasil ringkas",
                                      ":material/functions: Detail fuzzy",
                                      ":material/account_tree: Forward chaining trace"])

# ---------------------------------------------------------------------------
with tab_sum:
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.markdown(f"**Fatigue level** &nbsp; {level_badge(res.fatigue_level)}", unsafe_allow_html=True)
        st.plotly_chart(charts.fatigue_gauge(res.fatigue_index, res.fatigue_level), width="stretch",
                        config={"displayModeBar": False})
        st.caption(f"LOW < {t_low:.2f} ≤ MODERATE < {t_high:.2f} ≤ HIGH. "
                   "Dengan centroid, indeks yang dapat dicapai kira-kira 17-83.")
    with right:
        st.subheader("Faktor kontribusi utama")
        factors = main_contributing_factors(res.risk_degrees)
        if factors:
            st.plotly_chart(charts.factor_bars(factors, height=90 + 40 * len(factors)), width="stretch",
                            config={"displayModeBar": False})
            st.caption(f"Nilai = derajat keanggotaan pada label risiko tiap input. "
                       f"Faktor ≥ {FACT_ALPHA_CUT} menjadi fakta di knowledge base.")
        else:
            st.success("Tidak ada faktor risiko yang aktif (semua derajat risiko = 0).",
                       icon=":material/check_circle:")

        st.subheader("Rekomendasi")
        with st.container(border=True):
            for _, text in rec.actions:
                st.markdown(f"- {text}")
        st.caption("Saran umum untuk kesejahteraan mahasiswa, bukan saran medis.")

# ---------------------------------------------------------------------------
with tab_fuzzy:
    with st.expander("1. Fuzzifikasi", expanded=True):
        rows = []
        for var, degs in res.memberships.items():
            active = ", ".join(f"{t} = {d:.2f}" for t, d in degs.items() if d > 0)
            rows.append({"input": INPUT_VARIABLES[var]["label"], "value": res.inputs[var],
                         "active labels": active})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        cols = st.columns(2)
        for i, var in enumerate(INPUT_VARIABLES):
            cols[i % 2].plotly_chart(charts.input_mf(var, res.inputs[var]), width="stretch",
                                     config={"displayModeBar": False})

    fired = [r for r in res.rule_strengths if r["strength"] > 0]
    with st.expander(f"2. Evaluasi aturan ({len(fired)} dari {len(res.rule_strengths)} aturan aktif)",
                     expanded=True):
        st.caption("AND antar input = min, OR antar label satu input = bounded sum min(1, a+b). "
                   "Hanya aturan dengan firing strength > 0 yang ditampilkan.")
        show_all = st.toggle("Tampilkan semua aturan", value=False)
        shown = res.rule_strengths if show_all else fired
        st.dataframe(pd.DataFrame([{"rule": r["id"], "strength": round(r["strength"], 3),
                                    "then fatigue is": r["then"], "rule text": r["text"]} for r in shown]),
                     hide_index=True, width="stretch",
                     column_config={"strength": st.column_config.ProgressColumn(
                         "strength", min_value=0.0, max_value=1.0, format="%.3f")})

    with st.expander("3. Implikasi dan agregasi", expanded=True):
        cols = st.columns(3)
        for col, t in zip(cols, OUTPUT_TERMS_ORDER):
            col.metric(f"Clip level {t}", f"{res.output_levels[t]:.2f}")
        st.plotly_chart(charts.output_mf(res), width="stretch", config={"displayModeBar": False})

    with st.expander("4. Defuzzifikasi (centroid)", expanded=True):
        st.latex(r"z^* = \frac{\sum_i y_i\,\mu_{agg}(y_i)}{\sum_i \mu_{agg}(y_i)} = "
                 + f"{res.fatigue_index:.2f}")
        st.markdown(f"Level = label output dengan keanggotaan tertinggi pada z* → "
                    f"<b style='color:{LEVEL_COLOR[res.fatigue_level]}'>{res.fatigue_level}</b>",
                    unsafe_allow_html=True)

# ---------------------------------------------------------------------------
with tab_kb:
    st.markdown("**Fakta awal**")
    st.code("\n".join(rec.initial_facts), language=None)
    st.caption(f"Faktor risiko dijadikan fakta bila derajat keanggotaannya ≥ {FACT_ALPHA_CUT}.")

    st.markdown("**Jejak inferensi**")
    if rec.trace:
        for it in sorted({s["iteration"] for s in rec.trace}):
            with st.container(border=True):
                st.markdown(f"Iterasi {it}")
                for s in (s for s in rec.trace if s["iteration"] == it):
                    st.markdown(f"`{s['rule']}` &nbsp; {s['premises']} → **{s['derived']}**")
        st.caption(f"Titik tetap tercapai pada iterasi {max(s['iteration'] for s in rec.trace) + 1} "
                   "(tidak ada fakta baru).")
    else:
        st.write("Tidak ada aturan yang terpicu.")

    st.markdown("**Rekomendasi akhir**")
    for aid, text in rec.actions:
        st.markdown(f"- `{aid}`: {text}")
