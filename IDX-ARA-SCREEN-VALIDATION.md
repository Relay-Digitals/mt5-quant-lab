# IDX ARA Screener — Syarat Validasi Entry

> Service: `idx-ara-screen` (CT108 `/opt/idx-quant/idx_ara_screen.py`), jalan harian **15:40 WIB** (08:40 UTC).
> Entry lolos → masuk paper-trade `ara_paper.json` + langsung kirim report Paper-Trade.
> Konstanta: `MINCHG=15%` · `MINVALUE=Rp10M` · `ALLOC=Rp10jt` · `LOT=100`.

## Tahap 1 — Masuk daftar kandidat (universe)

Sumber: 3 mover list **TOP_GAINER**, **TOP_VALUE**, **TOP_FREQUENCY**, dengan filter:

- Kode = **4 huruf** (`isalpha`) → buang waran/rights (-W / -R).
- **Naik ≥ 15%** (`MINCHG`) **DAN** nilai transaksi **≥ Rp10 miliar** (`MINVALUE`).
- **+ semua saham KONGLO** — *selalu* dievaluasi, **bypass** filter mover di atas.

## Tahap 2 — Validasi per kandidat (gate berlapis)

Urutan di `screen()`:

1. **Sudah dipegang?** → skip (anti-dobel).
2. **ARA-lock?** (`offer freq == 0`, antrian jual kosong) → **SKIP** "tak bisa beli".
3. **Score < 0** (verdict 🔴 RISIKO) → **SKIP**.
4. **Lot < 1** — `(Rp10jt × 0.999) ÷ harga` < 100 lembar → **SKIP** "lot<1" (saham mahal kena di sini).
5. Lolos semua → **ENTRY** (status=open, src=screen).

## Inti validasi: scoring `evaluate()`

| Sinyal | Kondisi | Skor |
|---|---|---|
| Foreign akumulasi 5 hari | `f5 > 0` | **+1** |
| Foreign distribusi konsisten | `f5 < 0` **dan** `fnet < 0` (intraday) | **−1** |
| Bid tebal (tekanan beli) | bid/offer lot ratio `bor ≥ 1.5` | **+1** |
| Offer tebal (tekanan jual) | `bor < 0.7` & tidak lock | **−1** |
| Saham gocap/penny | `harga < Rp200` | **−1** |

**Verdict:** `score ≥ 2` = 🟢 **KUAT** · `score 0–1` = 🟡 **CAMPUR** · `score < 0` = 🔴 **RISIKO**

→ **Boleh entry = `score ≥ 0`** (🟢 KUAT atau 🟡 CAMPUR). 🔴 RISIKO ditolak.

## Catatan

- **Corporate action** (dividend / stocksplit / RUPS dgn exdate ≥ hari ini) **tidak nge-gate** — hanya ditampilkan sebagai katalis + ⚠️ "sell-news" di report.
- Ringkasnya, saham **entry** kalau: **mover kuat (≥15%, ≥Rp10M) atau konglo**, **bukan ARA-lock**, **tidak ada distribusi foreign + offer tebal bareng** (score ≥ 0), **bukan gocap**, dan **muat ≥1 lot** di alokasi Rp10jt.
- ⚠️ Konsekuensi konglo: lolos masuk kandidat (bypass filter mover), tapi yang **mahal** (DCII ~40rb, AMMN ~8rb) kemungkinan kena **gate lot<1** di alokasi Rp10jt → dievaluasi & muncul di report, tapi tidak ambil posisi. (Naikkan `ALLOC` kalau ingin konglo mahal bisa entry.)
