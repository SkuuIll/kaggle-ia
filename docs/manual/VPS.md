# Despliegue y Mantenimiento en Servidor VPS

## Arquitectura del despliegue en Linux

El proyecto se instala en `/opt/kaggle-ia` sobre Linux `x86_64` con `systemd`, utilizando entornos y usuarios de sistema sin privilegios ni shell interactivo:

- **Usuario `kaggle-ia`:** ejecuta `/opt/kaggle-ia/sistema/panel_server.py` con Python 3.12 aislado (gestionado mediante `uv` en `/opt/kaggle-ia/python` y `/opt/kaggle-ia/sistema/.venv`). Escucha en `127.0.0.1:8765` (panel) y `127.0.0.1:19134` / `19860` (proxies medidos).
- **Usuario `kaggle-ia-web`:** ejecuta Caddy (`kaggle-ia-web.service`) con `CAP_NET_BIND_SERVICE` para gestionar certificados TLS automáticos y servir el dominio público HTTPS sin privilegios de `root`.
- **Endurecimiento (`systemd`):** ambos servicios aplican `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectSystem=strict`, `ProtectHome=true` y `UMask=0077`, limitando la escritura exclusivamente a `/opt/kaggle-ia/sistema`, `/opt/kaggle-ia/exportaciones` y `/var/lib/kaggle-ia-web`.

---

## Instalación reproducible desde cero

1. Copiá el árbol del proyecto en `/opt/kaggle-ia`.
2. Ubicá los archivos de estado privado en `/opt/kaggle-ia/sistema/.private/` (`kaggle_relay`, `known_hosts`, `connection.json`, `api-clients.json`, `inference-auth.json`) y las credenciales `kaggle(1).json` / `kaggle(2).json` en `/opt/kaggle-ia/sistema/`.
3. Generá el hash `scrypt` de la contraseña del panel (si aún no existe `panel-auth.json`):
   ```bash
   python3 /opt/kaggle-ia/sistema/panel_password.py
   ```
4. Verificá que el dominio configurado en `/opt/kaggle-ia/deployment/Caddyfile` y en la variable `IA_PUBLIC_ORIGIN` de `/opt/kaggle-ia/deployment/kaggle-ia.service` coincida con tu registro DNS `A` apuntando a la IP de la VPS (en Cloudflare usar modo **DNS only / nube gris** para permitir la validación directa de certificados o TLS estándar).
5. Ejecutá el instalador como `root`:
   ```bash
   sudo bash /opt/kaggle-ia/deployment/install-vps.sh
   ```
   El script descarga las versiones oficiales fijadas de `uv` y `Caddy`, comprueba sus sumas `SHA-256` antes de extraerlas, instala Python 3.12 y `requirements.lock.txt`, aplica permisos restrictivos (`0700` en `.private/`, `0600` en archivos sensibles), valida el `Caddyfile` y habilita ambos servicios `systemd`.

---

## Comandos habituales de administración

### Consultar estado y registros

```bash
sudo systemctl status kaggle-ia kaggle-ia-web
sudo journalctl -u kaggle-ia -n 50 --no-pager
sudo journalctl -u kaggle-ia-web -n 50 --no-pager
```

### Verificar puertos en escucha

```bash
sudo ss -ltnp | grep -E '8765|19134|19860|18134|17860|2020'
```

Todos los puertos de control, proxies y túneles deben aparecer enlazados a `127.0.0.1`.

### Actualizar el código en la VPS

Después de actualizar los archivos de `/opt/kaggle-ia/sistema` o `/opt/kaggle-ia/docs`:

```bash
sudo chown -R kaggle-ia:kaggle-ia /opt/kaggle-ia/sistema /opt/kaggle-ia/exportaciones
sudo chmod 700 /opt/kaggle-ia/sistema/.private
sudo find /opt/kaggle-ia/sistema/.private -type f -exec chmod 600 {} +
sudo find /opt/kaggle-ia/sistema/.private -type d -exec chmod 700 {} +
sudo systemctl restart kaggle-ia
```

> **Nota:** Reiniciar `kaggle-ia` en la VPS no detiene ninguna sesión GPU que ya esté corriendo en Kaggle, pero revoca las sesiones web activas en memoria (deberás volver a iniciar sesión en `/login`). No reinicies `kaggle-ia` mientras haya una operación de encendido o apagado en curso en el panel.
