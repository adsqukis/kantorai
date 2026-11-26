#!/usr/bin/env bash
# Cek VPS sebelum instal kantorai. HANYA MEMBACA, tidak mengubah apa pun.
# Jalankan:  sudo bash cek-vps.sh  > hasil-cek.txt 2>&1
echo "=== OS & sumber daya ==="
. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME"
nproc; free -h | head -2; df -h / | tail -1
echo; echo "=== Port yang sedang dipakai (listen) ==="
ss -tulpn 2>/dev/null | awk 'NR==1 || /LISTEN|UNCONN/'
echo; echo "=== Web server terpasang ==="
for b in nginx apache2 httpd caddy traefik node pm2 docker python3 python3.12; do
  command -v "$b" >/dev/null 2>&1 && echo "$b: $($b --version 2>&1 | head -1)"
done
echo; echo "=== Layanan aktif yang relevan ==="
systemctl list-units --type=service --state=running --no-pager 2>/dev/null | grep -Ei 'nginx|apache|httpd|caddy|traefik|docker|node|pm2|gunicorn|uvicorn|php|mysql|maria|postgres|redis|laporan' || true
echo; echo "=== Situs nginx ==="
ls -l /etc/nginx/sites-enabled/ 2>/dev/null
grep -rhoE 'server_name[^;]+;|listen[^;]+;|proxy_pass[^;]+;' /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null | sort -u
echo; echo "=== Situs apache ==="
ls /etc/apache2/sites-enabled/ 2>/dev/null
echo; echo "=== Caddyfile ==="
grep -vE '^\s*#' /etc/caddy/Caddyfile 2>/dev/null | grep -v '^\s*$' | head -40
echo; echo "=== Docker ==="
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Ports}}' 2>/dev/null
echo; echo "=== PM2 ==="
pm2 ls 2>/dev/null | head -30
echo; echo "=== Folder /opt dan /var/www ==="
ls /opt /var/www 2>/dev/null
echo; echo "=== Firewall ==="
ufw status 2>/dev/null | head -20
