#!/usr/bin/env bash
set -euo pipefail
APP=/opt/kaggle-ia
if [[ $(id -u) != 0 ]]; then echo 'Ejecutar como root.' >&2; exit 1; fi
if [[ ! -f "$APP/sistema/.private/panel-auth.json" ]]; then echo 'Falta hash de acceso privado.' >&2; exit 1; fi
id kaggle-ia >/dev/null 2>&1 || useradd --system --home-dir "$APP" --shell /usr/sbin/nologin kaggle-ia
id kaggle-ia-web >/dev/null 2>&1 || useradd --system --home-dir /var/lib/kaggle-ia-web --shell /usr/sbin/nologin kaggle-ia-web
mkdir -p "$APP/tools" /etc/kaggle-ia /var/lib/kaggle-ia-web
# Pinned official releases; verify before extracting or executing.
download_verified() {
    local url="$1" target="$2" digest="$3"
    if [[ ! -f "$target" ]]; then curl --fail --location --proto '=https' --tlsv1.2 "$url" -o "$target"; fi
    printf '%s  %s\n' "$digest" "$target" | sha256sum --check --status
}
download_verified 'https://github.com/astral-sh/uv/releases/download/0.13.7/uv-x86_64-unknown-linux-gnu.tar.gz' /tmp/kaggle-ia-uv.tar.gz c5221ff41b7892bfc223543883600125f6a47fe845093e0f5bdff4f359196d83
download_verified 'https://github.com/caddyserver/caddy/releases/download/v2.11.7/caddy_2.11.7_linux_amd64.tar.gz' /tmp/kaggle-ia-caddy.tar.gz 727b91701a392de6ebc5027509f548bf39979e5216340d0faed8fa5e69c84f8b
tar -xzf /tmp/kaggle-ia-uv.tar.gz -C "$APP/tools" --strip-components=1
UV_PYTHON_INSTALL_DIR="$APP/python" "$APP/tools/uv" python install 3.12
UV_PYTHON_INSTALL_DIR="$APP/python" "$APP/tools/uv" venv --python 3.12 "$APP/sistema/.venv"
"$APP/tools/uv" pip install --python "$APP/sistema/.venv/bin/python" -r "$APP/sistema/requirements.lock.txt"
tar -xzf /tmp/kaggle-ia-caddy.tar.gz -C "$APP/tools" caddy
install -m 644 "$APP/deployment/kaggle-ia.service" /etc/systemd/system/kaggle-ia.service
install -m 644 "$APP/deployment/kaggle-ia-web.service" /etc/systemd/system/kaggle-ia-web.service
install -m 644 "$APP/deployment/Caddyfile" /etc/kaggle-ia/Caddyfile
chown -R kaggle-ia:kaggle-ia "$APP/sistema" "$APP/python"
mkdir -p "$APP/sistema/.private/user-home"
chown kaggle-ia:kaggle-ia "$APP/sistema/.private/user-home"
chmod 700 "$APP/sistema/.private"
find "$APP/sistema/.private" -type f -exec chmod 600 {} +
find "$APP/sistema/.private" -type d -exec chmod 700 {} +
mkdir -p "$APP/exportaciones"
chown kaggle-ia:kaggle-ia "$APP/exportaciones"
chmod 600 "$APP/sistema/"kaggle\(*\).json
chown kaggle-ia-web:kaggle-ia-web /var/lib/kaggle-ia-web
"$APP/tools/caddy" validate --config /etc/kaggle-ia/Caddyfile --adapter caddyfile
systemctl daemon-reload
systemctl enable --now kaggle-ia.service kaggle-ia-web.service
systemctl is-active kaggle-ia.service kaggle-ia-web.service
