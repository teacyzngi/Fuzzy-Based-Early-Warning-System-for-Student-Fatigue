import streamlit as st

from components.ui import DISCLAIMER
from fuzzy_model import INPUT_VARIABLES, RULES
from recommendation import KB_RULES

st.title("Early Warning System for Student Fatigue")
st.caption("Mamdani fuzzy inference + forward-chaining knowledge base")
st.warning(DISCLAIMER, icon=":material/warning:")

st.write(
    "Sistem prototype untuk memperkirakan tingkat kelelahan mahasiswa berdasarkan "
    "empat indikator aktivitas harian: durasi tidur, jumlah tugas yang belum selesai, "
    "screen time non-akademik, dan frekuensi makan."
)

c1, c2, c3 = st.columns(3)
c1.metric("Input variables", len(INPUT_VARIABLES), border=True)
c2.metric("Fuzzy rules", len(RULES), border=True)
c3.metric("Knowledge-base rules", len(KB_RULES), border=True)

st.subheader("Alur inferensi")
st.graphviz_chart("""
digraph {
  rankdir=LR; bgcolor="transparent";
  node [shape=box, style="rounded,filled", fillcolor="#EFF6FF", color="#2563EB",
        fontname="Helvetica", fontsize=11];
  edge [color="#64748B"];
  input [label="4 crisp inputs"];
  fuzz  [label="Fuzzification\\n(trapezoid MF)"];
  rules [label="Rule evaluation\\n(11 rules, min / bounded sum)"];
  agg   [label="Implication + aggregation\\n(clip, max)"];
  defz  [label="Defuzzification\\n(centroid)"];
  kb    [label="Forward chaining\\n(13 Horn clauses)"];
  out   [label="Fatigue index, level,\\nrecommendations", fillcolor="#DBEAFE"];
  input -> fuzz -> rules -> agg -> defz -> kb -> out;
}
""", width="stretch")

c1, c2, c3 = st.columns(3)
with c1.container(border=True):
    st.markdown("**1. Fuzzy inference (Mamdani)**")
    st.caption("Fuzzifikasi, 11 aturan IF-THEN, agregasi, dan centroid menghasilkan Fatigue Index 0-100.")
with c2.container(border=True):
    st.markdown("**2. Knowledge base (forward chaining)**")
    st.caption("Level kelelahan dan faktor risiko menjadi fakta; aturan Horn menurunkan rekomendasi "
               "beserta jejak inferensinya.")
with c3.container(border=True):
    st.markdown("**3. Evaluasi survei**")
    st.caption("CSV survei dibandingkan dengan fatigue self-report (korelasi peringkat, "
               "kesesuaian kategori).")

if st.button("Mulai assessment", type="primary", icon=":material/arrow_forward:"):
    st.switch_page("pages/assessment.py")
