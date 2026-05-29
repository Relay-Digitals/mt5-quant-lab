# Self-Hosted Coding LLM (Qwen2.5-Coder + IPEX-LLM) di Proxmox LXC

Self-hosted "Claude-like" coding assistant pakai Intel iGPU lewat IPEX-LLM,
di CT Proxmox. Tidak butuh GPU NVIDIA. Stack lengkap: chat UI, web IDE,
dan IDE-integrated autocomplete.

**Host:** Proxmox 9.1, Intel i3-1215U (Alder Lake), 15 GB RAM, Intel UHD iGPU
**CT 131:** `ai-coder` (Debian 12, privileged, 6 GB RAM / 8 GB swap / 4 core / 50 GB disk) — IP `192.168.0.123`
**Berdampingan dengan:**
- CT 130 `comfyui-openvino` (Stable Diffusion — lihat `SETUP.md`)
- CT 103 `vscode-server` (code-server existing — kita extend dengan Continue.dev)

| Komponen | Lokasi | URL | Fungsi |
|---|---|---|---|
| **Open WebUI** | CT 131 | `http://192.168.0.123:3000` | Chat UI ala Claude/ChatGPT, multi-model, RAG dokumen |
| **Ollama API** | CT 131 | `http://192.168.0.123:11434` | IPEX-LLM Ollama 0.5.4, iGPU accelerated via SYCL/Level Zero |
| **code-server** | CT 103 | `http://192.168.0.<ct103>:8080` | VS Code di browser (existing) — extended dengan Continue.dev |
| **Continue.dev** | CT 103 | `Ctrl+L` di code-server | IDE chat/autocomplete, pointing ke CT 131 Ollama |

---

## Kenapa stack ini

| Kebutuhan | Pilihan | Alternatif yang ditolak | Alasan |
|---|---|---|---|
| Model coding open source | **Qwen2.5-Coder 7B/14B** | DeepSeek-V3 685B, Llama-3.3 70B | Performa coding mendekati Claude Sonnet 3.5 di HumanEval/LiveCodeBench, sekaligus muat di iGPU + 8 GB RAM |
| Inference engine | **IPEX-LLM Ollama** | vanilla Ollama (CPU), llama.cpp SYCL manual | Intel-optimized fork dengan Level Zero/SYCL backend → 2-3× lebih cepat dari CPU murni di iGPU Anda |
| Chat UI | **Open WebUI** | LibreChat, AnythingLLM | Paling matang, RAG bawaan, multi-user, mirip ChatGPT |
| Web IDE | **code-server** | OpenVSCode Server, Gitpod | Standar de facto, ringan, extension marketplace lengkap |
| IDE bridge | **Continue.dev** | Cline, Aider, Cody | Pure open source, autocomplete + chat + edit, native Ollama support |
| RAG embeddings | **nomic-embed-text** (via Ollama) | sentence-transformers internal Open WebUI | Reuse Ollama, hemat RAM, lebih cepat di iGPU |

---

## Arsitektur

```
Proxmox host (192.168.0.222)
  └── i915 + xe kernel modules (Intel UHD)
       └── /dev/dri/{card1, renderD128}     ← bind ke CT 130 DAN CT 131
            ├── CT 130 comfyui-openvino  (image gen — lihat SETUP.md)
            └── CT 131 ai-coder
                 ├── intel-opencl-icd + libtbb (oneAPI/Level Zero userspace)
                 ├── IPEX-LLM Ollama  → :11434  (systemd: ipex-ollama.service)
                 │    ├── qwen2.5-coder:7b           (chat)
                 │    ├── qwen2.5-coder:1.5b-base    (autocomplete)
                 │    └── nomic-embed-text           (RAG embed)
                 ├── Open WebUI       → :3000   (systemd: open-webui.service)
                 │    └── DATA_DIR + RAG → Ollama embedding
                 └── code-server      → :8443   (systemd: code-server@root)
                      └── Continue.dev extension → http://localhost:11434
```

iGPU **shared antara CT 130 dan CT 131** lewat device-node passthrough (DRM
major 226). Kernel driver tetap di host; CT cuma punya userspace runtime.
Tidak konflik karena Ollama dan SD jarang jalan barengan kalau RAM
masih sempit — dan iGPU sendiri bisa time-share workload.

---

## Reproduksi dari nol

### 1. Buat CT 131 (jalankan di Proxmox host)

```bash
# dari mesin Anda, push script ke host lalu jalankan
scp llm-01-host-create-ct.sh root@192.168.0.222:/root/
ssh root@192.168.0.222 'bash /root/llm-01-host-create-ct.sh'
```

Output akhir akan kasih tahu IP CT-nya, misal `192.168.0.107`.

### 2. Provision dalam CT

```bash
# masih dari host:
pct push 131 llm-02-container-setup.sh /root/llm-02-container-setup.sh
pct push 131 llm-03-models-pull.sh     /root/llm-03-models-pull.sh
pct exec 131 -- bash /root/llm-02-container-setup.sh
```

Script akan:
- enable contrib + non-free repo (untuk intel-media-va-driver)
- install Intel OpenCL/Level Zero userspace
- download + setup IPEX-LLM portable Ollama
- pip install Open WebUI di venv terpisah
- install code-server + Continue.dev extension
- pre-configure `~/.continue/config.yaml` untuk Ollama lokal
- start 3 systemd services
- simpan kredensial ke `/root/AI-CODER-INFO.txt`

### 3. Pull models (~6 GB)

```bash
pct exec 131 -- bash /root/llm-03-models-pull.sh
```

Default pull: `qwen2.5-coder:7b`, `qwen2.5-coder:1.5b-base`, `nomic-embed-text`.
Edit script kalau mau model lain.

### 4. Pakai

1. Buka `http://<ct-ip>:3000` → buat akun admin (user pertama otomatis admin)
2. Di chat, model `qwen2.5-coder:7b` sudah terdeteksi otomatis dari Ollama
3. Buka `http://<ct-ip>:8443` → login dengan password di `/root/AI-CODER-INFO.txt`
4. Di code-server, panel Continue (Ctrl+L untuk chat, Ctrl+I untuk inline edit) sudah terhubung ke Ollama

---

## Struktur file di CT

```
/opt/ai-coder/
├── ipex-ollama/              # IPEX-LLM portable Ollama binary + libs
│   └── ollama                # binary (juga di /usr/local/bin/ollama shim)
├── open-webui/
│   ├── venv/                 # Python venv (~1 GB)
│   └── data/                 # chats, users, RAG indexes, vector DB
├── code-server/
│   └── workspace/            # default workspace folder
└── models/                   # Ollama model blobs (~6 GB default)

/etc/systemd/system/
├── ipex-ollama.service
├── open-webui.service
└── (code-server@root.service — dibuat oleh installer)

/root/
├── .config/code-server/config.yaml   # port + password code-server
├── .continue/config.yaml              # Continue.dev: model → Ollama
└── AI-CODER-INFO.txt                  # ringkasan kredensial
```

---

## Operasi sehari-hari

| Aksi | Perintah (di host) |
|---|---|
| Buka chat | http://192.168.0.\<ip\>:3000 |
| Buka IDE | http://192.168.0.\<ip\>:8443 |
| Logs Ollama | `pct exec 131 -- journalctl -u ipex-ollama -f` |
| Logs Open WebUI | `pct exec 131 -- journalctl -u open-webui -f` |
| Logs code-server | `pct exec 131 -- journalctl -u code-server@root -f` |
| Restart Ollama | `pct exec 131 -- systemctl restart ipex-ollama` |
| Restart Open WebUI | `pct exec 131 -- systemctl restart open-webui` |
| List models | `pct exec 131 -- ollama list` |
| Pull model baru | `pct exec 131 -- ollama pull <model>:<tag>` |
| Cek iGPU dalam CT | `pct exec 131 -- clinfo -l` |
| Memory CT | `pct exec 131 -- free -h` |
| Lihat password code-server | `pct exec 131 -- cat /root/AI-CODER-INFO.txt` |

---

## Performance aktual (deployment 2026-05-28)

Diukur on-host setelah pertama kali load. Pertama load model = +32 detik
(kompilasi SYCL kernel, di-cache di `~/.cache/syclcache`).

| Model | Quant | RAM resident | Throughput (token/s) — **measured** | Use case |
|---|---|---|---|---|
| qwen2.5-coder:1.5b-base | Q4_K_M | ~1.0 GB | ~15-25 (est.) | Autocomplete (Continue.dev FIM) |
| **qwen2.5-coder:7b** | **Q4_K_M** | **~4.7 GB** | **~6 generation / ~5 PP** | **Default chat / edit** |
| qwen2.5-coder:14b | Q4_K_M | ~9.0 GB | 3-4 (est.) | Lebih akurat — swap-heavy di 6 GB CT |
| deepseek-coder-v2:16b (MoE) | Q4_K_M | ~9.4 GB | 5-8 (est.) | 2.4B aktif → cepat untuk ukurannya |

**Honest take:** ~6 tok/s untuk Qwen 7B di iGPU UHD adalah angka realistic, bukan optimal.
Cukup untuk Q&A pendek, refactor 20-50 baris, autocomplete short. Bukan untuk generate
file 500 baris dalam satu shot. Untuk "merasa seperti Claude" responsif, **stick di 7B**.
14B-ke-atas baru bermakna kalau Anda upgrade hardware (16+ GB RAM, ideally
dGPU). Tapi untuk pekerjaan coding sehari-hari, Qwen 7B sudah sangat
kompeten — leaderboard LiveCodeBench menempatkannya di tier yang sama
dengan GPT-4o mini dan Claude 3 Haiku.

---

## Continue.dev — IDE integration

Pre-configured di `/root/.continue/config.yaml`. Keybindings utama:

| Shortcut | Aksi |
|---|---|
| `Ctrl+L` | Chat sidebar (tanya / minta jelaskan / refactor) |
| `Ctrl+I` | Inline edit (highlight kode → minta perubahan) |
| `Tab` | Accept autocomplete |
| `@codebase` | Inject seluruh workspace ke context (RAG via nomic-embed) |
| `@docs` | Tambah dokumentasi external |
| `@terminal` | Inject output terminal terakhir |

Edit `config.yaml` untuk ganti model default, atau tambah provider lain
(OpenAI-compatible, OpenRouter, dll).

---

## Open WebUI tips

- **Default model**: Profile → Settings → General → "Default Model"
- **System prompt**: Profile → Settings → General → "System Prompt" — bagus untuk inject persona "senior software engineer"
- **RAG dokumen**: Workspace → Knowledge → Create → upload PDF/markdown/code repo. Akan di-embed pakai `nomic-embed-text` via Ollama.
- **Code interpreter**: Settings → Admin → Code Execution → enable Pyodide untuk eksekusi Python di sandbox browser
- **Multi-user**: signup default enabled. Disable lewat env `ENABLE_SIGNUP=false` setelah akun admin dibuat.

---

## Menambah / ganti model

```bash
pct exec 131 -- ollama pull <namespace>/<model>:<tag>

# contoh model coding open source lain yang kompatibel:
ollama pull codegemma:7b                # Google
ollama pull codellama:13b               # Meta (klasik, masih solid)
ollama pull starcoder2:7b               # BigCode
ollama pull granite-code:8b             # IBM
ollama pull yi-coder:9b                 # 01.AI
ollama pull deepseek-coder-v2:16b       # DeepSeek MoE
```

Setelah pull, model langsung muncul di dropdown Open WebUI. Untuk Continue.dev,
edit `/root/.continue/config.yaml` dan reload window (`Ctrl+Shift+P` → "Continue: Reload Config").

---

## Gotchas (issue yang mungkin muncul)

| Issue | Penyebab | Fix |
|---|---|---|
| `clinfo -l` kosong di CT | `/dev/dri` belum di-passthrough atau permisi salah | Cek `lxc.cgroup2.devices.allow: c 226:* rwm` di `/etc/pve/lxc/131.conf`. Restart CT. |
| `intel-media-va-driver` not found | Bookworm default tidak include `non-free` | Script sudah enable. Cek `/etc/apt/sources.list` ada `contrib non-free non-free-firmware`. |
| **Ollama crash dengan `sycl::_V1::exception: No device of requested type`** | **Debian Bookworm libze1 1.8.x + libze_intel_gpu 1.3.x (Jan 2023) terlalu tua untuk IPEX-LLM 2025** | **Pakai Intel Graphics repo Ubuntu jammy → install `libze1` 1.21.x + `libze-intel-gpu1` 25.x (script v2 sudah handle). Conflict dengan legacy `intel-level-zero-gpu` package — jangan install yang itu.** |
| IPEX-LLM Ollama URL gagal auto-resolve | Repo distribution di `ipex-llm/ipex-llm` (mirror), **bukan** `intel/ipex-llm` | Script v2 sudah fallback ke stable v2.2.0. Manual override: `IPEX_OLLAMA_URL=https://github.com/ipex-llm/ipex-llm/releases/download/v2.2.0/ollama-ipex-llm-2.2.0-ubuntu.tgz`. |
| Open WebUI pip install download ~2.5 GB NVIDIA CUDA wheels | Default PyTorch wheel includes CUDA | Script v2 install `torch` dari `--index-url https://download.pytorch.org/whl/cpu` dulu sebelum `open-webui`. Saves ~2.5 GB & ~15 min. |
| `ollama` command not found setelah install | `/usr/local/bin` tidak di PATH default Debian non-login shell | Script v2 set `PATH=/usr/local/bin:...` di `/etc/environment`. Workaround: pakai full path `/usr/local/bin/ollama`. |
| `sudo: command not found` saat run llm-04 di CT 103 | Minimal LXC tanpa sudo | Script llm-04 v2 deteksi root dan skip sudo. |
| Inference jatuh ke CPU (lambat) | SYCL/Level Zero gagal initialize | Cek `journalctl -u ipex-ollama` cari "SYCL" / "Level Zero". Verifikasi `clinfo -l` shows iGPU. Pastikan `ZES_ENABLE_SYSMAN=1` env terset. |
| Open WebUI tidak lihat model | `OLLAMA_BASE_URL` salah | Cek env service: `systemctl show open-webui --property=Environment`. Restart. |
| Open WebUI install gagal (PyTorch wheel) | Bookworm Python 3.11 di CT, PyTorch wheel CPU saja butuh banyak disk | Pastikan disk CT ≥50 GB. PyTorch CPU wheel ~800 MB. |
| code-server "command not found: code-server" | install script gagal | Re-run: `curl -fsSL https://code-server.dev/install.sh \| sh`. Cek apakah `/usr/bin/code-server` ada. |
| Continue.dev tidak bisa connect | `apiBase` salah / firewall | Test: dari terminal code-server `curl http://localhost:11434/api/tags`. Edit `~/.continue/config.yaml` jika port custom. |
| OOM saat load 14B di 8 GB | Memang kekecilan | Pindah ke 7B, atau bump CT RAM: `pct set 131 -memory 12288 -swap 12288` (kurangi alokasi CT 130 dulu). |
| Pull model gagal di tengah | Network glitch | `ollama pull <model>` resumable, jalankan ulang. |
| RAG embedding super lambat | nomic-embed-text belum di-pull | `ollama pull nomic-embed-text`. Pertama kali pakai jalan lama (kernel compile). |
| Continue autocomplete tidak muncul | model `:1.5b-base` belum di-pull | Pull: `ollama pull qwen2.5-coder:1.5b-base`. Tag `-base` penting (FIM tokens), bukan instruct. |

---

## Limitasi

- **Tidak ada GPU NVIDIA** → tidak bisa jalankan model >14B dengan throughput layak. Jangan harap o1/Claude Opus-tier reasoning lokal.
- **iGPU Intel UHD 96 EUs + 8 GB RAM** → bottleneck di prompt processing (PP) untuk context panjang. Context >8k token akan terasa pelan.
- **Tidak ada vision/multimodal** di stack default. Tambah `llava` atau `qwen2-vl` model jika butuh image input — tapi performa di iGPU sangat terbatas.
- **Tidak ada tool-use / function calling reliable** di model 7B lokal — jangan harap agent autonomous seperti Claude dengan computer-use.
- **Coexistence dengan CT 130 (SD)**: kalau jalan barengan di iGPU, throughput keduanya turun ~50%. Idealnya pakai satu-satu.

---

## Upgrade path

Kalau di kemudian hari upgrade hardware:

| Hardware baru | Model recommended | Engine |
|---|---|---|
| 32 GB RAM + Intel Arc A380 (~$130) | qwen2.5-coder:14b Q5 / codestral:22b Q4 | IPEX-LLM (sama stack) |
| RTX 3060 12 GB | qwen2.5-coder:14b FP16 / 32b Q4 | vanilla Ollama CUDA |
| RTX 4090 24 GB | qwen2.5-coder:32b FP16 / deepseek-v3-distill | vLLM / Ollama CUDA |

Stack yang sama (Open WebUI + code-server + Continue.dev) tidak berubah, cuma swap engine di belakang Ollama API.

---

## Cleanup / uninstall

```bash
# stop services
pct exec 131 -- systemctl disable --now ipex-ollama open-webui code-server@root

# hapus CT (destruktif)
pct stop 131 && pct destroy 131
```
