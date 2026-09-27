# Design Document — Fuzzy-Based Early Warning System untuk Tingkat Kelelahan Mahasiswa

Dokumen ini menjawab Part 1–19 dari brief kelompok. Semua angka hasil (test case, monotonicity, contoh perhitungan) **dihasilkan oleh kode di repo ini**, bukan tebakan. Jalankan ulang `python run_test_cases.py` dan `python -m pytest -q` setiap kali rule atau membership function diubah.

Label sumber parameter yang dipakai di seluruh dokumen:

| Label | Arti |
|---|---|
| **[DATA-DERIVED]** | Diturunkan dari data survei kelompok. **Saat ini belum ada**, karena survei belum dilakukan. |
| **[REFERENCE-DERIVED]** | Didukung referensi terpublikasi yang dicantumkan di bagian Referensi. |
| **[DESIGN ASSUMPTION]** | Keputusan desain kelompok. Bukan fakta medis dan harus bisa dipertanggungjawabkan secara lisan. |

---

## Kelayakan algoritma

Fuzzy Logic diajarkan di **Lecture 6**, sehingga termasuk klausul Section 3 PDF (*"Any further algorithm introduced later in the course"*).

Selain itu, recommendation layer diimplementasikan sebagai **knowledge-based system dengan forward chaining (Lecture 4)**: knowledge base Horn clause, iterasi sampai fixed point, dan inference trace. Menurut Section 3, menggabungkan lebih dari satu algoritma dinilai sebagai **extra depth**. Framing untuk presentasi: *"Fuzzy inference (Lecture 6) menghitung indeks; forward chaining (Lecture 4) menurunkan rekomendasi."*

Pastikan judul di report sama persis dengan yang terdaftar di ugm.id/aitbproject (D1).

---

## PART 1 — Requirements dari PDF dan pemenuhannya

| Requirement (sumber di PDF) | Isi requirement | Cara proyek ini memenuhi |
|---|---|---|
| Real-world problem (R2, rubric "Realism" 15%) | Kasus nyata, bukan latihan sintetis | Kelelahan mahasiswa akibat kurang tidur, beban tugas, screen time, dan pola makan adalah masalah kampus nyata. Input diambil dari kebiasaan yang bisa dilaporkan mahasiswa. |
| Algorithm implementation (R2, Section 3) | Implementasi jelas dari algoritma kuliah | Mamdani FIS (Lecture 6) ditulis dari nol dengan NumPy (`fuzzy_model.py`) + forward chaining (Lecture 4, `recommendation.py`) sebagai extra depth. |
| Real data/rules (R2, D3) | Dataset atau rule set nyata beserta asal-usulnya | Rule set disusun kelompok (dilabeli [DESIGN ASSUMPTION]). Parameter tidur didukung referensi NSF. Data survei primer dipakai untuk evaluasi (Part 6). |
| Problem formalization (D3, rubric 15%) | Formalisasi dalam istilah kuliah | Variabel linguistik, membership function, rule base, operator inference. Rekomendasi diformalkan sebagai KB + forward chaining (Part 2–5). |
| Design justification (R2, R3) | Alasan setiap pilihan desain | Setiap parameter berlabel sumber, setiap rule punya alasan (Part 3–4). |
| Working system/demo (rubric 20%) | Sistem yang bisa dipakai non-programmer | Aplikasi web Streamlit berisi 5 halaman (Part 8–9). |
| Results (D3) | Hasil beserta screenshot | Test case (Part 13), evaluasi survei (Part 14), dan screenshot aplikasi di folder `screenshots/`. |
| Limitations (D3) | Diskusi keterbatasan | Part 15. |
| GitHub repository (D2) | Public, README cara menjalankan | Repo ini, README.md. |
| Report maks. 6 halaman (D3) | PDF, memuat link repo dan seluruh isi di atas | Struktur di Part 16. |
| Presentation (D4) | File .pptx | Struktur di Part 17. |
| AI-tool policy (R3, Section 6) | Inti algoritma harus dipahami dan bisa dipertanggungjawabkan kelompok | Seluruh keputusan desain terlihat dan berlabel. **Kelompok wajib meninjau, bisa mengubah, dan memahami setiap rule/parameter** (lihat Part 12, "5 Things"). |
| Cite everything (Section 6) | Cantumkan semua sumber eksternal | Bagian Referensi dokumen ini. |
| Deliverable | Tepat 2 file ke ELOK: report PDF + .pptx, deadline 30 Sep 2026 23.59 WIB | — |

---

## PART 2 — Definisi sistem

1. **Problem statement.** Mahasiswa sering tidak menyadari bahwa kombinasi kurang tidur, tumpukan tugas, screen time hiburan yang tinggi, dan makan tidak teratur sedang menumpuk. Kondisi ini baru disadari ketika performa atau kesejahteraan sudah menurun. Indikator-indikator ini bersifat samar (apakah 6,5 jam tidur itu "kurang"?), sehingga threshold tajam (crisp) kurang cocok.
2. **Target users.** Mahasiswa S1 yang ingin memantau diri secara mandiri. Pengguna sekunder: dosen wali atau organisasi mahasiswa sebagai alat edukasi, **bukan** untuk menilai atau menyaring mahasiswa.
3. **Real-world scenario.** Di minggu padat UTS, seorang mahasiswa membuka aplikasi dan memasukkan rata-rata tidur 5,5 jam, 7 tugas yang deadline-nya dalam 7 hari, 6 jam screen time hiburan, dan 2 kali makan. Sistem memberi indeks, level, faktor penyumbang, serta saran umum (misalnya memprioritaskan tugas terdekat dan menjaga jam tidur).
4. **System objective.** Menghasilkan indeks kelelahan 0–100 yang *monoton terhadap risiko* (input memburuk → indeks tidak turun, dengan pengecualian kecil yang terukur di Part 14), dapat dijelaskan langkah demi langkah, dan disertai rekomendasi umum yang bisa ditelusuri.
5. **Inputs.** `sleep_hours` (0–12), `outstanding_assignments` (0–15, tugas yang deadline-nya dalam 7 hari), `screen_time_hours` (0–16, **non-akademik**), `meals_per_day` (0–6). Nilai di luar rentang dipotong (clip) ke batas.
6. **Outputs.** Fatigue Index (0–100), Fatigue Level (LOW/MODERATE/HIGH), faktor penyumbang utama, daftar rekomendasi, dan inference trace.
7. **Fuzzy inference pipeline.** Mamdani (lihat diagram di bawah).
8. **Recommendation mechanism.** Level + fakta risiko (derajat keanggotaan ≥ 0,5) diproses oleh forward chaining atas 13 Horn clause, menghasilkan aksi.
9. **Limitations.** Lihat Part 15.

**Keputusan desain: screen time = non-akademik [DESIGN ASSUMPTION].** Brief menyebut "screen time aktif". Kalau screen time belajar ikut dihitung, input ini akan tumpang tindih dengan beban tugas (double counting). Karena itu pertanyaan survei **harus** menyebut "di luar kegiatan akademik". Jika kelompok memilih total screen time, parameter MF-nya harus digeser.

### Diagram konseptual (setiap tahap = fungsi nyata di kode)

```
User Input (4 angka)                         app.py: page_assessment()
   ↓  clamp ke rentang                       fuzzy_model.clamp_inputs()
Input Fuzzification                          fuzzy_model.fuzzify()          → trapmf()
   ↓  derajat keanggotaan 12 label
Fuzzy Rule Evaluation (AND=min, OR=bounded sum) fuzzy_model.evaluate_rules()   → RULES (11)
   ↓  firing strength per rule
Implication (min/clipping) + Rule Aggregation (max)  fuzzy_model.implicate_and_aggregate()
   ↓  satu himpunan fuzzy output
Defuzzification (centroid)                   fuzzy_model.defuzzify_centroid()
   ↓
Fatigue Index 0–100                          FuzzyResult.fatigue_index
   ↓
Fatigue Level (argmax membership output)     fuzzy_model.categorize()
   ↓  + fakta risiko (α-cut 0,5)
Recommendation (forward chaining)            recommendation.facts_from_fuzzy() → forward_chain()
```

---

## PART 3 — Desain sistem fuzzy

### Prinsip desain yang dipakai untuk semua input

- **Trapesium untuk label ujung (shoulder), trapesium atau segitiga untuk label tengah** [DESIGN ASSUMPTION]. Bentuk linear mudah dihitung manual saat oral defense dan cukup untuk data berskala kasar (jam, jumlah).
- **Ruspini partition**: pada setiap nilai, paling banyak 2 label aktif dan **jumlah derajatnya selalu 1** [DESIGN ASSUMPTION, diuji di `test_inputs_are_ruspini_partitions`]. Contohnya, tidur 6,5 jam = 0,5 LOW + 0,5 NORMAL. Properti ini membuat OR dengan bounded sum sama persis dengan "NOT label lain" (lihat Part 5).
- **Overlap** selalu terletak pada satu segmen miring bersama dengan titik silang di derajat 0,5.

Notasi: `trap(a, b, c, d)` = naik dari a ke b, bernilai 1 di [b, c], turun dari c ke d.

### A. Sleep Hours (jam/hari, rata-rata 7 hari terakhir) — universe 0–12

| Label | Parameter | Sumber |
|---|---|---|
| LOW | trap(0, 0, 6, 7) | Plateau ≤ 6 jam: sejalan dengan NSF (<6 jam "not recommended" untuk 18–25 th) [REFERENCE-DERIVED]. Lebar slope 1 jam [DESIGN ASSUMPTION] |
| NORMAL | trap(6, 7, 9, 10) | Inti 7–9 jam = rekomendasi NSF untuk dewasa muda 18–25 th [REFERENCE-DERIVED] |
| HIGH | trap(9, 10, 12, 12) | Batas 10 jam [DESIGN ASSUMPTION]; NSF memberi rentang 10–11 jam sebagai "may be appropriate" |

- Overlap: 6–7 (LOW↔NORMAL), 9–10 (NORMAL↔HIGH). Kedua zona transisi ini kira-kira sesuai dengan pita "may be appropriate" di NSF (6 jam dan 10–11 jam). Ini hanya dipakai sebagai *inspirasi posisi*; bentuk linearnya tetap asumsi kelompok.
- Universe 0–12: di atas 12 jam dianggap sama dengan 12 (clip).
- **HIGH diperlakukan sama dengan NORMAL di rule base** [DESIGN ASSUMPTION]. Kelompok tidak punya dasar untuk mengklaim bahwa tidur panjang menambah atau mengurangi kelelahan, jadi tidak ada klaim medis soal oversleeping. Label HIGH tetap didefinisikan agar keputusan ini eksplisit dan terlihat di fuzzifikasi.
- **Catatan jujur:** NSF adalah rekomendasi durasi tidur untuk kesehatan, bukan model kelelahan. Referensi ini hanya mendukung "berapa jam yang dianggap cukup", bukan besarnya kontribusi tidur ke indeks.

### B. Outstanding Assignments (tugas dengan deadline ≤ 7 hari) — universe 0–15

| Label | Parameter | Sumber |
|---|---|---|
| FEW | trap(0, 0, 2, 4) | [DESIGN ASSUMPTION] |
| MODERATE | trap(2, 4, 6, 8) | [DESIGN ASSUMPTION] |
| MANY | trap(6, 8, 15, 15) | [DESIGN ASSUMPTION] |

- Overlap 2–4 dan 6–8, titik silang di 3 dan 7 tugas.
- Alasan: dengan beban 18–24 SKS (sekitar 7–9 mata kuliah), 4–6 tugas per minggu adalah minggu "biasa" dan ≥ 8 dianggap berat. Ini **murni asumsi kelompok**. Setelah survei ada, bandingkan dengan tertil data di halaman *Survey Data* (tabel "Membership functions vs data").
- Jendela 7 hari dipilih supaya angka ini bermakna. "Jumlah tugas" tanpa batas waktu tidak bisa dibandingkan antar mahasiswa.

### C. Screen Time non-akademik (jam/hari) — universe 0–16

| Label | Parameter | Sumber |
|---|---|---|
| LOW | trap(0, 0, 2, 4) | [DESIGN ASSUMPTION] |
| MODERATE | trap(2, 4, 6, 8) | [DESIGN ASSUMPTION] |
| HIGH | trap(6, 8, 16, 16) | [DESIGN ASSUMPTION] |

- Overlap 2–4 dan 6–8. **Tidak ada cut-off klinis untuk dewasa yang diklaim.** Angka ini adalah pilihan kelompok untuk penggunaan hiburan. Validasi hanya bisa lewat data (Part 6).

### D. Meals per Day — universe 0–6

| Label | Parameter | Sumber |
|---|---|---|
| LOW | trap(0, 0, 1, 3) | [DESIGN ASSUMPTION] |
| ADEQUATE | trap(1, 3, 3, 5) (segitiga, puncak 3) | Puncak 3 kali/hari = kebiasaan umum [DESIGN ASSUMPTION], **bukan klaim gizi** |
| HIGH | trap(3, 5, 6, 6) | [DESIGN ASSUMPTION] |

- 2 kali makan = 0,5 LOW + 0,5 ADEQUATE; 4 kali = 0,5 ADEQUATE + 0,5 HIGH.
- HIGH bersifat netral di rule base (tidak ada klaim bahwa sering makan menambah atau mengurangi kelelahan).

### Output — Fatigue Index 0–100

| Label | Parameter | Sumber |
|---|---|---|
| LOW | trap(0, 0, 20, 45) | [DESIGN ASSUMPTION] |
| MODERATE | trap(30, 50, 50, 70) (segitiga) | [DESIGN ASSUMPTION] |
| HIGH | trap(55, 80, 100, 100) | [DESIGN ASSUMPTION] |

- Dibuat simetris terhadap 50 supaya "tengah" bermakna netral.
- Konsekuensi centroid: indeks **tidak pernah mencapai 0 atau 100**. Minimum = 17,03 (hanya LOW aktif penuh) dan maksimum = 82,97 (hanya HIGH aktif penuh). Ini sifat defuzzifikasi centroid, bukan bug. Sampaikan di presentasi.

---

## PART 4 — Fuzzy rule base (11 rules)

**Konvensi:** di dalam satu variabel beberapa label digabung dengan **OR**; antar variabel digabung dengan **AND**. Tidak ada OR antar variabel.

### Struktur

- **Tabel dasar tidur × beban tugas (R1–R4).** Keduanya dianggap penggerak utama.

  | | FEW | MODERATE | MANY |
  |---|---|---|---|
  | **LOW sleep** | MODERATE (R2) | HIGH (R1) | HIGH (R1) |
  | **NORMAL/HIGH sleep** | LOW (R4\*) | LOW (R4\*) | MODERATE (R3) |

  \* R4 (→ LOW) hanya berlaku jika screen time **tidak** HIGH dan makan **tidak** LOW.
- **Eskalasi (R5–R11).** Screen time tinggi atau makan kurang menaikkan level satu tingkat, dan **tidak pernah** menurunkannya.

| ID | IF | THEN | Alasan |
|---|---|---|---|
| R1 | sleep LOW AND assignments (MODERATE or MANY) | HIGH | Kurang tidur + beban nyata = ruang pemulihan kecil |
| R2 | sleep LOW AND assignments FEW | MODERATE | Kurang tidur saja sudah tanda peringatan |
| R3 | sleep (NORMAL or HIGH) AND assignments MANY | MODERATE | Tidur cukup, tetapi beban berat tetap menjadi beban |
| R4 | sleep (NORMAL or HIGH) AND assignments (FEW or MODERATE) AND screen (LOW or MODERATE) AND meals (ADEQUATE or HIGH) | LOW | LOW hanya jika **keempat** indikator baik |
| R5 | screen HIGH AND sleep (NORMAL or HIGH) AND assignments (FEW or MODERATE) | MODERATE | Screen time tinggi menaikkan situasi yang tadinya LOW |
| R6 | screen HIGH AND assignments MANY | HIGH | Screen time tinggi di atas beban berat |
| R7 | screen HIGH AND sleep LOW | HIGH | Screen time tinggi + kurang tidur |
| R8 | meals LOW AND sleep (NORMAL or HIGH) AND assignments (FEW or MODERATE) | MODERATE | Makan kurang menaikkan situasi yang tadinya LOW |
| R9 | meals LOW AND assignments MANY | HIGH | Makan kurang di atas beban berat |
| R10 | meals LOW AND sleep LOW | HIGH | Makan kurang + kurang tidur |
| R11 | screen HIGH AND meals LOW | HIGH | Dua faktor gaya hidup sekaligus |

Semua rule berlabel **[DESIGN ASSUMPTION]**. Rule disusun kelompok berdasarkan penalaran umum, bukan dari studi klinis.

### Kenapa 11 rule, bukan 15–30?

Tabel penuh 3⁴ = 81 kombinasi terlalu banyak untuk dijelaskan. Rule yang konsekuennya sama pada label bertetangga **sengaja digabung dengan OR** (misalnya R1 = dua sel tabel). Penggabungan ini bukan sekadar menghemat. Pada versi awal dengan rule terpisah, uji monotonicity menemukan indeks *turun* hingga 4,7 poin ketika beban tugas bertambah. Penyebabnya adalah "max-dip": di titik silang, dua rule dengan konsekuen sama masing-masing hanya 0,5, dan aggregation max tidak menjumlahkannya (lihat Part 5). 11 rule ini secara implisit mencakup seluruh 81 kombinasi label.

### Kombinasi yang tidak punya rule eksplisit

Tidak ada celah. R1–R3 bersama R4/R5/R8 menutup setiap kombinasi tidur × beban tugas. Setiap kali R4 mati karena screen HIGH atau meals LOW, R5 atau R8 (atau R6/R7/R9/R10) mengambil alih. Hal ini diuji otomatis di `test_rule_base_is_complete` (28.561 kombinasi grid, selalu ada rule yang aktif). Label netral (sleep HIGH, meals HIGH, screen LOW/MODERATE) tidak butuh rule sendiri karena tercakup lewat OR.

---

## PART 5 — Metode inferensi: Mamdani

| Tahap | Pilihan | Alasan |
|---|---|---|
| Fuzzification | `trapmf` pada setiap label | Mengubah angka crisp menjadi derajat keanggotaan [0, 1] |
| AND (antar variabel) | **min** | Standar Mamdani: sebuah rule hanya sekuat kondisi terlemahnya |
| OR (dalam satu variabel) | **bounded sum** min(1, a+b) | Karena input berupa Ruspini partition, "FEW or MODERATE" = 1 − μ(MANY) persis. Jika memakai **max**, nilainya turun ke 0,5 di titik silang dan membuat indeks tidak monoton (terbukti di uji awal). Ini keputusan desain yang dibuktikan dengan data uji |
| Firing strength | nilai AND dari antecedent | — |
| Implication | **min** (clipping) | Himpunan konsekuen dipotong setinggi firing strength |
| Aggregation | **max** | Standar Mamdani; himpunan yang dipotong digabung per titik |
| Defuzzification | **centroid** atas universe 0–100 dengan langkah 0,1 (1001 titik) | Memakai seluruh bentuk himpunan output. Hasil kontinu dan halus |
| Level | label output dengan membership tertinggi pada indeks; seri → label lebih parah | Threshold diturunkan dari MF output: **36,67** dan **63,33** |

**Kenapa Mamdani (bukan Sugeno)?** Konsekuen berupa label linguistik (LOW/MODERATE/HIGH) yang bisa dibaca dan digambar. Ini penting untuk explainability dan oral defense. Sugeno lebih efisien, tetapi konsekuennya fungsi atau konstanta yang kurang intuitif. Data survei juga tidak cukup untuk mengestimasi koefisien Sugeno.

**Kenapa implementasi sendiri (bukan scikit-fuzzy)?** Setiap tahap menjadi fungsi terpisah yang bisa ditunjuk saat oral defense, dan dependency berkurang. Kebenaran implementasi dicek dengan cara independen: centroid dari kode dibandingkan dengan integrasi numerik `scipy.integrate.quad` (selisih < 0,1; `test_centroid_matches_numerical_integration`).

### Contoh perhitungan manual A — input dari brief

**Input:** Sleep = 5 jam, Assignments = 6, Screen = 8 jam, Meals = 2/hari

**1. Membership degree**

| Variabel | Perhitungan | Hasil |
|---|---|---|
| Sleep 5 | LOW trap(0,0,6,7): 5 ≤ 6 → plateau | LOW = 1, NORMAL = 0, HIGH = 0 |
| Assign 6 | MODERATE trap(2,4,6,8): 6 = c → plateau; MANY trap(6,8,…): 6 = a → 0 | FEW = 0, MOD = 1, MANY = 0 |
| Screen 8 | HIGH trap(6,8,16,16): 8 = b → 1 | LOW = 0, MOD = 0, HIGH = 1 |
| Meals 2 | LOW: (3−2)/(3−1) = 0,5; ADEQUATE: (2−1)/(3−1) = 0,5 | LOW = 0,5, ADEQ = 0,5, HIGH = 0 |

**2–3. Rule aktif dan firing strength**

| Rule | Perhitungan | Strength | → |
|---|---|---|---|
| R1 | min(LOW=1, MOD+MANY = 1+0 = 1) | **1,00** | HIGH |
| R7 | min(screen HIGH=1, sleep LOW=1) | **1,00** | HIGH |
| R10 | min(meals LOW=0,5, sleep LOW=1) | **0,50** | HIGH |
| R11 | min(screen HIGH=1, meals LOW=0,5) | **0,50** | HIGH |
| Lainnya | ada antecedent bernilai 0 (misalnya R4: sleep NORMAL/HIGH = 0) | 0 | — |

**4. Aggregated output.** Level clip per label: LOW = 0, MODERATE = 0, HIGH = max(1; 1; 0,5; 0,5) = **1**. Himpunan output = seluruh trapesium HIGH (55, 80, 100, 100).

**5. Defuzzifikasi (centroid).**
- Secara analitis: segitiga 55–80 (luas 12,5; titik berat 71,67) + persegi panjang 80–100 (luas 20; titik berat 90) → (12,5×71,67 + 20×90)/32,5 = **82,95**.
- Kode (langkah 0,1) = **82,97**. Selisihnya berasal dari diskretisasi.

**6. Kategori:** 82,97 ≥ 63,33 → **HIGH**.

**7. Rekomendasi (forward chaining).**
- Fakta awal: `level_high`, `short_sleep` (μ=1), `high_screen_time` (μ=1), `irregular_meals` (μ=0,5 ≥ 0,5). `heavy_workload` tidak menjadi fakta karena μ(MANY)=0.
- Iterasi 1: K2 → `elevated_fatigue`, K4 → `multiple_risk_factors`, K9 → `act_recovery_break`.
- Iterasi 2: K7 → `act_reduce_non_essential`, K11 → `act_protect_sleep`, K12 → `act_regular_meals`, K13 → `act_seek_support`.
- Iterasi 3: tidak ada fakta baru, sehingga berhenti (fixed point).

### Contoh perhitungan manual B — overlap dan beberapa output (disarankan dipakai saat oral defense)

Contoh A hanya menghasilkan satu himpunan output. Contoh B memperlihatkan OR, AND, dan aggregation sekaligus.

**Input:** Sleep = 7,5; Assignments = 7; Screen = 4; Meals = 2,5

| Variabel | Membership |
|---|---|
| Sleep 7,5 | NORMAL = 1 |
| Assign 7 | MODERATE = (8−7)/2 = 0,5; MANY = (7−6)/2 = 0,5 |
| Screen 4 | MODERATE = 1 (LOW = (4−4)/2 = 0) |
| Meals 2,5 | LOW = (3−2,5)/2 = 0,25; ADEQUATE = (2,5−1)/2 = 0,75 |

| Rule | Perhitungan | Strength | → |
|---|---|---|---|
| R3 | min(NORMAL+HIGH = 1, MANY = 0,5) | 0,50 | MODERATE |
| R4 | min(sleep 1, FEW+MOD = 0,5, screen LOW+MOD = 1, meals ADEQ+HIGH = 0,75) | 0,50 | LOW |
| R8 | min(meals LOW 0,25, sleep 1, FEW+MOD 0,5) | 0,25 | MODERATE |
| R9 | min(meals LOW 0,25, MANY 0,5) | 0,25 | HIGH |

**Aggregation (max per label):** LOW = 0,50; MODERATE = max(0,50; 0,25) = 0,50; HIGH = 0,25.

**Centroid manual dengan sampel setiap 10 poin** (cara papan tulis):

| y | 0 | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| μ(y) | 0,5 | 0,5 | 0,5 | 0,5 | 0,5 | 0,5 | 0,5 | 0,25 | 0,25 | 0,25 | 0,25 |

Σμ = 4,5 ; Σ y·μ = 190 → centroid ≈ 190 / 4,5 = **42,22**.

Kode memakai 1001 sampel dan menghasilkan **42,89**. Perbedaan 0,67 berasal dari sampel yang lebih kasar. Metodenya sama, hanya resolusinya berbeda.

**Kategori:** 36,67 ≤ 42,89 < 63,33 → **MODERATE**.

**Rekomendasi:**
- Fakta awal: `level_moderate`, `heavy_workload` (μ(MANY) = 0,5 ≥ 0,5).
- Iterasi 1: K1 → `elevated_fatigue`, K6 → `act_short_rest`.
- Iterasi 2: K8 → `act_prioritize_urgent`.

Gambar himpunan teragregasi untuk contoh A: `docs/figures/worked_example_aggregation.png`.

---

## PART 6 — Hubungan survei dengan model fuzzy

| | A. Survei untuk menetapkan/menyesuaikan MF | B. Survei untuk mengevaluasi output |
|---|---|---|
| Kebutuhan data | Besar (distribusi stabil per variabel, idealnya ratusan) | Kecil sampai sedang (n ≈ 30 sudah bisa menghasilkan korelasi dengan CI lebar) |
| Risiko | Overfitting ke sampel kecil; sirkular jika data yang sama juga dipakai untuk evaluasi | Kesimpulannya terbatas: "searah atau tidak" |
| Kelayakan dalam 2–3 hari | Rendah | **Tinggi** |

**Keputusan: pendekatan B sebagai pendekatan utama.** Survei dipakai untuk **evaluasi**, bukan "training". Tidak ada parameter yang dipelajari dari data.

A dipakai hanya sebagai **sanity check** (tanpa mengubah parameter): halaman *Survey Data* menampilkan titik silang MF di samping tertil data (P33/P67). Jika kelompok memutuskan mengubah MF berdasarkan data, ikuti aturan berikut:
1. Ubah **sebelum** melihat korelasi dengan self-report.
2. Label parameter itu menjadi [DATA-DERIVED] dengan menyebut statistik yang dipakai (misalnya "crossover = median data").
3. Idealnya bagi data menjadi dua: separuh untuk penyesuaian, separuh untuk evaluasi. Dengan n kecil, laporkan hasilnya secara jujur sebagai eksplorasi.

**Saran praktis:** `git tag v1.0-frozen` sekarang, sebelum data masuk. Dengan begitu kelompok bisa membuktikan bahwa model tidak disetel agar cocok dengan data.

**Self-reported fatigue** (skala 1–10) = **referensi subjektif**, bukan clinical ground truth. Kata "accuracy" sebaiknya tidak dipakai. Gunakan "agreement" atau "korelasi dengan self-report".

### Kuesioner (Google Form) yang disarankan

Semua pertanyaan memakai periode acuan yang sama: **7 hari terakhir**.

1. Kode responden (buat sendiri, misalnya inisial + 2 angka acak). **Jangan minta NIM atau nama.**
2. Rata-rata berapa jam Anda tidur per hari dalam 7 hari terakhir? (angka, boleh desimal)
3. Berapa tugas kuliah yang belum selesai dengan deadline dalam 7 hari ke depan? (angka)
4. Rata-rata berapa jam per hari Anda memakai layar **di luar kegiatan akademik** (hiburan, media sosial, game)? (angka)
5. Rata-rata berapa kali makan utama per hari dalam 7 hari terakhir? (angka)
6. Seberapa lelah Anda merasa dalam 7 hari terakhir? (1 = sama sekali tidak lelah … 10 = sangat lelah)
7. Persetujuan: "Saya setuju data anonim ini dipakai untuk tugas mata kuliah AI." (wajib centang)

Target: n ≥ 30. Ekspor ke CSV dengan header sesuai `data/survey_template.csv`.

---

## PART 7 — Recommendation engine

### Threshold level

Threshold contoh di brief (33/66) **tidak dipakai**. Threshold diturunkan dari MF output: level = label output dengan membership tertinggi pada indeks.

- LOW turun (20→45), MODERATE naik (30→50). Keduanya sama tinggi di 20(45−x) = 25(x−30) → **x = 36,67**.
- MODERATE turun (50→70), HIGH naik (55→80). Keduanya sama tinggi di **x = 63,33**.

Jadi threshold **berasal dari MF output** (konsisten dengan model), sedangkan MF output itu sendiri [DESIGN ASSUMPTION]. Tidak ada threshold yang berasal dari data. Nilai tepat di titik silang masuk ke level yang lebih parah (pilihan early warning) [DESIGN ASSUMPTION].

### Fakta dan knowledge base

Konversi fuzzy → fakta: faktor risiko menjadi fakta jika membership label risikonya **≥ 0,5** (α-cut di titik silang) [DESIGN ASSUMPTION].

| Fakta | Syarat |
|---|---|
| `short_sleep` | μ(sleep LOW) ≥ 0,5 (tidur ≤ 6,5 jam) |
| `heavy_workload` | μ(assignments MANY) ≥ 0,5 (≥ 7 tugas) |
| `high_screen_time` | μ(screen HIGH) ≥ 0,5 (≥ 7 jam) |
| `irregular_meals` | μ(meals LOW) ≥ 0,5 (≤ 2 kali) |
| `level_low` / `level_moderate` / `level_high` | hasil kategori |

Knowledge base (13 Horn clause, [DESIGN ASSUMPTION]):

| ID | IF | THEN |
|---|---|---|
| K1 | level_moderate | elevated_fatigue |
| K2 | level_high | elevated_fatigue |
| K3 | level_high ∧ short_sleep ∧ heavy_workload | multiple_risk_factors |
| K4 | level_high ∧ high_screen_time ∧ irregular_meals | multiple_risk_factors |
| K5 | level_low | act: Maintain current routine |
| K6 | level_moderate | act: Take a short rest |
| K7 | elevated_fatigue ∧ high_screen_time | act: Reduce non-essential activities |
| K8 | elevated_fatigue ∧ heavy_workload | act: Prioritize urgent assignments |
| K9 | level_high | act: Take a longer recovery break |
| K10 | level_high ∧ heavy_workload | act: Consider requesting a deadline extension |
| K11 | elevated_fatigue ∧ short_sleep | act: Protect sleep schedule |
| K12 | elevated_fatigue ∧ irregular_meals | act: Eat at regular times |
| K13 | multiple_risk_factors | act: Seek additional support if the pattern persists |

K1–K4 adalah **kesimpulan antara** sehingga rantai inferensi bisa lebih dari satu langkah. Setiap iterasi forward chaining memeriksa semua rule terhadap fakta di awal iterasi, lalu menambahkan semua kesimpulan baru. Proses berhenti ketika tidak ada fakta baru. Semua saran bersifat **umum (well-being)**. Tidak ada diagnosis, obat, atau istilah klinis. K13 hanya menyarankan bicara dengan orang yang dipercaya, dosen wali, atau layanan konseling kampus jika pola berlanjut.

---

## PART 8 & 9 — Aplikasi web

Streamlit, berjalan lokal, tanpa database, login, API eksternal, atau cloud. Lima halaman lewat sidebar:

| Halaman | Isi |
|---|---|
| Home | Judul, deskripsi, disclaimer *"This system is an academic prototype and is not a medical diagnostic tool."*, ringkasan 3 komponen |
| Fatigue Assessment | 4 number input dalam form + tombol **Analyze Fatigue**. Setelah diklik, otomatis pindah ke Result |
| Result | Indeks XX/100, level berwarna, gauge dengan zona threshold, bar chart faktor penyumbang, rekomendasi, lalu "How this result was computed": tabel membership + plot MF dengan titik input, tabel rule aktif, plot himpunan teragregasi + garis centroid, dan trace forward chaining |
| How the Model Works | Plot semua MF, tabel 11 rule beserta alasan, tabel 13 KB rule, grafik sensitivitas (satu input divariasikan) |
| Survey Data | Upload CSV atau checkbox dataset dummy, validasi baris (baris tidak valid dibuang **dan dilaporkan**), preview, statistik deskriptif, histogram, tabel MF vs tertil data, Spearman ρ + CI bootstrap, category agreement, Cohen's κ, confusion matrix, distribusi level, scatter, dan unduh CSV hasil. **Banner merah otomatis jika data dummy.** |

"Main contributing factors" = derajat keanggotaan label risiko setiap input (μ sleep LOW, μ assignments MANY, μ screen HIGH, μ meals LOW). Nilai ini dibaca langsung dari hasil fuzzifikasi, bukan skor tambahan yang dikarang.

---

## PART 10 — Struktur proyek

```
student-fatigue-fuzzy/
├── app.py                  # UI Streamlit saja
├── fuzzy_model.py          # ★ ALGORITHMIC CORE 1: Mamdani FIS
├── recommendation.py       # ★ ALGORITHMIC CORE 2: forward chaining KB
├── evaluation.py           # validasi survei, statistik agreement, sensitivity, monotonicity
├── run_test_cases.py       # mencetak tabel Part 13 dari model yang sebenarnya
├── make_figures.py         # mengekspor gambar untuk report
├── tests/test_model.py     # 9 unit test
├── data/
│   ├── dummy_survey_data.csv   # DUMMY, bukan hasil penelitian
│   ├── survey_template.csv     # header kosong
│   └── README.md               # definisi kolom = definisi pertanyaan survei
├── docs/
│   ├── DESIGN.md           # dokumen ini
│   └── figures/            # gambar untuk report/slide
├── screenshots/            # isi dengan screenshot aplikasi untuk README & report
├── requirements.txt
└── README.md
```

Perubahan dari struktur di brief, beserta alasannya:
- `evaluation.py` dipisah dari `app.py` supaya logika statistik bisa diuji tanpa UI.
- `data/survey_data.csv` diganti menjadi `dummy_survey_data.csv` + `survey_template.csv`. Nama file sendiri sudah memberi tahu bahwa isinya dummy, sehingga tidak bisa tertukar dengan data nyata.
- Ada `tests/` dan `run_test_cases.py` agar hasil Part 13 bisa direproduksi.

---

## PART 11 — Kode

Seluruh kode ada di repo ini dan sudah dijalankan:
- `python tests/test_model.py` → **9/9 test lulus** (bentuk MF, Ruspini partition, kelengkapan rule, centroid vs integrasi scipy, threshold, arah input, ID unik, chaining multi-langkah, level LOW).
- `python run_test_cases.py` → tabel Part 13.
- Setiap halaman `app.py` sudah dieksekusi dengan stub Streamlit: semua halaman, callback Analyze, upload CSV valid/tidak valid/kolom hilang, dan dataset dummy. Tidak ada error. **Belum diuji di Streamlit asli** karena lingkungan pengembangan tidak punya akses ke package Streamlit. Jalankan `streamlit run app.py` sekali di laptop sebelum demo.

---

## PART 12 — Penjelasan algorithmic core untuk oral defense

| Yang ditanya | File → fungsi / objek |
|---|---|
| Membership functions | `fuzzy_model.py` → `trapmf()`, `INPUT_VARIABLES`, `OUTPUT_VARIABLE` |
| Fuzzy rules | `fuzzy_model.py` → `RULES` (R1–R11), `rule_to_text()` |
| Fuzzification | `fuzzy_model.fuzzify()` |
| Inference (firing strength) | `fuzzy_model.evaluate_rules()`: OR = `min(1, sum)`, AND = `min` |
| Implication + aggregation | `fuzzy_model.implicate_and_aggregate()`: `np.fmin` (clip), `np.fmax` (aggregate) |
| Defuzzification | `fuzzy_model.defuzzify_centroid()`: `sum(y·μ)/sum(μ)` |
| Fatigue index | `fuzzy_model.infer()` → `FuzzyResult.fatigue_index` |
| Fatigue level + threshold | `fuzzy_model.categorize()`, `category_thresholds()` |
| Recommendation | `recommendation.facts_from_fuzzy()`, `KB_RULES`, `forward_chain()` |

### 5 Things Every Team Member Must Understand

1. **Why Fuzzy Logic?** Indikatornya samar. Threshold crisp "< 7 jam = kurang tidur" membuat 6,9 jam dan 4 jam sama-sama "kurang", sementara 7,0 jam "normal". Fuzzy memberi transisi bertahap (6,5 jam = 0,5 LOW + 0,5 NORMAL), dan aturannya bisa ditulis dalam bahasa manusia. Tidak ada data berlabel yang cukup untuk classifier; pengetahuan dituangkan langsung sebagai rule.
2. **Why these inputs?** Keempatnya bisa dilaporkan sendiri oleh mahasiswa dengan cepat dan mewakili tiga sisi: pemulihan (tidur, makan), beban (tugas), dan kebiasaan (screen time hiburan). Screen time dibatasi ke non-akademik supaya tidak dobel-hitung dengan beban tugas. Ini keputusan desain, bukan klaim bahwa keempatnya adalah penyebab kelelahan satu-satunya.
3. **Why these membership functions?** Bentuk linear mudah dihitung manual. Ruspini partition membuat derajat selalu berjumlah 1 dan OR = NOT label lain. Hanya inti tidur 7–9 jam yang didukung referensi (NSF). Sisanya asumsi kelompok yang akan dicek dengan data. **Setiap anggota harus bisa menyebut parameter mana yang asumsi.**
4. **How does one input case produce the final fatigue index?** Latih Contoh B di Part 5 sampai bisa ditulis di papan: membership → min/bounded-sum per rule → clip → max → centroid → 42,9 → MODERATE.
5. **How are recommendations generated?** Level + fakta risiko (α-cut 0,5) masuk ke forward chaining. Rule menyala jika semua premis sudah menjadi fakta, lalu diulang sampai tidak ada fakta baru. Tunjukkan trace (iterasi 1 → 2). Semua saran bersifat umum dan bukan medis.

**Pertanyaan yang kemungkinan muncul, beserta jawabannya:**
- *"Kenapa indeks tidak pernah 0 atau 100?"* Itu sifat centroid (lihat Part 3, bagian Output).
- *"Kenapa OR pakai bounded sum, bukan max?"* Karena max membuat dip 0,5 di titik silang. Uji monotonicity membuktikannya (Part 4/14).
- *"Apakah ini diagnosis?"* Bukan. Ini prototipe akademik; self-report bukan ground truth klinis.

---

## PART 13 — Test cases (dihasilkan oleh `python run_test_cases.py`)

Singkatan input: S = sleep (jam), A = assignments, C = screen non-akademik (jam), M = meals. Clip level L/M/H = hasil aggregation per label output.

| Case | Input (S, A, C, M) | Rules aktif (strength → output) | Clip L/M/H | Index | Level | Rekomendasi |
|---|---|---|---|---|---|---|
| 1. Very healthy routine | 8, 1, 1.5, 3 | R4 1.00→L | 1/0/0 | 17.03 | LOW | maintain_routine |
| 2. Low sleep | 4.5, 2, 2, 3 | R2 1.00→M | 0/1/0 | 50.00 | MODERATE | short_rest, protect_sleep |
| 3. High workload | 7.5, 10, 2, 3 | R3 1.00→M | 0/1/0 | 50.00 | MODERATE | short_rest, prioritize_urgent |
| 4. High screen time | 7.5, 3, 9, 3 | R5 1.00→M | 0/1/0 | 50.00 | MODERATE | short_rest, reduce_non_essential |
| 5. Low meal frequency | 7.5, 3, 2, 1 | R8 1.00→M | 0/1/0 | 50.00 | MODERATE | short_rest, regular_meals |
| 6. Multiple risk factors | 5, 9, 8, 1 | R1, R6, R7, R9, R10, R11 all 1.00→H | 0/0/1 | 82.97 | HIGH | reduce_non_essential, prioritize_urgent, recovery_break, deadline_extension, protect_sleep, regular_meals, seek_support |
| 7a. Borderline (sleep 6.5) | 6.5, 5, 5, 3 | R1 0.50→H, R4 0.50→L | 0.5/0/0.5 | 50.00 | MODERATE | short_rest, protect_sleep |
| 7b. Borderline (workload 7) | 7.5, 7, 7, 2 | R3, R5, R8 0.50→M; R4 0.50→L; R6, R9, R11 0.50→H | 0.5/0.5/0.5 | 50.00 | MODERATE | short_rest, reduce_non_essential, prioritize_urgent, regular_meals |
| 8a. Extreme worst | 2, 15, 14, 0 | R1, R6, R7, R9, R10, R11 1.00→H | 0/0/1 | 82.97 | HIGH | (sama dengan case 6) |
| 8b. Out-of-range input | 12, 30→15, 0, 6 | R3 1.00→M | 0/1/0 | 50.00 | MODERATE | short_rest, prioritize_urgent |
| 9. Worked example A | 5, 6, 8, 2 | R1 1.00, R7 1.00, R10 0.50, R11 0.50 →H | 0/0/1 | 82.97 | HIGH | reduce_non_essential, recovery_break, protect_sleep, regular_meals, seek_support |

**Pengamatan yang perlu disebut di report:**
- **Pengelompokan nilai (plateau clustering).** Banyak input menghasilkan indeks yang persis sama (17,03 / 50,00 / 82,97) karena input berada di plateau MF, sehingga hanya satu label output aktif penuh. Indeks baru bervariasi halus di zona transisi. Resolusinya terbatas, dan ini berdampak pada korelasi (banyak ties).
- **Case 7a:** LOW dan HIGH masing-masing 0,5 tanpa MODERATE, hasilnya tepat 50. Dua rule yang bertentangan "saling membatalkan" ke tengah. Ini sifat centroid yang wajar dijelaskan.
- **Case 8b:** 30 tugas dipotong ke 15 (tetap MANY penuh), dan tidur 12 jam = HIGH (netral), hasilnya MODERATE.

---

## PART 14 — Evaluasi

### 14.1 Rule consistency (tanpa data survei, sudah dijalankan)

| Cek | Hasil |
|---|---|
| Kelengkapan: setiap kombinasi grid 13⁴ = 28.561 titik punya ≥ 1 rule aktif | ✅ lulus |
| Tidak ada dua rule dengan antecedent identik tetapi konsekuen berbeda | ✅ (diperiksa manual pada tabel Part 4) |
| Ruspini partition semua input | ✅ lulus |
| Centroid kode vs integrasi `scipy.quad` (4 kasus) | ✅ selisih < 0,1 |

### 14.2 Sensitivity dan monotonicity (`evaluation.monotonicity_check()`, sudah dijalankan)

Setiap input digeser ke arah "lebih berisiko" dengan langkah 0,25. Input lain ditahan pada semua kombinasi titik breakpoint dan titik ¼ di dalam slope, karena di situlah artefak muncul. Tidur di atas 8 jam dan makan di atas 3 kali tidak ikut diuji karena rule base memperlakukannya netral.

| Input (arah berisiko) | Langkah dicek | Indeks turun > 0,01 | % | Penurunan terbesar | Level ikut turun |
|---|---|---|---|---|---|
| sleep (turun) | 50.688 | 35 | 0,07% | 1,82 poin | 0 |
| assignments (naik) | 95.040 | 368 | 0,39% | 1,10 poin | 84 |
| screen time (naik) | 101.376 | 24 | 0,02% | 0,82 poin | 12 |
| meals (turun) | 20.736 | 28 | 0,14% | 0,82 poin | 14 |

**Interpretasi jujur.**
- Versi rule awal (rule per sel tabel, OR=max) punya penurunan hingga **4,7 poin**. Setelah penggabungan rule dan bounded-sum OR, penurunan maksimum turun menjadi **1,8 poin**, dan hanya terjadi di zona transisi saat sebuah rule MODERATE memudar sementara rule HIGH sudah jenuh. Ini sifat dikenal dari kombinasi aggregation max + centroid pada Mamdani, bukan kesalahan rule.
- "Level ikut turun" hanya terjadi ketika indeks berada < 2 poin di atas threshold 36,67 atau 63,33.
- Untuk sensitivitas per kasus, gunakan grafik di halaman *How the Model Works*.

### 14.3 Perbandingan dengan self-reported fatigue (setelah survei)

Metrik (sudah diimplementasikan di `evaluation.py` dan halaman *Survey Data*):

| Metrik | Kenapa | Catatan |
|---|---|---|
| **Spearman ρ** + 95% CI bootstrap (2000 resample) | Self-report adalah skala ordinal; yang ditanya "searah atau tidak" | Metrik utama. CI wajib dilaporkan karena n kecil |
| Category agreement (%) | Kesesuaian level. Self-report dipetakan dengan threshold yang sama setelah rescale 1–10 → 0–100: 1–4 LOW, 5–6 MODERATE, 7–10 HIGH [DESIGN ASSUMPTION] | Bergantung pada pemetaan ini |
| Cohen's κ | Agreement dikoreksi faktor kebetulan | Tidak stabil jika n kecil atau kelas timpang |
| Confusion matrix | Melihat arah kesalahan (sistem lebih "galak" atau lebih "lunak") | — |
| Distribusi level prediksi | Mengecek apakah sistem hanya mengeluarkan satu level | — |
| MAE indeks vs self-report yang di-rescale | Pelengkap saja | Mengasumsikan skala interval |

**Format tabel hasil untuk report.** Angka di bawah berasal dari **DUMMY DATA** dan hanya menunjukkan format. Nilai `self_reported_fatigue` dummy ditulis tangan agar "terlihat masuk akal", sehingga korelasinya tinggi secara artifisial. **Jangan dikutip sebagai hasil.**

| Metrik | Nilai (DUMMY, n=15) | Nilai survei nyata |
|---|---|---|
| Spearman ρ [95% CI] | 0,91 [0,76; 0,95] | *diisi setelah survei* |
| Category agreement | 87% | … |
| Cohen's κ | 0,80 | … |
| Distribusi level (L/M/H) | 5 / 4 / 6 | … |

**Keterbatasan evaluasi dengan n kecil.** Dengan n ≈ 30, CI korelasi akan lebar (kira-kira ±0,3). Satu kategori bisa hampir kosong sehingga κ tidak stabil. Indeks yang berkelompok di 17/50/83 menimbulkan banyak ties. Hasilnya hanya boleh ditulis sebagai "indikasi awal searah/tidak searah", bukan validasi.

### 14.4 Usability (opsional, murah)

Minta 5 teman mencoba aplikasi tanpa bantuan. Catat apakah mereka bisa menyelesaikan assessment dan apakah mereka paham arti level dan rekomendasi (ya/tidak + satu komentar). Laporkan sebagai pengamatan informal.

---

## PART 15 — Limitations

1. **Sampel survei kecil dan convenience sample** (teman satu fakultas), sehingga tidak mewakili seluruh mahasiswa.
2. **Semua input dan referensi bersifat self-report**, rentan recall bias dan social desirability bias.
3. **Self-reported fatigue itu subjektif**, bukan ground truth. Kesesuaian dengannya bukan bukti validitas klinis.
4. **Rule dan sebagian besar MF dirancang manual** ([DESIGN ASSUMPTION]); orang lain bisa merancang secara berbeda dengan alasan yang sama kuatnya.
5. **MF mungkin tidak berlaku umum.** Definisi "banyak tugas" berbeda antar program studi dan antar minggu dalam semester.
6. **Tidak ada validasi klinis**, dan sistem ini bukan alat diagnosis.
7. **Variabel terbatas**: tidak ada kualitas tidur, stres, aktivitas fisik, kafein, kondisi kesehatan, atau pekerjaan sampingan.
8. **Sifat Mamdani + centroid**: indeks terbatas di sekitar 17–83, nilai berkelompok, dan ada penurunan kecil non-monoton (≤ 1,8 poin) di zona transisi (Part 14.2).
9. **Rekomendasi bersifat umum** dan tidak dipersonalisasi, bukan saran medis.
10. **Tidak ada dimensi waktu**: sistem menilai satu snapshot "rata-rata 7 hari", bukan tren.

---

## PART 16 — Struktur report (maks. 6 halaman)

Isi wajib dari PDF D3: link GitHub, formalisasi masalah dalam istilah kuliah, data/rules beserta asalnya, justifikasi desain, hasil + screenshot, dan limitation.

| # | Section | Isi | Figure/Table | Perkiraan halaman |
|---|---|---|---|---|
| 1 | Introduction | Konteks kelelahan mahasiswa, alasan early warning, kontribusi (FIS + KB + evaluasi survei). Link GitHub sudah dicantumkan di sini | — | 0,4 |
| 2 | Problem and System Objective | Problem statement, target user, skenario, tujuan, **kenapa fuzzy (Lecture 6) + forward chaining (Lecture 4)** | Diagram pipeline (Part 2) | 0,5 |
| 3 | Data and Data Collection | Kuesioner, periode acuan 7 hari, anonimisasi/consent, n, tanggal pengambilan, cleaning (baris yang dibuang dan alasannya), statistik deskriptif. **Sebutkan jelas bahwa data dummy hanya untuk pengembangan** | Tabel statistik deskriptif, histogram | 0,7 |
| 4 | Fuzzy Logic Model | Variabel & MF dengan label sumber, rule base, operator Mamdani, threshold, KB rekomendasi, **satu contoh perhitungan (Contoh B)** | Gambar MF (4+1), tabel rule, tabel parameter berlabel | 1,6 |
| 5 | System Implementation | Arsitektur modul, halaman aplikasi, bagaimana tiap tahap dipetakan ke fungsi, cara verifikasi (unit test, cek scipy) | 2–3 screenshot (Assessment, Result + trace) | 0,8 |
| 6 | Results and Evaluation | Tabel test case (Part 13), monotonicity (14.2), hasil survei (ρ + CI, agreement, κ, confusion matrix, scatter) | Tabel 13, tabel 14.2, scatter, confusion matrix | 1,2 |
| 7 | Limitations | Part 15, dipadatkan | — | 0,4 |
| 8 | Conclusion | Apa yang dicapai, apa yang belum, langkah lanjut (lebih banyak data, rule divalidasi ahli) | — | 0,2 |
| 9 | GitHub Repository + References | Link repo, daftar referensi (NSF, Mamdani, Zadeh, AIMA), pernyataan penggunaan AI tools sesuai Section 6 | — | 0,2 |

Jika data survei belum masuk saat menulis, Section 3 dan 6 ditulis sebagai *"akan dilaporkan"* dan hanya memuat hasil yang benar-benar ada. Jangan mengisi angka dummy.

---

## PART 17 — Struktur presentasi (10 slide, fokus algoritma)

| # | Slide | Isi utama | Visual |
|---|---|---|---|
| 1 | Title | Judul terdaftar, anggota, NIM | — |
| 2 | Real-world problem | Kelelahan menumpuk tanpa disadari; indikator yang samar | 1 kalimat + 4 ikon input |
| 3 | Proposed solution | Pipeline FIS → index → level → forward chaining → aksi | Diagram pipeline |
| 4 | Data | Kuesioner, n, periode, anonim; self-report = referensi subjektif | Histogram |
| 5 | Fuzzy model | Operator Mamdani (Lecture 6) & alasan (bounded-sum OR, centroid, threshold 36,67/63,33); forward chaining (Lecture 4) sebagai layer rekomendasi | Tabel operator |
| 6 | Membership functions + rules | 4 MF + label sumber; tabel dasar 2×3 + eskalasi | Gambar MF, grid rule |
| 7 | Worked example | Contoh B langkah demi langkah (membership → rule → clip → max → centroid 42,9) | `worked_example_aggregation.png` atau plot contoh B |
| 8 | System demo | Demo live atau screenshot Result + trace | Screenshot |
| 9 | Results & limitations | Test case penting, monotonicity (0,02–0,39%, maks 1,8 poin), ρ survei + CI, keterbatasan utama | Tabel kecil, scatter |
| 10 | Conclusion | Apa yang dicapai dan langkah lanjut | — |

Setiap anggota sebaiknya memegang minimal satu slide algoritma (5, 6, atau 7), karena ada oral check individual.

---

## PART 18 — README

Lihat `README.md` di root repo.

---

## PART 19 — Final check

| Item | Status | Bukti / catatan |
|---|---|---|
| Real-world problem | ✅ | Part 2 |
| Real student survey data can be inserted | ✅ | Upload CSV + template + validasi |
| Fuzzy algorithm clearly implemented | ✅ | `fuzzy_model.py`, fungsi terpisah per tahap |
| Membership functions explicitly defined | ✅ | `INPUT_VARIABLES`, `OUTPUT_VARIABLE` |
| Rules explicitly defined | ✅ | `RULES` R1–R11 beserta alasan |
| Fuzzification implemented | ✅ | `fuzzify()` |
| Inference implemented | ✅ | `evaluate_rules()` |
| Aggregation implemented | ✅ | `implicate_and_aggregate()` |
| Defuzzification implemented | ✅ | `defuzzify_centroid()`, dicek vs scipy |
| Fatigue index generated | ✅ | `infer()` |
| Recommendation generated | ✅ | `forward_chain()` + trace |
| Interactive web app works | ⚠️ | Semua halaman lulus smoke test dengan stub; **jalankan sekali di Streamlit asli** |
| CSV upload works | ⚠️ | Diuji lewat stub (valid, kolom hilang, nilai rusak); cek sekali di Streamlit asli |
| Dummy data clearly labeled | ✅ | Nama file, ID `DUMMY_`, banner merah, `data/README.md` |
| Testing performed | ✅ | 9 unit test + 11 test case + monotonicity |
| Limitations discussed | ✅ | Part 15 |
| GitHub-ready | ⚠️ | Tinggal `git init`, push, jadikan public, isi `screenshots/` |
| README available | ✅ | — |
| Report structure follows PDF | ✅ | Part 16 memuat semua isi D3 |
| Presentation structure follows PDF | ✅ | Part 17 (.pptx) |
| Kelayakan algoritma (Section 3) | ✅ | Fuzzy = Lecture 6, forward chaining = Lecture 4 |
| **Data survei nyata** | ❌ | Belum ada; kumpulkan paling lambat 29 Sep |
| Rule/parameter ditinjau & dipahami seluruh anggota (Section 6) | ❌ | **Wajib dilakukan kelompok sendiri** |

---

## Referensi

- Hirshkowitz, M., Whiton, K., Albert, S. M., et al. (2015). National Sleep Foundation's sleep time duration recommendations: methodology and results summary. *Sleep Health*, 1(1), 40–43.
- Mamdani, E. H., & Assilian, S. (1975). An experiment in linguistic synthesis with a fuzzy logic controller. *International Journal of Man-Machine Studies*, 7(1), 1–13.
- Zadeh, L. A. (1965). Fuzzy sets. *Information and Control*, 8(3), 338–353.
- Russell, S., & Norvig, P. (2021). *Artificial Intelligence: A Modern Approach* (4th ed.). Pearson. (forward chaining, Bab 7)

Kelompok juga wajib menyebut penggunaan AI tools untuk scaffolding kode/UI sesuai Section 6 PDF.
