#!/bin/bash
# Emite e instala el cert para chainguard.chain-cortex.com
# Idempotente: solo acts si el DNS ya resuelve a este host.
set -euo pipefail
HOST="chainguard.chain-cortex.com"
EXPECT_IP="212.227.90.79"
APACHE_LOG_DIR="/var/log/apache2"

# 1) DNS check
RESOLVED_IP=$(getent ahostsv4 "$HOST" 2>/dev/null | awk "NR==1{print \$1}" || true)
if [ -z "$RESOLVED_IP" ]; then
  echo "[SKIP] $HOST no resuelve todavia (DNS pendiente)"
  exit 2
fi
if [ "$RESOLVED_IP" != "$EXPECT_IP" ]; then
  echo "[SKIP] $HOST resuelve a $RESOLVED_IP, esperado $EXPECT_IP"
  exit 3
fi
echo "[OK] DNS: $HOST -> $RESOLVED_IP"

# 2) Certbot (plugin apache)
if certbot certonly --webroot -w /var/www/html \
    --cert-name "$HOST" -d "$HOST" \
    --agree-tos --non-interactive \
    --register-unsafely-without-email \
    --keep-until-expiring 2>&1 | tail -5; then
  echo "[OK] cert emitido"
else
  echo "[FAIL] certbot fallo"; exit 1
fi

# 3) SSL vhost
cat > /etc/apache2/sites-available/chainguard-sub-le-ssl.conf <<EOF
<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName $HOST

    ErrorLog \${APACHE_LOG_DIR}/chainguard_sub_error.log
    CustomLog \${APACHE_LOG_DIR}/chainguard_sub_access.log combined

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    Include /etc/letsencrypt/options-ssl-apache.conf
    SSLCertificateFile /etc/letsencrypt/live/$HOST/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/$HOST/privkey.pem
</VirtualHost>
</IfModule>
EOF

a2ensite chainguard-sub-le-ssl >/dev/null
apache2ctl configtest
systemctl reload apache2
echo "[OK] SSL vhost activo"
