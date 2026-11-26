# Runbook — Laporan Pagi di VPS Sumopod

Spek: 2 vCPU, 2 GB RAM, 40 GB SSD, Ubuntu 24.04.

## 0. Cek VPS dulu (hanya membaca)

```bash
sudo bash deploy/cek-vps.sh > hasil-cek.txt 2>&1
```

Port yang dipakai sistem ini (semua hanya di 127.0.0.1, tidak terbuka ke internet):

| Layanan | Port |
|---|---|
| Dashboard laporan | 8710 |
| Runtime untuk kantor 3D | 8711 |
| Kantor 3D | 8712 |

Jika salah satu port sudah dipakai, ganti angkanya di `deploy/*.service` dan di konfigurasi web server.

**Web server:** jika port 80/443 sudah dipegang nginx, **jangan pasang Caddy**. Pakai `deploy/nginx-kantorai.conf` (situs baru yang berdiri sendiri, web lama tidak disentuh). Jika belum ada web server sama sekali, pakai `deploy/Caddyfile`.

## 1. Siapkan server (sekali)

```bash
sudo apt update && sudo apt install -y python3.12-venv sqlite3 git curl
# Hanya bila VPS belum punya web server (lihat langkah 0): pasang Caddy
# sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
# curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
# curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
# sudo apt update && sudo apt install -y caddy
sudo useradd --system --home /opt/laporan --shell /usr/sbin/nologin laporan
sudo mkdir -p /opt/laporan /var/lib/laporan /var/backups/laporan /etc/laporan
sudo git clone https://github.com/adsqukis/kantorai /opt/laporan
sudo python3.12 -m venv /opt/laporan/.venv
sudo /opt/laporan/.venv/bin/pip install /opt/laporan
sudo chown -R laporan:laporan /opt/laporan /var/lib/laporan /var/backups/laporan
```

## 2. Isi rahasia

```bash
sudo cp /opt/laporan/.env.example /etc/laporan/laporan.env
sudo nano /etc/laporan/laporan.env      # isi DEEPSEEK_API_KEY, 4 token, DASHBOARD_PASSWORD
python3 -c "import secrets;print(secrets.token_hex(32))"   # nilai SESSION_SECRET
sudo chown root:laporan /etc/laporan/laporan.env && sudo chmod 640 /etc/laporan/laporan.env
```

## 3. Cek sambungan ke 4 web

```bash
cd /opt/laporan && sudo -u laporan bash -c 'set -a; . /etc/laporan/laporan.env; .venv/bin/laporan probe'
```

Lengkapi `config/sources.yaml` (id operasi TaQis, args tanggal) dan `config/brands.yaml` (alias brand per web) dari hasil probe. Pastikan setiap tool di `sources.yaml` ada di `READ_ONLY_TOOLS` (`laporan/mcp_client.py`), lalu:

```bash
sudo -u laporan bash -c 'set -a; . /etc/laporan/laporan.env; .venv/bin/laporan probe --try konten'   # ulangi: tiktok, taqis, keuangan
```

## 4. Uji run manual

```bash
sudo -u laporan bash -c 'set -a; . /etc/laporan/laporan.env; .venv/bin/laporan run'
```

## 5. Kantor 3D

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install -y nodejs
# RAM 2 GB: tambah swap sementara supaya build tidak kehabisan memori
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
cd /opt/laporan/kantor3d && sudo -u laporan npm ci --no-audit --no-fund && sudo -u laporan npm run build
python3 -c "import secrets;print('STUDIO_ACCESS_TOKEN='+secrets.token_urlsafe(24))" | sudo tee /etc/laporan/kantor3d.env
sudo chown root:laporan /etc/laporan/kantor3d.env && sudo chmod 640 /etc/laporan/kantor3d.env
sudo mkdir -p /var/lib/laporan/kantor3d-state && sudo chown laporan:laporan /var/lib/laporan/kantor3d-state
```

Simpan nilai `STUDIO_ACCESS_TOKEN`; itu "password" untuk membuka kantor 3D.

## 6. Aktifkan layanan

```bash
sudo cp /opt/laporan/deploy/*.service /opt/laporan/deploy/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now laporan-web.service laporan-runtime.service kantor3d.service laporan-run.timer laporan-backup.timer
```

Web server — pilih **salah satu**:

```bash
# A. VPS belum punya web server: Caddy
printf 'LAPORAN_DOMAIN=laporan.qukis.web.id\nKANTOR_DOMAIN=kantor.qukis.web.id\n' | sudo tee /etc/default/caddy
sudo cp /opt/laporan/deploy/Caddyfile /etc/caddy/Caddyfile && sudo systemctl restart caddy
```

```bash
# B. VPS sudah memakai nginx
sudo cp /opt/laporan/deploy/nginx-kantorai.conf /etc/nginx/sites-available/kantorai
sudo ln -s ../sites-available/kantorai /etc/nginx/sites-enabled/kantorai
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d laporan.qukis.web.id -d kantor.qukis.web.id
```

```bash
systemctl list-timers 'laporan-*'
```

Arahkan DNS subdomain (A record) ke IP VPS sebelum menyalakan Caddy, supaya sertifikat HTTPS bisa terbit.

## Sehari-hari

- Jalankan ulang tanggal tertentu: `sudo systemctl start laporan-run` (hari ini) atau
  `sudo -u laporan bash -c 'set -a; . /etc/laporan/laporan.env; /opt/laporan/.venv/bin/laporan run --date 2026-11-26'`
- Log run: `journalctl -u laporan-run -n 200`
- Log dashboard: `journalctl -u laporan-web -n 200`
- Log kantor 3D: `journalctl -u kantor3d -n 200` dan runtime: `journalctl -u laporan-runtime -n 200`
- Backup ada di `/var/backups/laporan` (30 hari terakhir).

## Catatan biaya

- Biaya DeepSeek hari pertama: _(isi setelah run perdana)_
