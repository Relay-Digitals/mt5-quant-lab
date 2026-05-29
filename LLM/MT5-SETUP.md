# Self-Hosted MetaTrader 5 (gmag11/metatrader5_vnc) di Proxmox LXC

MetaTrader 5 jalan di Linux LXC tanpa Windows — pakai Wine via image Docker
**`gmag11/metatrader5_vnc`** yang sudah battle-tested. Expose 2 API:
- **noVNC web** untuk akses visual MT5 di browser
- **RPyC server** untuk akses Python lewat library `mt5linux` / `py3mt5linux`

**Host:** Proxmox 9.1, Intel i3-1215U, 15 GB RAM
**CT 132:** `mt5-server` (Debian 12, privileged, 4 GB RAM / 4 GB swap / 2 core / 30 GB disk) — IP `192.168.0.116`
**Berdampingan dengan:**
- CT 103 `vscode-server` (code-server existing)
- CT 130 `comfyui-openvino` (SD generator)
- CT 131 `ai-coder` (LLM stack)

| Komponen | URL | Fungsi |
|---|---|---|
| **noVNC web** | `http://192.168.0.116:3000` | MT5 GUI di browser (Connect → MT5 muncul) |
| **RPyC API** | `192.168.0.116:8001` | Python bridge via `mt5linux` package |
| **Persistent data** | `/opt/mt5-data` di CT | All MT5 state, MQL5 files, history |

---

## Kenapa stack ini

| Kebutuhan | Pilihan | Alternatif ditolak | Alasan |
|---|---|---|---|
| MT5 di Linux | **gmag11/metatrader5_vnc** | mt5linux manual setup | Battle-tested, all-in-one, Wine + Mono + Gecko + noVNC + RPyC ter-bundle |
| Container runtime | Docker-in-LXC | Native LXC | Image gmag11 sudah solved Wine quirks. Native setup memerlukan 4-8x effort, risk debug intensif |
| VNC client | **noVNC (browser)** | TigerVNC / x11vnc desktop client | No client install, akses dari mana saja |
| Python bridge | **RPyC + mt5linux** | ZeroMQ (ejtraderLabs) | RPyC API drop-in compatible dengan `MetaTrader5` package — copy-paste kode Windows langsung jalan |

---

## Arsitektur

```
Proxmox host (192.168.0.222)
  └── CT 132 mt5-server  (privileged LXC, features: nesting=1,keyctl=1)
       └── Docker engine (docker-ce)
            └── container: mt5  (image gmag11/metatrader5_vnc:latest, ~4 GB)
                 ├── Wine 9.x runtime
                 │    ├── MetaTrader 5.exe (auto-updated)
                 │    └── Python-for-Windows + MetaTrader5 package
                 ├── KasmVNC (X11 server + noVNC web) → :3000
                 └── RPyC server (mt5linux server.py) → :8001

  Volume bind: /opt/mt5-data  ←→  /config in container
                    (MT5 state, .wine prefix, MQL5/, history)
```

Kunci: Wine dan MT5 jalan di dalam Docker container, **bukan langsung di LXC**.
Persistensi via volume mount supaya login broker + custom indicator survive restart.

---

## Reproduksi dari nol

### 1. Buat CT 132 (di Proxmox host)

```bash
scp mt5-01-host-create-ct.sh root@192.168.0.222:/root/
ssh root@192.168.0.222 'CTID=132 ROOT_PASSWORD=<set-strong-pw> bash /root/mt5-01-host-create-ct.sh'
```

Output kasih tahu IP CT, mis `192.168.0.116`.

### 2. Provision dalam CT

```bash
pct push 132 mt5-02-container-setup.sh /root/mt5-02-container-setup.sh
pct exec 132 -- bash /root/mt5-02-container-setup.sh
```

Script akan:
- install Docker engine dari repo official
- pull `gmag11/metatrader5_vnc:latest` (~4 GB, butuh 5-15 min)
- bikin systemd unit `mt5.service` yang wrap `docker run`
- start container dengan port 3000 (noVNC), 8001 (RPyC)
- tunggu noVNC ready
- tulis ringkasan ke `/root/MT5-INFO.txt`

### 3. Login broker

1. Buka `http://192.168.0.116:3000` di browser
2. Klik **Connect** → MT5 GUI muncul
3. **File → Login to Trade Account** → masukkan kredensial broker
4. MT5 state akan auto-save ke `/opt/mt5-data` di CT (persist across reboot)

### 4. Test Python access

Dari mana pun di network (host Anda, CT 103, laptop, dll):

```bash
pip install mt5linux
```

```python
from mt5linux import MetaTrader5

mt5 = MetaTrader5(host='192.168.0.116', port=8001)
mt5.initialize()

print(mt5.terminal_info())
print(mt5.account_info())

# Get last 100 candles of EURUSD H1
import datetime
rates = mt5.copy_rates_from('EURUSD', mt5.TIMEFRAME_H1, datetime.datetime.now(), 100)
print(rates)

mt5.shutdown()
```

Semua API `MetaTrader5` Windows package available — drop-in via RPyC.

---

## Struktur file di CT 132

```
/opt/mt5/                       # placeholder (tidak banyak isinya, Docker yang handle)
/opt/mt5-data/                  # PERSIST: di-mount ke /config dalam container
├── .wine/
│   └── drive_c/
│       └── Program Files/MetaTrader 5/
│           ├── terminal64.exe   # MT5 binary (auto-updated)
│           ├── MQL5/
│           │   ├── Experts/     # EA / bot Anda taruh di sini
│           │   ├── Indicators/  # Custom indicator
│           │   └── Scripts/
│           └── Bases/           # Historical data
└── .config/                     # config window posisi, dll

/etc/systemd/system/mt5.service  # systemd wrapper untuk docker run
/root/MT5-INFO.txt                # ringkasan
```

---

## Operasi sehari-hari

| Aksi | Perintah (di host Proxmox) |
|---|---|
| Buka MT5 GUI | http://192.168.0.116:3000 |
| Status container | `pct exec 132 -- docker ps` |
| Logs MT5 container | `pct exec 132 -- docker logs mt5 -f --tail 50` |
| Logs systemd wrapper | `pct exec 132 -- journalctl -u mt5 -f` |
| Restart MT5 | `pct exec 132 -- systemctl restart mt5` |
| Stop MT5 (preserves data) | `pct exec 132 -- systemctl stop mt5` |
| Upgrade Docker image | `pct exec 132 -- docker pull gmag11/metatrader5_vnc:latest && systemctl restart mt5` |
| Masuk Wine shell (debugging) | `pct exec 132 -- docker exec -it mt5 bash` |
| MQL5 files | `pct exec 132 -- ls -la "/opt/mt5-data/.wine/drive_c/Program Files/MetaTrader 5/MQL5"` |
| Memory CT | `pct exec 132 -- free -h` |

---

## Python client examples

### Trading bot dari laptop / CT 103

```python
# pip install mt5linux pandas
from mt5linux import MetaTrader5
import pandas as pd

mt5 = MetaTrader5(host='192.168.0.116', port=8001)
mt5.initialize()

# Snapshot semua open positions
positions = mt5.positions_get()
df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
print(df)

# Place a market order
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": "EURUSD",
    "volume": 0.01,
    "type": mt5.ORDER_TYPE_BUY,
    "deviation": 20,
    "magic": 123456,
    "comment": "python script",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}
result = mt5.order_send(request)
print(result)
```

### Streaming ticks (websocket-style poll)

```python
import time
from mt5linux import MetaTrader5

mt5 = MetaTrader5(host='192.168.0.116', port=8001)
mt5.initialize()

last_time = 0
while True:
    tick = mt5.symbol_info_tick('EURUSD')
    if tick.time != last_time:
        print(tick.time, tick.bid, tick.ask)
        last_time = tick.time
    time.sleep(0.1)
```

---

## Auto-trading / EA

1. Letakkan `.mq5` atau `.ex5` Anda di `/opt/mt5-data/.wine/drive_c/Program Files/MetaTrader 5/MQL5/Experts/`
2. Buka MT5 via noVNC → Navigator → Expert Advisors → drag ke chart
3. Pastikan **Algo Trading** ON di toolbar (icon hijau)
4. EA akan tetap jalan selama container hidup (systemd auto-restart)

---

## Gotchas

| Issue | Penyebab | Fix |
|---|---|---|
| `docker: command not found` setelah mt5-02 jalan | CT tidak ada `nesting=1` + `keyctl=1` features | Cek `/etc/pve/lxc/132.conf` ada `features: nesting=1,keyctl=1`. Restart CT. |
| Docker pull `error pulling image configuration` | Kuota Docker Hub anonymous (100/6h) | Login: `docker login` atau set rate limits via paid account |
| noVNC blank screen / "loading" terus | Container masih initialize Wine (first run) | Wait 3-5 menit. Tail logs: `docker logs mt5 --tail 100 -f`. Cari `KasmVNC started`. |
| **`[7/7] Failed to start the mt5linux server on port 8001`** | **gmag11 image start.sh pakai mt5linux API lama (`-H`), tapi pip pulls mt5linux 1.0.3 yang berubah ke `--host` AND tidak terima positional args** | **mt5-02 v2 sudah patch: tulis launcher persistent ke `/config/start-mt5linux.sh` + `mt5-rpyc.service` systemd unit yang invoke `wine python -m mt5linux --host 0.0.0.0 -p 8001` (no positional)** |
| **`ImportError: numpy.core.multiarray failed to import`** dari `mt5.initialize()` | **Wine Python pip install dapat numpy 2.x, tapi MetaTrader5 binary `_core.pyd` compiled against numpy 1.x ABI** | **mt5-02 v2: `wine python -m pip install "numpy<2"` setelah init container done. Plus kill wine processes lama supaya tidak cache numpy 2.x state.** |
| **Linux side rpyc 6.0.2 vs Wine side 5.2.3 — protocol break** | **mt5linux 1.0.3 dep resolver pin rpyc==5.2.3 di Wine tapi pull latest (6.0.2) di Linux** | **mt5-02 v2: `pip install --user --force-reinstall rpyc==5.2.3 plumbum==1.7.0 "pyparsing>=3.1.0,<4"` di Linux side** |
| `initialize()` returns `False` + `(-10004, 'No IPC connection')` | MT5 terminal GUI belum dilaunch/login. RPyC bisa connect tapi MT5 IPC server belum ada di Wine | Buka noVNC → login broker via File → Login. Setelah terminal MT5 jalan, `initialize()` return `True`. |
| MT5 GUI muncul tapi tidak bisa login | Network MT5 → broker server diblokir / latency tinggi | Cek dari host: `nc -zv broker-server.com 443`. Mungkin perlu VPN. |
| MQL5 Algo Trading icon merah | Default disabled saat fresh install | Toolbar → Algo Trading button (atau Ctrl+E). Save di File → Login → Save settings. |
| `mt5.initialize()` dari client hang | RPyC port tidak terbuka atau MT5 belum login | Cek dari client: `telnet 192.168.0.116 8001`. Pastikan MT5 sudah login broker (via noVNC). |
| `mt5linux` `pip install` gagal "rpyc not found" | Older pip cache | `pip install --upgrade rpyc mt5linux` |
| Container restart loop | OOM (RAM 4GB kurang untuk multi-account + heavy strategy) | Bump RAM: `pct set 132 -memory 6144 -swap 6144`. Atau kurangi `--shm-size`. |
| Position size dari API beda dari GUI | MT5 menghitung lot dengan precision; Python `volume` harus mod symbol step | Cek `symbol_info('EURUSD').volume_step`. Round volume ke step. |
| Container restart hilangkan login broker | Volume mount salah | Cek `/opt/mt5-data/.wine` ada isinya. `docker inspect mt5` cari `Mounts`. |

---

## Limitasi

- **MT5 versi**: auto-update dari MetaQuotes server. Bisa break custom indicator yang depend versi spesifik. Pin tag `gmag11/metatrader5_vnc:2.1` kalau Anda butuh stability.
- **Hanya 1 akun aktif per container**: untuk multi-account, jalankan multiple container dengan port + volume berbeda. CT 132 cukup untuk 2-3 instance ringan dalam RAM 4 GB.
- **Tidak ada GPU acceleration**: MT5 + indicator pakai CPU. Backtesting visual lambat (Wine + VNC layer).
- **Latency Python ↔ MT5**: RPyC over TCP nambah ~1-5ms per call. Untuk HFT, pakai EA native MQL5 di dalam MT5, jangan Python.
- **Tidak ada audio alert**: container headless, MT5 sound alerts tidak keluar. Pakai webhook / email alert via Python wrapper.
- **noVNC bandwidth**: ~50-200 KB/s saat MT5 idle, lebih saat banyak chart aktif. OK untuk LAN, OK juga untuk WAN dengan reverse proxy + auth.

---

## Security catatan

Default install **TIDAK ada auth** untuk noVNC dan RPyC. Untuk production:

1. Bind 127.0.0.1 only + reverse proxy dengan auth (Caddy / nginx + basic auth)
2. Atau pakai Wireguard / tailscale untuk network isolation
3. Atau set firewall rule di Proxmox host

Jangan expose port 3000/8001 ke internet tanpa auth — RPyC bisa execute arbitrary Python.

---

## Cleanup / uninstall

```bash
# stop container & service
pct exec 132 -- systemctl disable --now mt5

# remove Docker container + image (keeps data in /opt/mt5-data)
pct exec 132 -- docker rm -f mt5
pct exec 132 -- docker rmi gmag11/metatrader5_vnc:latest

# WIPE data too (destructive)
pct exec 132 -- rm -rf /opt/mt5-data

# destroy CT
pct stop 132 && pct destroy 132
```
