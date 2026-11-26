# Kantor AI Qukis

Tim agent AI yang tiap pagi (06.30 WIB) membaca 4 web bisnis, menulis laporan, menyambungkan konten dengan penjualan per brand, lalu menampilkannya di:

- **Dashboard laporan**: ringkasan, saran, dan laporan per web.
- **Kantor 3D** (fork [Claw3D](https://github.com/iamlukethedev/Claw3D), MIT): agent bekerja di meja saat ada kerjaan; saat santai mereka ngopi, nonton TV, atau tidur.

| Agent | Sumber |
|---|---|
| Pelapor Konten | qukistudio.com |
| Pelapor TikTok | cms-tiktok-qks |
| Pelapor TaQis | qukis.web.id |
| Pelapor Keuangan | qks.smartup.id |
| Analis | gabungan keempatnya |
| Koordinator | mengatur & meringkas |

Akses ke keempat web **hanya baca**, dan setiap angka di laporan dicocokkan dengan data asli.

## Coba di komputer sendiri

Butuh Python 3.12+, Node.js 20+, dan npm (macOS/Linux).

```bash
git clone https://github.com/adsqukis/kantorai && cd kantorai
./scripts/jalan-lokal.sh --demo
```

- Dashboard: http://localhost:8710 (password `qukis`)
- Kantor 3D: http://localhost:8712/office (klik **Connect** bila diminta)

`--demo` mengisi data **CONTOH** (angka fiktif). Tambah `--berjalan` untuk melihat agent sedang bekerja di meja.

Untuk data asli: salin `.env.example` ke `.lokal/env`, isi `DEEPSEEK_API_KEY` dan 4 token baca, lalu jalankan tanpa `--demo` dan buat laporan dengan:

```bash
set -a; . .lokal/env; set +a; DB_PATH=.lokal/laporan.db .venv/bin/laporan run
```

## Pasang di VPS

Lihat [`deploy/RUNBOOK.md`](deploy/RUNBOOK.md). Cek dulu VPS dengan `deploy/cek-vps.sh` (hanya membaca) supaya tidak bentrok dengan web yang sudah ada.

## Dokumen

- Desain: `docs/superpowers/specs/2026-11-26-tim-agent-laporan-harian-design.md`
- Rencana: `docs/superpowers/plans/`
