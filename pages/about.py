import streamlit as st

from components.ui import DISCLAIMER, REPO_URL

st.title("About & Limitations")
st.warning(DISCLAIMER, icon=":material/warning:")

st.subheader("Metodologi")
st.markdown("""
| Langkah | Pilihan |
|---|---|
| Fungsi keanggotaan | Trapesium/segitiga; tiap input partisi Ruspini (derajat berjumlah 1) |
| AND (antar input) | min |
| OR (label satu input) | bounded sum `min(1, a+b)` |
| Implikasi | min (clipping) |
| Agregasi | max |
| Defuzzifikasi | centroid pada 0-100 (langkah 0.1) |
| Rekomendasi | forward chaining pada knowledge base Horn clause |

Hanya inti tidur normal 7-9 jam yang berasal dari referensi (National Sleep Foundation, 2015).
Parameter lain adalah asumsi desain tim. Detail lengkap ada di `docs/DESIGN.md`.
""")

st.subheader("Keterbatasan")
st.markdown("""
- Sampel survei kecil dan berbasis self-report.
- Fatigue self-report adalah acuan subjektif, bukan ground truth.
- Aturan dan sebagian besar fungsi keanggotaan dirancang tim dan belum tentu tergeneralisasi.
- Tidak ada validasi klinis.
- Hanya empat variabel input.
- Centroid membatasi indeks pada kisaran 17-83, membuat nilai mengelompok, dan menimbulkan
  penurunan kecil non-monoton (≤ 1.8 poin) di zona transisi.
- Rekomendasi bersifat saran umum, bukan saran medis.
""")

st.subheader("Anggota tim")
st.markdown("""
| Nama | NIM | Peran |
|---|---|---|
| … | … | … |
| … | … | … |
| … | … | … |
""")

st.subheader("Referensi")
st.markdown("""
- Hirshkowitz, M., et al. (2015). National Sleep Foundation's sleep time duration recommendations:
  methodology and results summary. *Sleep Health*, 1(1), 40-43.
- Mamdani, E. H., & Assilian, S. (1975). An experiment in linguistic synthesis with a fuzzy logic
  controller. *International Journal of Man-Machine Studies*, 7(1), 1-13.
- Zadeh, L. A. (1965). Fuzzy sets. *Information and Control*, 8(3), 338-353.
- Russell, S., & Norvig, P. (2021). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson.
""")

st.caption(f"Final Project Kecerdasan Buatan, DTETI Universitas Gadjah Mada (2026). "
           f"[Repositori GitHub]({REPO_URL})")
