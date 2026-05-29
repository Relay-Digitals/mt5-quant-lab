# Stable Diffusion (OpenVINO) di Proxmox LXC

Setup self-hosted image generation menggunakan Intel iGPU lewat OpenVINO, di CT Proxmox.
Tidak butuh GPU NVIDIA. Akses via web UI.

**Host:** Proxmox 9.1, Intel i3-1215U (Alder Lake), 15 GB RAM, Intel UHD iGPU
**CT:** 130 `comfyui-openvino` (Debian 12, privileged, 10 GB RAM / 4 GB swap / 4 core / 30 GB disk)
**Akses:** http://192.168.0.106:7860

---

## Arsitektur singkat

```
Proxmox host (192.168.0.222)
  └── i915 + xe kernel modules (Intel UHD)
       └── /dev/dri/{card1, renderD128}                   ← di-bind ke CT
            └── LXC CT 130 (privileged)
                 ├── intel-opencl-icd (OpenCL ICD)
                 ├── OpenVINO 2026.2 + openvino-genai
                 │    └── Pipeline Text2ImagePipeline (device="GPU")
                 └── Gradio 6.15 di :7860 (systemd service)
                      └── Model registry (SDXL-Turbo, SD1.5 FP16, SD1.5 INT8)
```

Kunci: iGPU di-passthrough sebagai device node, **bukan** VFIO/PCIe passthrough.
Driver kernel tetap di host, CT cuma punya userspace OpenCL/Level-Zero runtime.

---

## Reproduksi dari nol

### 1. Buat CT dengan iGPU passthrough

Di Proxmox host (`root@192.168.0.222`):

```bash
# template
pveam update
pveam download local debian-12-standard_12.12-1_amd64.tar.zst

# CT (privileged untuk simplisitas pass-through)
pct create 130 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname comfyui-openvino \
  --cores 4 --memory 10240 --swap 4096 \
  --rootfs local-lvm:30 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp,firewall=0 \
  --features nesting=1 \
  --unprivileged 0 --onboot 1 \
  --password 'CHANGEME' --start 0

# iGPU passthrough (DRM major = 226)
cat >> /etc/pve/lxc/130.conf <<'EOF'

# Intel iGPU passthrough
lxc.cgroup2.devices.allow: c 226:* rwm
lxc.mount.entry: /dev/dri dev/dri none bind,optional,create=dir
EOF

pct start 130
pct exec 130 -- ls /dev/dri  # harus muncul: card1, renderD128, by-path
```

### 2. Install Intel runtime di CT

```bash
pct exec 130 -- bash -c "
sed -i 's|bookworm main|bookworm main contrib non-free non-free-firmware|' /etc/apt/sources.list
sed -i 's|bookworm-updates main|bookworm-updates main contrib non-free non-free-firmware|' /etc/apt/sources.list
sed -i 's|bookworm-security main|bookworm-security main contrib non-free non-free-firmware|' /etc/apt/sources.list
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  ca-certificates curl wget git python3 python3-venv python3-pip python3-dev \
  build-essential pkg-config libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 ffmpeg \
  intel-opencl-icd intel-media-va-driver intel-gpu-tools \
  ocl-icd-libopencl1 clinfo vainfo libtbb12 libtbbmalloc2 numactl
clinfo -l  # harus muncul: Intel(R) Graphics [0x46b3]
"
```

### 3. Install OpenVINO + Gradio

```bash
pct exec 130 -- bash -c "
mkdir -p /opt/sd-openvino && cd /opt/sd-openvino
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel
pip install openvino-genai openvino-tokenizers gradio pillow huggingface-hub transformers

# verifikasi iGPU terlihat OpenVINO
python -c 'from openvino import Core; [print(d, Core().get_property(d, \"FULL_DEVICE_NAME\")) for d in Core().available_devices]'
# harus muncul: GPU -> Intel(R) Graphics [0x46b3] (iGPU)
"
```

### 4. Download model

```bash
pct exec 130 -- bash -c "
cd /opt/sd-openvino && source venv/bin/activate

# SD 1.5 FP16 (3.2 GB)
hf download OpenVINO/stable-diffusion-v1-5-fp16-ov --local-dir models/sd15-fp16

# SDXL-Turbo INT8 (4.5 GB) — rekomendasi utama untuk fotorealistik
hf download rupeshs/sdxl-turbo-openvino-int8 --local-dir models/sdxl-turbo-int8
"
```

### 5. Patch SDXL-Turbo (lihat **Gotchas** di bawah)

```bash
pct exec 130 -- bash -c "
cd /opt/sd-openvino && source venv/bin/activate

# patch class name (Img2Img -> Txt2Img)
sed -i 's/StableDiffusionXLImg2ImgPipeline/StableDiffusionXLPipeline/' \
  models/sdxl-turbo-int8/model_index.json

# convert tokenizers (i32 untuk tokenizer, i64 untuk tokenizer_2)
python <<'EOF'
from transformers import AutoTokenizer
from openvino_tokenizers import convert_tokenizer
import openvino as ov
from openvino import Type
MODEL = '/opt/sd-openvino/models/sdxl-turbo-int8'
for sub, dt in [('tokenizer', Type.i32), ('tokenizer_2', Type.i64)]:
    tok = AutoTokenizer.from_pretrained(f'{MODEL}/{sub}')
    ov_model = convert_tokenizer(tok, tokenizer_output_type=dt)
    if isinstance(ov_model, tuple): ov_model = ov_model[0]
    ov.save_model(ov_model, f'{MODEL}/{sub}/openvino_tokenizer.xml')
EOF
"
```

### 6. Deploy app + systemd

Push `sd_app.py` (lihat repo lokal) ke `/opt/sd-openvino/app.py`, lalu:

```bash
cat > /tmp/sd-openvino.service <<'EOF'
[Unit]
Description=Stable Diffusion (OpenVINO, Intel iGPU)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/sd-openvino
Environment="OV_DEVICE=GPU"
Environment="HOST=0.0.0.0"
Environment="PORT=7860"
Environment="OV_CACHE_DIR=/opt/sd-openvino/ov_cache"
ExecStart=/opt/sd-openvino/venv/bin/python /opt/sd-openvino/app.py
Restart=on-failure
RestartSec=10
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

pct push 130 /tmp/sd-openvino.service /etc/systemd/system/sd-openvino.service
pct exec 130 -- systemctl daemon-reload
pct exec 130 -- systemctl enable --now sd-openvino.service
```

---

## Struktur file di CT

```
/opt/sd-openvino/
├── app.py                  # Gradio frontend (multi-model dropdown)
├── venv/                   # Python virtualenv (~1 GB)
├── ov_cache/               # OpenCL kernel cache (auto-managed)
├── smoke_test.py           # CLI smoke test
└── models/
    ├── sd15-fp16/          # 3.2 GB
    ├── sd15-int8/          # 2.2 GB (legacy, bisa dihapus)
    └── sdxl-turbo-int8/    # 4.5 GB (default, fotorealistik)

/etc/systemd/system/sd-openvino.service
```

---

## Operasi sehari-hari

| Aksi | Perintah (di host) |
|---|---|
| Buka UI | http://192.168.0.106:7860 |
| Lihat logs | `pct exec 130 -- journalctl -u sd-openvino -f` |
| Restart | `pct exec 130 -- systemctl restart sd-openvino` |
| Status | `pct exec 130 -- systemctl status sd-openvino` |
| Masuk CT | `pct enter 130` |
| Cek iGPU dalam CT | `pct exec 130 -- clinfo -l` |
| Memory CT | `pct exec 130 -- free -h` |

---

## Performance (Intel UHD i3-1215U, 512×512)

Pertama kali pakai resolusi/model baru = +30 detik (kompilasi kernel, di-cache).

| Model | Steps | Waktu | Use case |
|---|---|---|---|
| SDXL-Turbo INT8 | 1 | ~29s | Quick draft |
| **SDXL-Turbo INT8** | **4** | **~22s** | **Default (foto realistik)** |
| SD 1.5 FP16 | 25 | ~149s | Saat butuh negative prompt |
| SD 1.5 INT8 | 20 | ~100s | Fallback ringan |

---

## Menambah model baru

1. Download model OpenVINO IR ke `models/<name>/` (lewat `hf download` atau convert `optimum-cli export openvino`)
2. Tambahkan entry di `REGISTRY` dict di `app.py`:
   ```python
   "my-model": {
       "path": f"{MODELS_ROOT}/my-model-dir",
       "label": "My Model — desc",
       "steps": 20, "max_steps": 30,
       "cfg": 7.5, "size": 512,
       "tip": "optional tip",
   },
   ```
3. Restart service: `systemctl restart sd-openvino`

Model muncul otomatis di dropdown kalau path-nya ada.

---

## Gotchas (issue yang sempat muncul, beserta fix-nya)

| Issue | Cause | Fix |
|---|---|---|
| `intel-media-va-driver-non-free` not found | Bookworm default tidak include `non-free` | Enable contrib + non-free + non-free-firmware di `/etc/apt/sources.list` |
| `huggingface-cli` deprecated | HF Hub library 1.0+ | Pakai `hf download` (perintah baru) |
| Gradio `Blocks.launch() got unexpected kwarg 'show_api'` | Gradio 6 API change | Hapus param dari `.launch()` |
| Gradio warn "theme moved to launch()" | Gradio 6 API change | Pindah `theme=` dari `Blocks(...)` ke `.launch(theme=...)` (opsional) |
| `Unsupported pipeline 'StableDiffusionXLImg2ImgPipeline'` | rupeshs/sdxl-turbo export salah class name | `sed -i 's/StableDiffusionXLImg2ImgPipeline/StableDiffusionXLPipeline/' model_index.json` |
| `openvino_tokenizer.xml was not provided` | rupeshs repo cuma include HF tokenizer files | Convert: `openvino_tokenizers.convert_tokenizer()` |
| `Tensor i64 not representable as pointer to i32` | tokenizer output type ≠ text_encoder input type | Tokenizer: `Type.i32`. Tokenizer_2: `Type.i64` (cek dengan `grep element_type text_encoder*/openvino_model.xml`) |
| `Guidance scale ≤ 1.0 ignores negative prompt` | openvino-genai strict | Skip `negative_prompt` kwarg saat CFG ≤ 1.0 (untuk Turbo/LCM) |
| OOM kill saat load SDXL atau download besar | CT memory cap kekecilan | Bump `pct set 130 -memory 10240 -swap 4096` |
| Service systemd restart loop | First app crash + `Restart=on-failure` | Cek logs penyebab: `journalctl -u sd-openvino -n 100` |

---

## Limitasi

- **Tidak ada NVIDIA GPU** → video gen (LTX-Video/HunyuanVideo/dll) **tidak feasible** di hardware ini. Untuk video, perlu sewa GPU cloud (Runpod/Modal/Replicate) atau upgrade hardware.
- iGPU Intel UHD Xe-LP 96 EUs → maksimal sekitar 22s/image SDXL-Turbo 512px. Tidak akan mendekati performa GPU diskrit.
- 10 GB RAM cap → SDXL base FP16 (~6.5 GB resident) muat tapi tight. SD3.5/Flux **tidak feasible**.
- Resolusi >768 kemungkinan OOM atau sangat lambat.

---

## Cleanup / uninstall

```bash
# stop & disable service
pct exec 130 -- systemctl disable --now sd-openvino.service

# hapus CT (destruktif)
pct stop 130 && pct destroy 130
```
