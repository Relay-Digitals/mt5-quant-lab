Sudah selesai. Semua active dan terverifikasi end-to-end.

  Akses (LAN)

  ┌────────────────┬───────────────────────────────────────────────┬─────────────────────────────────────┐
  │    Layanan     │                      URL                      │                Login                │
  ├────────────────┼───────────────────────────────────────────────┼─────────────────────────────────────┤
  │ Web UI         │ http://192.168.0.140:3909                     │ root / Sudimara19 (bcrypt)          │
  ├────────────────┼───────────────────────────────────────────────┼─────────────────────────────────────┤
  │ Landing        │ http://192.168.0.140/                         │ —                                   │
  ├────────────────┼───────────────────────────────────────────────┼─────────────────────────────────────┤
  │ File publik    │ http://192.168.0.140/files-public/<filename>  │ anonymous (permanen)                │
  ├────────────────┼───────────────────────────────────────────────┼─────────────────────────────────────┤
  │ S3 API         │ http://192.168.0.140:3900                     │ access key (di bawah)               │
  ├────────────────┼───────────────────────────────────────────────┼─────────────────────────────────────┤
  │ S3 Web (vhost) │ http://192.168.0.140:3902 (butuh Host header) │ anonymous untuk bucket files-public │
  └────────────────┴───────────────────────────────────────────────┴─────────────────────────────────────┘

  S3 credentials

  endpoint   = http://192.168.0.140:3900
  region     = garage
  access_key = GK83ba3b274057e88a11378da6
  secret_key = d39dd7615208fcb7f981d2ede182f4256f62fe3ccc69cec2da0017050616356a

  Catat dan simpan — secret tidak bisa di-show lagi tanpa garage key info admin-key --show-secret.

  Bucket

  ┌───────────────┬─────────────────┬───────────────────────────────────────────────────────────────────────────┐
  │    Bucket     │      Mode       │                                   Akses                                   │
  ├───────────────┼─────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ files-public  │ Website mode ON │ Anyone via http://192.168.0.140/files-public/<key> (permanent, no expiry) │
  ├───────────────┼─────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ files-private │ Standard        │ Hanya dengan S3 key                                                       │
  └───────────────┴─────────────────┴───────────────────────────────────────────────────────────────────────────┘

  Storage

  - ZFS dataset: fileserver/garage (LZ4 compress, atime off, xattr=sa)
  - Mount in CT: /mnt/garage → /mnt/garage/data + /mnt/garage/meta
  - Capacity: 600 GB allocated, 623 GB physical free
  - CT 140: 2 GB RAM, 1 GB swap, 8 GB root disk

  Smoke test

  # upload (dari client manapun yang punya aws cli)
  aws --endpoint-url http://192.168.0.140:3900 \
      --profile garage s3 cp myfile.pdf s3://files-public/myfile.pdf

  # share URL ini bisa diakses siapa saja, permanen:
  http://192.168.0.140/files-public/myfile.pdf

  ├─────────────┼─────────────────────────────────────────────────────────────┤
  │ Logs Garage │ pct exec 140 -- journalctl -u garage -f                     │
  ├─────────────┼─────────────────────────────────────────────────────────────┤
  │ Logs WebUI  │ pct exec 140 -- journalctl -u garage-webui -f               │
  ├─────────────┼─────────────────────────────────────────────────────────────┤
  │ Restart     │ pct exec 140 -- systemctl restart garage garage-webui nginx │
  ├─────────────┼─────────────────────────────────────────────────────────────┤
  │ CLI Garage  │ pct exec 140 -- /usr/local/bin/garage <command>             │
  ├─────────────┼─────────────────────────────────────────────────────────────┤
  │ Bucket info │ pct exec 140 -- garage bucket info files-public             │
  └─────────────┴─────────────────────────────────────────────────────────────┘

  Catatan

  - "Permanen" = Garage tidak punya lifecycle expiration default. File tetap ada sampai dihapus manual.
  - Untuk upload besar pakai S3 multipart (aws cli + s3api otomatis split di >8MB).
  - Mau ekspos ke internet? Tambah reverse proxy + Let's Encrypt — atau gunakan rathole CT 100 yang sudah ada.
  - Web UI tidak punya audit log built-in. Akses log via nginx + journalctl.
  - Replication factor = 1 (single node). Tidak ada redundansi data di luar yang ZFS sudah berikan.

  Total runtime resources baru: ~50 MB RAM (Garage idle) + ZFS metadata cache. Tidak akan mengganggu workload existing.



  di proxmox saya ingin ada android emulator untuk testing pengembangan yg bisa konek via tcpip
  di proxmox saya ingin ada whatsapp bot untuk otp
  di proxmox saya ingin ada web crawler / mcp browser bisa auto fill dan submit form, scroll dan lainnya dan bisa program able
  di proxmox saya ingin punya wiki web untuk dokumentasi semua riset, semua configurasi service, db, etc
  di proxmox saya ingin punya smtp mail server sendiri untuk pengembangan dan bisa diakses dari internet juga via rathole dan bisa jualan smpt server juga 
