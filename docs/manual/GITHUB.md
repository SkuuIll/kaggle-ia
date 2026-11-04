# Publicación en GitHub y Control de Versiones

## Organización del repositorio

El proyecto separa estrictamente el código fuente público del estado privado de la instalación:

- **Archivos públicos (versionables en GitHub):**
  - `README.md` y `.gitignore`
  - `.github/workflows/tests.yml`: flujo de integración continua con `unittest` en Python 3.12.
  - `deployment/`: `Caddyfile`, `install-vps.sh`, `kaggle-ia.service` y `kaggle-ia-web.service`.
  - `docs/manual/`: documentación técnica y manuales de operación.
  - `sistema/`: módulos Python (`*.py`), instalador PowerShell (`instalar.ps1`), interfaz web (`login.html`, `panel.html`, `panel.css`, `dashboard.js`), tipografía (`fonts/Geist-Variable.ttf`, `fonts/OFL.txt`), dependencias (`requirements.txt`, `requirements.lock.txt`) y plantilla de configuración (`model_profiles.example.json`).

- **Archivos privados y locales (excluidos por `.gitignore` y prohibidos en GitHub):**
  - `sistema/.private/`: claves SSH (`kaggle_relay`, `known_hosts`), hashes de autenticación (`panel-auth.json`, `inference-auth.json`), claves Bearer (`api-clients.json`), base de datos `usage.sqlite`, herramientas locales y respaldos.
  - `sistema/kaggle(1).json` y `sistema/kaggle(2).json`: tokens y credenciales de Kaggle.
  - `sistema/model_profiles.json`: configuración activa con nombres de usuario reales de Kaggle.
  - `sistema/kernel/` y `sistema/kernel2/`: notebooks `.ipynb` generados (contienen incrustada la clave SSH restringida del relay).
  - `exportaciones/`: paquetes ZIP generados y carpetas de exportación.
  - `PROJECT_CONTEXT.md` y `AGENTS.md`: notas internas de contexto y reglas locales de agentes.

---

## Cómo preparar y verificar el código para GitHub

### Opción 1: Usar el exportador con escaneo de secretos (`recomendado`)

Ejecutá el verificador de publicación desde la raíz del proyecto:

```powershell
sistema/.venv/Scripts/python.exe sistema/publicar_codigo.py
```

O en la VPS:

```bash
/opt/kaggle-ia/sistema/.venv/bin/python /opt/kaggle-ia/sistema/publicar_codigo.py
```

Esta herramienta:
1. Empaqueta únicamente los archivos de la lista blanca definida en `sistema/portability.py`.
2. Genera un `sistema/model_profiles.example.json` limpio (reemplazando el usuario real por `CONFIGURAR_USUARIO`).
3. Escanea cada archivo del paquete contra todas las claves reales presentes en la máquina (`kaggle(*.json)`, `api-clients.json`, `kaggle_relay`, `ACCESO_PANEL.txt` y encabezados `BEGIN OPENSSH PRIVATE KEY`).
4. Extrae el árbol limpio y auditado en `exportaciones/github-listo/` y crea `exportaciones/kaggle-ia-publico.zip`.

Si vas a subir archivos arrastrándolos desde la interfaz web de GitHub, subí **únicamente el contenido de `exportaciones/github-listo/`** (el navegador ignora `.gitignore` si seleccionás carpetas privadas manualmente).

### Opción 2: Publicar con Git CLI

El archivo `.gitignore` de la raíz ya bloquea credenciales, `.private/`, notebooks `.ipynb`, bases SQLite, entornos `.venv` y archivos internos. Antes de hacer `git commit`, verificá siempre el estado con:

```bash
git status --ignored
```

> **Importante:** Si alguna credencial o clave SSH llegara a subirse por error a un repositorio público o privado, borrarla en un commit posterior no es suficiente: debés revocar/rotar inmediatamente el token en Kaggle o la clave SSH en la VPS y reescribir el historial del repositorio.
