# Runbook — Laporan Pagi di VPS Sumopod

Spek: 2 vCPU, 2 GB RAM, 40 GB SSD, Ubuntu 24.04.

## 1. Siapkan server (sekali)

```bash
sudo apt update && sudo apt install -y python3.12-venv sqlite3 git debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
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

## 5. Aktifkan layanan

```bash
sudo cp /opt/laporan/deploy/*.service /opt/laporan/deploy/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now laporan-web.service laporan-run.timer laporan-backup.timer
echo 'LAPORAN_DOMAIN=laporan.qukis.web.id' | sudo tee /etc/default/caddy
sudo cp /opt/laporan/deploy/Caddyfile /etc/caddy/Caddyfile && sudo systemctl restart caddy
systemctl list-timers 'laporan-*'
```

Arahkan DNS subdomain (A record) ke IP VPS sebelum menyalakan Caddy, supaya sertifikat HTTPS bisa terbit.

## Sehari-hari

- Jalankan ulang tanggal tertentu: `sudo systemctl start laporan-run` (hari ini) atau
  `sudo -u laporan bash -c 'set -a; . /etc/laporan/laporan.env; /opt/laporan/.venv/bin/laporan run --date 2026-11-26'`
- Log run: `journalctl -u laporan-run -n 200`
- Log dashboard: `journalctl -u laporan-web -n 200`
- Backup ada di `/var/backups/laporan` (30 hari terakhir).

## Catatan biaya

- Biaya DeepSeek hari pertama: _(isi setelah run perdana)_
