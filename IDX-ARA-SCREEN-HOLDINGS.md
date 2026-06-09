# IDX ARA Screener — Saham Saat Ini

> Snapshot `ara_paper.json` (CT108 `/opt/idx-quant/data/`) — diambil 2026-06-09.
> Portfolio dibuat 2026-06-02, modal awal Rp100jt. 16 posisi total.

## 🟢 Posisi TERBUKA sekarang (held)

| Saham | Sumber | Entry | Harga kini | %  | Verdict |
|---|---|---|---|---|---|
| **TPIA** | screen | 1.525 | 1.775 | **+16,4%** | 🟡 CAMPUR |

Hanya **TPIA** yang masih open. Sisanya sudah exit (closed).

## 🔮 Di-entry oleh idx-ara-screen (src=screen)

| Saham | Status | Entry | Exit/kini | Verdict | P/L (Rp) |
|---|---|---|---|---|---|
| TPIA | open | 1.525 | 1.775 | 🟡 CAMPUR | (floating) |
| MSIN | closed | 452 | 530 | 🟡 CAMPUR | +1.945.065 |
| GRIA | closed | 169 | 171 | 🟡 CAMPUR | +1.965.430 |
| AMRT | closed | 1.350 | 1.350 | — | −39.960 |
| AMMN | closed | 3.920 | 3.480 | — | −1.211.850 |
| ASPR | closed | 222 | 189 | — | −1.252.530 |

## 📋 Di-entry dari WATCH paper-trade (src=watch) — sudah closed

BREN +1.936.440 · CUAN +1.947.002 · DSSA +1.945.471 · BUVA +679.235 · PTRO +421.848 · CDIA +368.901 · BRPT +36.771 · RAJA −38.896 · RATU −217.800 · KJEN −1.215.086

## 🏦 Universe konglo yang SELALU dipantau screener

Sejak update 2026-06-09, 22 saham konglo ini **selalu** dievaluasi screener (bypass filter mover, tetap lewat gate validasi):

> TPIA, INDF, ICBP, AMMN, DNET, ASII, UNTR, AALI, INKP, TKIM, SMAR, DSNG, ADRO, ADMR, AADI, MEDC, BUMI, BRMS, EMTK, BMTR, MNCN, DCII

## Catatan

- Universe screener = **movers harian (TOP gainer/value/freq, dinamis)** + **22 konglo (tetap)**. Daftar movers berubah tiap hari, jadi kandidat non-konglo tidak tetap.
- Konglo baru efektif untuk **run screening berikutnya** & **book paper-trade baru** (state sekarang dibuat 2 Juni, sebelum penambahan konglo).
- Syarat sebuah saham bisa entry: lihat [`IDX-ARA-SCREEN-VALIDATION.md`](IDX-ARA-SCREEN-VALIDATION.md).
