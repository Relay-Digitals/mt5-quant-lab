# Infrastructure Overview

Snapshot semua container, service, dan endpoint yang berjalan di Proxmox `192.168.0.222`.

## Host

| Item | Value |
|---|---|
| Hostname | proxmox host |
| IP | 192.168.0.222 |
| CPU | Intel i3-1215U (Alder Lake, 6 cores, no NVIDIA GPU) |
| RAM | 15 GB total |
| iGPU | Intel UHD Graphics `[0x46b3]` Xe-LP 96 EUs |
| Kernel | 6.17.13-2-pve |
| Proxmox | 9.1.7 |
| Storage | local-lvm + ZFS pool `fileserver` (1 TB HDD, ~623 GB free) |

## LXC containers

| CTID | Hostname | IP | Purpose | RAM | Disk |
|---|---|---|---|---|---|
| 100 | rathole | — | Tunnel reverse | 512 MB | — |
| 102 | fileserver | 192.168.0.103 | NFS/SMB file server | 1 GB | 8 GB |
| 103 | vscode-server | — | Remote dev | 4 GB | — |
| 104 | honk | — | Service | 1 GB | — |
| 105 | nginx | 192.168.0.108 | (idle, unused) | 512 MB | 8 GB |
| 106 | jenkins | — | CI/CD | 4 GB | — |
| 108 | tradeforge-db | — | Database | 8 GB | — |
| 114 | tradeforge-services | — | App services | 8 GB | — |
| 115 | tradeforge-registry | — | Docker registry | 2 GB | — |
| 120 | multica-server | — | App server | 1 GB | — |
| 121 | multica-daemon | — | Daemon | 4 GB | — |
| 122 | multica-daemon-2 | — | Daemon | 4 GB | — |
| **130** | **comfyui-openvino** | **192.168.0.106** | **Stable Diffusion (Intel iGPU)** | **10 GB** | **30 GB** |
| **140** | **garage** | **192.168.0.140** | **S3-compatible object storage (ZFS)** | **2 GB** | **8 GB** + 600 GB ZFS |
| **150** | **pihole** | **192.168.0.150** | **DNS + ad-block** | **1 GB** | **4 GB** |
| **151** | **caddy** | **192.168.0.151** | **HTTPS reverse proxy + internal CA** | **512 MB** | **4 GB** |
| **160** | **android** | **192.168.0.160** | **Android emulator (redroid)** | **10 GB** | **25 GB** |
| **170** | **whatsapp** | **192.168.0.170** | **WhatsApp HTTP API (WAHA)** | **1.5 GB** | **8 GB** |
| **180** | **browser** | **192.168.0.180** | **Browser automation (Browserless + Playwright MCP)** | **2.5 GB** | **12 GB** |
| **190** | **wiki** | **192.168.0.190** | **Wiki.js documentation (this site)** | **1 GB** | **8 GB** |

CT yang **bold** = built dalam project ini.

## Public endpoints (LAN-internal)

Semua via Caddy HTTPS dengan internal CA `Lab.lan Internal CA`. Install root CA dari `http://ca.lab.lan/root.crt` di tiap device.

| Service | URL HTTPS | URL HTTP direct | Auth |
|---|---|---|---|
| **Wiki** (this) | `https://wiki.lab.lan` | `http://192.168.0.190:3000` | Login admin |
| **Stable Diffusion UI** | `https://sd.lab.lan` | `http://192.168.0.106:7860` | none |
| **Garage Web UI** | `https://garage.lab.lan` | `http://192.168.0.140:3909` | root/Sudimara19 |
| **Garage S3 API** | `https://s3.lab.lan` | `http://192.168.0.140:3900` | S3 key |
| **Public file share** | `https://files.lab.lan/files-public/<file>` | `http://192.168.0.140/files-public/<file>` | anonymous (permanen) |
| **WhatsApp API (WAHA)** | `https://wa.lab.lan` | `http://192.168.0.170:3000` | X-API-Key |
| **WhatsApp Dashboard** | `https://wa.lab.lan/dashboard` | `http://192.168.0.170:3000/dashboard` | admin/Sudimara19 |
| **Browserless** | `https://browser.lab.lan` | `http://192.168.0.180:3000` | `?token=` |
| **Playwright MCP** | `https://mcp.lab.lan/mcp` | `http://192.168.0.180:8931/mcp` | none |
| **Pi-hole Admin** | — | `http://192.168.0.150/admin` | Sudimara19 |
| **CA cert download** | — | `http://ca.lab.lan/root.crt` | — |
| **ADB Android (TCP)** | — | `192.168.0.160:5555` (instance 1), `:5556` (2), … | — |

## DNS

Pi-hole di CT 150 (`192.168.0.150`) — DNS server LAN-wide.

| Hostname | Resolve ke |
|---|---|
| `wiki.lab.lan` | 192.168.0.151 → Caddy → 192.168.0.190:3000 |
| `sd.lab.lan` | 192.168.0.151 → Caddy → 192.168.0.106:7860 |
| `garage.lab.lan` | 192.168.0.151 → Caddy → 192.168.0.140:3909 |
| `files.lab.lan` | 192.168.0.151 → Caddy → 192.168.0.140:80 (nginx → s3_web vhost) |
| `s3.lab.lan` | 192.168.0.151 → Caddy → 192.168.0.140:3900 |
| `wa.lab.lan` | 192.168.0.151 → Caddy → 192.168.0.170:3000 |
| `browser.lab.lan` | 192.168.0.151 → Caddy → 192.168.0.180:3000 |
| `mcp.lab.lan` | 192.168.0.151 → Caddy → 192.168.0.180:8931 |
| `ca.lab.lan` | 192.168.0.151 → Caddy → root CA file server |

Update DNS: `pct exec 150 -- pihole-FTL --config dns.hosts '[ ... ]'` lalu `systemctl restart pihole-FTL`.

## Resource utilization (steady state)

```
Host RAM 15 GB:
├── 0.5 GB Proxmox overhead
├── 0.5 GB CT 100 rathole
├── 1.0 GB CT 102 fileserver
├── 4.0 GB CT 103 vscode-server
├── 1.0 GB CT 104 honk
├── 0.5 GB CT 105 nginx
├── 4.0 GB CT 106 jenkins
├── 1.5 GB CT 130 SD (idle, scales on inference)
├── 0.2 GB CT 140 garage (idle)
├── 0.4 GB CT 150 pihole
├── 0.1 GB CT 151 caddy
├── 1.5 GB CT 160 android (per instance)
├── 0.3 GB CT 170 WAHA (NOWEB engine)
├── 1.0 GB CT 180 browser
└── 0.4 GB CT 190 wiki
```

Total commit ~16 GB tapi actual usage biasanya overcommit ratio 60-70% — Linux memory accounting fleksibel.

## Storage

| Pool | Total | Used | Free | Purpose |
|---|---|---|---|---|
| `local-lvm` (HDD) | 358 GB | ~80 GB | ~280 GB | CT rootfs |
| `local` (HDD) | 100 GB | ~20 GB | ~80 GB | Templates + ISO |
| `fileserver` (ZFS HDD) | 943 GB | ~290 GB | ~625 GB | Bulk data (Garage objects, backup) |

## Network topology

```
                    Internet
                       │
                  [Router 192.168.0.1]
                       │
                  [LAN 192.168.0.0/24]
                       │
        ┌──────────────┼──────────────────┐
        │              │                  │
   [Mac client]   [Proxmox host       [other client]
                   192.168.0.222]
                       │
                  vmbr0 bridge
                       │
        ┌──────────────┼──────────────────────┐
        │              │                       │
    CT 130 SD     CT 140 Garage    ...    CT 190 Wiki
    .106          .140                     .190

                  [Pi-hole CT 150 = DNS]
                  [Caddy CT 151 = HTTPS proxy + CA]
```

## Backup checklist

| What | Where | Frequency | Status |
|---|---|---|---|
| Wiki SQLite database | `wiki_data` volume di CT 190 | Daily | TODO |
| WAHA session data | `waha_sessions` volume di CT 170 | Weekly | TODO |
| Garage object data | `fileserver/garage` ZFS dataset | ZFS snapshot daily | TODO |
| Stable Diffusion models | `/opt/sd-openvino/models` di CT 130 | (no — re-downloadable) | OK |
| Caddy data + CA | `/var/lib/caddy` di CT 151 | Weekly | TODO |
| Pi-hole config | `/etc/pihole` di CT 150 | Weekly | TODO |
| Proxmox cluster config | `/etc/pve` host | via `pve-zsync` / `vzdump` | TODO |

## Roadmap / TODO

- [ ] Automated backup cron for all critical CTs
- [ ] Prometheus + Grafana monitoring CT (CT 200?)
- [ ] Nightly ZFS snapshot rotation
- [ ] Healthcheck CT (CT 201?) — auto-restart misbehaving services
- [ ] Document Garage S3 client examples (boto3, mc, rclone)
- [ ] Document redroid workflow (APK install, scrcpy)
- [ ] Add Mac/iOS client setup for `*.lab.lan` (DNS + CA)

---

_Last updated by bulk upload script. Edit langsung via Wiki.js UI atau via GraphQL._
