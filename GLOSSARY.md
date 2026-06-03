# Glossary — Istilah Trading & Quant (untuk project ini)

> Penjelasan sederhana semua istilah teknis yang dipakai di diskusi strategi forex (MT5) & saham IDX (Stockbit).

## Kolom hasil backtest
| Istilah | Arti sederhana |
|---|---|
| **Pair** | Pasangan mata uang. `EURUSD` = Euro vs Dollar AS, `GBPUSD` = Pound vs Dollar, `USDJPY` = Dollar vs Yen, `XAUUSD` = Emas vs Dollar. |
| **R** (Reward:Risk) | Perbandingan target untung vs batas rugi. `R=2` → target profit 2× jarak stop-loss. Rugi −$1, menang +$2. |
| **ret** (return) | Hasil akhir dalam persen. `+9%` modal naik 9%, `−6%` turun 6%. |
| **PF** (Profit Factor) | Total uang menang ÷ total uang kalah. **>1 untung**, **<1 rugi**, =1 impas. PF 1,3 = tiap Rp1 rugi diimbangi Rp1,3 untung. |
| **FULL** | Hasil di seluruh periode data. |
| **IS** (In-Sample) | Data "lama" untuk mengembangkan/melihat strategi. |
| **OOS** (Out-of-Sample) | Data "baru" yang belum pernah dilihat strategi = **ujian kejujuran**. Bagus di IS tapi jelek di OOS = strategi cuma kebetulan cocok data lama, tak bisa dipercaya. |
| **win-rate** | % trade yang menang. 40% = 4 dari 10 trade untung. |
| **DD** (Drawdown) | Penurunan terdalam modal dari titik tertinggi. DD 25% = pernah turun 25% dari puncak. Makin kecil makin aman. |

## Mekanik trading
| Istilah | Arti |
|---|---|
| **SL / TP** | Stop Loss (batas rugi otomatis) / Take Profit (target untung otomatis). |
| **spread** | Selisih harga beli vs jual = biaya tiap buka posisi. |
| **pip / point** | Satuan gerak harga. 1 pip EURUSD = 0,0001 = 10 point. JPY: 1 pip = 0,01. |
| **ATR** (Average True Range) | Rata-rata besar gerakan per candle = ukuran volatilitas (seberapa liar harga). |
| **timeframe** | Kerangka waktu 1 candle: M1=1 menit, M5=5 mnt, M15=15 mnt, M30=30 mnt, H1=1 jam, H4=4 jam, D1=1 hari. |
| **HTF** (Higher Time Frame) | Timeframe lebih besar untuk lihat arah besar (mis. H1 jadi acuan arah saat entry di M15). |
| **lot** | Ukuran posisi. 0,01 lot (micro-lot) = terkecil, cocok modal kecil ($10). |
| **bias** | Kecenderungan arah. Bias naik = hanya cari posisi beli. |
| **magic number** | Label angka di tiap order MT5 agar tahu posisi itu dari strategi mana. |
| **session** | Sesi pasar: London (~07–11 UTC) & New York (~12–16 UTC) = paling ramai/likuid. Asia = sepi. |

## Cara menguji
| Istilah | Arti |
|---|---|
| **backtest** | Uji strategi pakai data masa lalu. |
| **forward-test / paper-trade** | Uji ke depan real-time tapi uang virtual (tidak rugi beneran). |
| **holdout** | Menyisihkan sebagian data untuk uji akhir (= OOS). |
| **base rate** | Peluang dasar suatu kejadian tanpa syarat apa pun. |
| **lift** | Berapa kali lipat suatu sinyal menaikkan peluang vs base rate. Lift ×26 = 26× lebih mungkin. |
| **overfit** | Strategi terlalu "dijahit" ke data lama → gagal di data baru. |

## Jenis strategi
| Istilah | Arti |
|---|---|
| **TREND / trend-following** | Ikut arah — beli saat naik kuat. |
| **MEANREV / mean-reversion** | Lawan arah sesaat — beli saat turun ekstrem, taruhan balik ke rata-rata. |
| **breakout** | Beli saat harga menembus level penting. |
| **S/R** (Support/Resistance) | Support = lantai harga (sering mantul naik); Resistance = atap (sering mantul turun). |
| **regime** | "Cuaca pasar": trending (searah) vs ranging/sideways (mondar-mandir). Strategi beda cocok untuk regime beda. |
| **trailing stop** | SL yang ikut bergerak mengunci profit saat harga jalan ke arah kita. |
| **breakeven stop** | Geser SL ke harga entry setelah untung tertentu (posisi jadi "bebas risiko"). |

## Indikator (rumus dari harga)
| Istilah | Arti |
|---|---|
| **EMA / SMA** | Moving Average (garis rata-rata harga). EMA lebih responsif. EMA50 = rata-rata 50 candle. |
| **RSI** | 0–100, ukur jenuh. <30 = oversold (jenuh jual), >70 = overbought (jenuh beli). |
| **Williams %R** | −100 s/d 0, mirip RSI. Dekat −100 = sangat oversold, dekat 0 = sangat overbought. |
| **Bollinger Bands** | Pita atas/bawah dari volatilitas; harga tembus pita = ekstrem. |
| **Donchian** | Kanal high tertinggi/low terendah N bar (dipakai breakout). |
| **ADX** | Ukur kekuatan tren. >25 trending kuat, <20 ranging/lemah. |
| **MACD / Stochastic / CCI / MFI** | Indikator momentum/jenuh lainnya. |

## Khusus saham Indonesia (IDX)
| Istilah | Arti |
|---|---|
| **ARA / ARB** | Auto Reject Atas = naik mentok batas harian (~20–35% tergantung harga); ARB = turun mentok. |
| **net foreign** | Selisih beli−jual investor asing (indikator bandar besar masuk/keluar). |
| **foreign-flow regime** | Strategi ikut akumulasi asing jangka menengah. |
| **gorengan** | Saham spekulatif yang sering ARA/ARB (digerakkan bandar). |
| **top gainer / mover** | Saham naik terbanyak / paling aktif hari itu. |
| **value investing** | Beli saham murah secara fundamental (PER rendah, dividen tinggi). |
| **EOD** (End of Day) | Akhir hari — scanner jalan setelah pasar tutup. |

---
_Dibuat 2026-06-02. Kalau ada istilah baru yang belum jelas, tanya saja — akan ditambahkan._
