# IDX Services — Status Running

> Lokasi: **CT108 `/opt/idx-quant`** (kecuali disebut lain). Diakses via Proxmox node `go`.
> Snapshot: 2026-06-09.

## 🟢 Continuously running (daemon)

| Service | Lokasi | Fungsi |
|---|---|---|
| `idx-ara-guard.service` | CT108 | ARA realtime **bearish-ignition exit guard** (paper) — aktif |
| `/idx-md` (PID 14746, up 14 hari) | CT114 | IDX market-data daemon |

## ⏲️ Active timers (terjadwal, auto-run — CT108)

| Timer | Jadwal | Fungsi |
|---|---|---|
| `idx-volign` | **tiap 10 mnt** jam bursa | volume-ignition gorengan scanner |
| `idx-obi-logger` | tiap 15 mnt jam bursa | orderbook-imbalance (whale absorption) logger |
| `idx-ara-intraday` | tiap 30 mnt jam bursa | mark ARA paper-trade |
| `idx-ara-screen` | harian 15:40 WIB | tutup day-trade + screening (validasi sebelum entry) |
| `idx-ara-timing` | harian 16:30 WIB | harvest jam ignition/lock |
| `idx-scanner` | harian 17:00 WIB (Sen–Jum) | EOD scanner MEANREV + foreign-flow |
| `idx-movers-logger` | harian 18:00 WIB | movers EOD logger (dataset pre-ARA) |
| `idx-ara-paper` | harian 18:30 WIB | ARA paper-trade daily after close |
| `idx-fundamental` | bulanan tgl 1, 18:00 WIB | fundamental value screener → RAG |

> **Catatan:** unit oneshot (`idx-volign.service` dll.) tampil `inactive dead` di sela run — itu **normal**, karena dipicu timer (jalan → selesai → mati sampai trigger berikutnya).
>
> `idx-volign` + `idx-ara-timing` sudah ~1 minggu numpuk data timing (lihat `tanya1-2minggukedepan.md`) — siap kalau mau lanjut "pertajam scanner".
