# Laporan Riset Strategi Forex — Regime-Aware Portfolio
**Tanggal:** 2026-06-02 · **Data:** H1, 2022-01 → 2026-06 (~4,4 thn, 27.455 bar/simbol)
**Setup:** modal $1.000/simbol · risk 0,5%/trade · spread ≤12% · backtest pakai `backtest_lab.py` (no logic-drift)
**Split:** IN-SAMPLE 2022–2024 · OUT-SAMPLE (OOS) 2025–2026 (tak dipakai tuning)

---

## 1. Ringkasan Eksekutif (baca ini saja kalau buru-buru)

- **Portofolio gabungan 4 simbol = RUGI −$192 (−4,8%) selama 4,4 thn.** Menggabungkan semuanya secara buta **tidak** menciptakan edge.
- **Satu-satunya edge yang benar-benar kokoh = AUDJPY regime-aware: +$218 (+21,8%), PF 1,16, max DD 9,7%, dan POSITIF di in-sample (+$194) maupun out-of-sample (+$24).** Kedua sleeve menyumbang (TREND +$151, MR +$67 dgn win-rate 59,8%).
- USDJPY, EURUSD = **rugi** (penyeret portofolio). EURJPY break-even (rugi total tapi OOS +$61).
- **Pelajaran inti:** edge forex H1 retail itu tipis & bergantung regime. Jangan deploy keranjang — deploy yang terbukti (AUDJPY), perlakukan sisanya sebagai *belum tervalidasi*.

---

## 2. Aturan Strategi yang Diuji

| Regime | Kondisi | Strategi | Exit |
|---|---|---|---|
| Trending | ADX ≥ 25 | **TREND** (Donchian-20 breakout + filter SMA-50) | **Trailing stop 2,0×ATR** (no TP tetap) |
| Ranging | ADX < 20 | **MR** (Bollinger-20/2σ + RSI-14 <30/>70) | SL & TP tetap 1,5×ATR (1:1) |
| Transisi | 20 ≤ ADX < 25 | — diam, tidak entry — | |

Risiko awal tiap trade = 1,5×ATR (≈1R). Satu posisi per simbol pada satu waktu.

---

## 3. P/L Portofolio Agregat (4 simbol, modal total $4.000)

| Periode | Trades | Win-rate | Gross Profit | Gross Loss | **NET** | PF | Max DD |
|---|---|---|---|---|---|---|---|
| **FULL 2022-2026** | 2.738 | 37,3% | +$5.048,61 | −$5.240,77 | **−$192,16 (−4,8%)** | 0,96 | 13,5% |
| IN-SAMPLE 2022-2024 | 1.926 | 37,2% | +$3.654,84 | −$3.758,01 | −$103,18 (−2,6%) | 0,97 | 9,2% |
| OUT-SAMPLE 2025-2026 | 812 | 37,6% | +$1.393,78 | −$1.482,76 | −$88,98 (−2,2%) | 0,94 | 6,1% |

Avg win +$4,94 · Avg loss −$3,05 · Trade terbaik +$38,60 · terburuk −$7,95.

---

## 4. Breakdown per Simbol (FULL 2022-2026)

| Simbol | NET | PF | Win% | Max DD | OOS NET | Verdict |
|---|---|---|---|---|---|---|
| **AUDJPY** | **+$217,95** | **1,16** | 41,1% | 9,7% | **+$24,43 (PF 1,05)** | ✅ **Edge nyata, robust IS+OOS** |
| EURJPY | −$68,89 | 0,94 | 39,3% | 19,1% | +$60,95 (PF 1,24) | ⚠️ OOS membaik, full masih merah |
| EURUSD | −$145,42 | 0,89 | 35,5% | 22,7% | −$63,49 | ❌ Rugi |
| USDJPY | −$195,81 | 0,86 | 33,9% | 27,7% | −$110,86 | ❌ Rugi, DD besar |

### Detail sleeve AUDJPY (sang juara)
- **TREND (trail 2,0×ATR):** n=521, win 37,2%, **net +$150,76**, PF 1,13, DD 10,4%
- **MR (ADX<20):** n=107, **win 59,8%**, **net +$67,20**, PF 1,32, **DD 3,1%** ← komplemen low-risk

---

## 5. Breakdown per Sleeve & per Tahun (FULL, semua simbol)

**Per sleeve:** TREND net −$101 (n=2.260, win 34,9%, PF 0,98) · MR net −$91 (n=478, win 48,5%, PF 0,91)
→ Secara agregat dua-duanya ~break-even; profit AUDJPY tertutup rugi USDJPY/EURUSD.

**Per tahun (net $):**
| 2022 | 2023 | 2024 | 2025 | 2026 (s/d Jun) |
|---|---|---|---|---|
| +$97 | −$150 | −$50 | **−$213** | +$124 |

→ 2022 (tren kuat) & 2026 (pemulihan) hijau; 2023–2025 (banyak choppy/whipsaw) merah. Mengonfirmasi: **edge bergantung regime**, dan 2023-25 adalah rezim yang menyulitkan breakout.

---

## 6. Perjalanan Riset (apa yang sudah diuji & dibuang)

| Eksperimen | Hasil | Kesimpulan |
|---|---|---|
| #1 Entry pullback (limit retest) | ret turun di semua pair | ❌ Buang — melewatkan tren besar |
| #3 Skip impulse candle (range>X·ATR) | menolong USDJPY/EURJPY saja | ⚠️ Marginal, symbol-dependent |
| Exit: BE@1R | DD turun, return flat | Pereduksi risiko, bukan profit |
| **Exit: Trailing 2,0×ATR** | robust naik PF & potong DD | ✅ **Adopsi** |
| Exit: Trailing 3,0×ATR | PF tertinggi di IS, rapuh di OOS | Bagus saat trending saja |
| ADX-gate di TREND | OOS positif tapi rusak IS, threshold per-pair | 🚩 Overfit |
| MR + ADX<20 (ranging gate) | hijau OOS di AUDJPY/EURJPY/EURUSD | ✅ Komplemen valid (small-sample) |
| **Portofolio gabungan** | net −4,8%, AUDJPY satu-satunya kokoh | ⇒ **Deploy selektif** |

---

## 7. Rekomendasi

1. **DEPLOY (live, size normal): AUDJPY regime-aware** — TREND(trail 2,0×ATR) saat ADX≥25 + MR(BB+RSI) saat ADX<20. Satu-satunya yang positif IS **dan** OOS dengan DD <10%.
2. **PERTIMBANGKAN (size kecil/observasi): EURJPY** — OOS membaik (PF 1,24) tapi belum konsisten penuh.
3. **JANGAN deploy** USDJPY & EURUSD pada strategi ini (rugi, DD besar). USDJPY TREND lama (`mt5-ft@USDJPY_TREND`) sebaiknya dievaluasi ulang.
4. **Upgrade exit semua sleeve TREND ke trailing 2,0×ATR** (ganti TP tetap 3×ATR) — perbaikan robust lintas simbol.
5. **Kelola ekspektasi:** edge tipis (PF ~1,1–1,3), low-frequency. Profit datang dari konsistensi + DD rendah, bukan ledakan return. Sampel OOS kecil (~30–200 trade) → konfirmasi lewat forward-test live sebelum naikkan size.

---

## 8. Caveat (penting)
- Backtest pakai eksekusi bar-close + asumsi konservatif (SL diprioritaskan saat 1 bar kena SL & TP). Slippage/spread riil bisa lebih buruk → forward-test wajib.
- Hasil OOS sebagian small-sample; bukan jaminan masa depan.
- XAUUSD sengaja dikeluarkan dari MR (DD 46–59% di config ini = jebakan).

*File backtest: `/opt/mt5-quant/bt_combo.py`, `bt_exit.py`, `bt_adx.py`, `bt_mr.py`, `bt_path.py` (CT 108). Report mentah: `/opt/mt5-quant/data/regime_report.txt`.*
