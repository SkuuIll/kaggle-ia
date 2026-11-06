# Kaggle IA — Panel de Administración e Inferencia en VPS

Plataforma privada alojada en VPS para administrar, monitorear y exponer servidores de inferencia LLM sobre GPUs gratuitas de Kaggle mediante túneles SSH inversos restringidos y endpoints HTTPS compatibles con OpenAI.

---

## Inicio rápido desde la web

1. Entrá al panel HTTPS y abrí **Cuentas** para verificar que haya una cuenta configurada.
2. En **Chat IA**, elegí la cuenta, prepará tu mensaje y pulsá **Iniciar servidor**. Si otra cuenta está activa, el panel pide confirmación antes de cambiarla.
3. Seguí la publicación y el arranque en **Actividad**. Cuando el chat indique **Servidor conectado**, enviá el mensaje.
4. Para cerrar la sesión de cómputo, usá **Apagar** y comprobá el estado terminal en Actividad. Cancelar una respuesta detiene solo esa solicitud.

[Guía del chat y del arranque web](docs/manual/CHAT_Y_ARRANQUE.md)

## Arquitectura general

```
[ Kaggle GPU (T4 x2) ]
   │  Ollama (127.0.0.1:11434) + Gateway de control
   │  Túnel SSH inverso restringido (loopback)
   ▼
[ VPS Linux (/opt/kaggle-ia) ]
   ├── Relay interno Cuenta 1 (127.0.0.1:18134) ──► Proxy medido (127.0.0.1:19134)
   ├── Relay interno Cuenta 2 (127.0.0.1:17860) ──► Proxy medido (127.0.0.1:19860)
   ├── Panel de control (127.0.0.1:8765)
   └── Caddy HTTPS (ia.example.com)
         ├── Panel Web (sesión __Host-ia_session + CSRF + scrypt)
         ├── /inference/cuenta1/v1 (Bearer API Key dedicada Cuenta 1)
         └── /inference/cuenta2/v1 (Bearer API Key dedicada Cuenta 2)
```

- **Sin costos de GPU:** aprovecha la cuota oficial gratuita de Kaggle sin contratar GPUs pagas.
- **Aislamiento de red:** los puertos de relay y proxies escuchan únicamente en `127.0.0.1`. La clave SSH de relay tiene shell deshabilitada (`nologin`) y permisos de forwarding restringidos.
- **Clientes por HTTPS:** **Continue** (en Antigravity IDE), **OpenCode**, **Paseo** y herramientas como **Aider** se conectan directamente por HTTPS a `https://ia.example.com/inference/cuentaN/v1` con claves Bearer independientes por cuenta.
- **Parada real verificada:** el apagado solicita la terminación de procesos al gateway del notebook y verifica en la API oficial de Kaggle que la sesión alcance un estado terminal (`COMPLETE`, `CANCEL_ACKNOWLEDGED` o `ERROR`). Nunca se publica un notebook vacío (`stop_kernel`) para simular un apagado.

---

## Características principales

- **Dashboard interactivo y flujo guiado:** monitoreo en tiempo real de sesiones activas, cuota oficial de GPU en Kaggle (horas usadas, reservadas, disponibles y fecha de renovación), solicitudes, gráfico de tokens medidos de los últimos 7 días, barra de flujo de trabajo en 4 pasos y paleta de comandos rápida (`Ctrl+K`).
- **Chat IA Multimodal integrado en la web:** estudio de conversación dentro del panel que permite chatear directamente con los modelos alojados, adjuntar **documentos** (`.pdf`, `.docx`, `.xlsx`, `.pptx`, `.txt`, `.md`, `.csv`, `.json`), **código fuente**, **fotos** (`.png`, `.jpg`, `.webp`, `.gif` con visor ampliado), **videos** (`.mp4`, `.webm`, `.mov` con reproductor en línea) y **audios** (`.mp3`, `.wav`, `.ogg`), además de descargar cualquier adjunto original, bloques de código generados, transcripciones `.md` o paquetes `.zip` completos de la conversación.
- **Gestión multicuentas:** ocho slots previstos, con credenciales independientes para cada cuenta configurada (`kaggle.json` legacy o token `KGAT_` con detección automática de usuario), manteniendo una única sesión GPU activa a la vez para proteger la cuota.
- **Selector y catálogo de modelos GGUF:** inspección directa de repositorios en Hugging Face con revisión SHA fija, más un catálogo en **Plantillas** con los modelos, herramientas y flujos disponibles en la instalación.
- **Diagnóstico y ahorro de cuota:** comprobación de estado en tres capas (Kaggle, API HTTPS y modelo residente en VRAM) sin generar tokens ni iniciar GPUs, perfiles de contexto (`16k`, `32k`, `128k`), autoapagado configurable en el notebook (por defecto 15 min de inactividad / 120 min máximo) y extensión explícita de sesión (`+30 min`).
- **Configuración de clientes lista para usar:** generación de bloques copiables (`opencode.json`, `config.json` de Paseo, `config.yaml` de Continue) y descarga de paquete instalador privado para Windows desde el navegador.
- **Portabilidad y publicación segura:** separación estricta entre la exportación pública de código (`sistema/publicar_codigo.py`, escaneada contra secretos locales) y los respaldos privados de conexión.

---

## Estructura del proyecto

```text
kaggle/
├── .github/workflows/tests.yml   # Integración continua (unittest en Python 3.12)
├── deployment/                   # Configuración de producción para VPS Linux
│   ├── Caddyfile                 # Proxy inverso HTTPS, cabeceras y rutas /inference/
│   ├── install-vps.sh            # Instalador reproducible con verificación SHA256
│   ├── kaggle-ia.service         # Servicio systemd del panel y proxies de inferencia
│   └── kaggle-ia-web.service     # Servicio systemd de Caddy HTTPS
├── docs/manual/                  # Documentación técnica y operativa
├── sistema/                      # Núcleo del servidor, controladores, interfaz y tests
│   ├── core/                     # Servidor HTTP, sesión, seguridad y exportación
│   ├── web/                      # Panel, login, estilos, tablero y fuentes
│   │   └── chat/workspace.js     # Conversaciones, adjuntos y generación
│   ├── chat/                     # SQLite, contexto, adjuntos y multimedia
│   ├── accounts/                 # Credenciales, notebooks y ciclo de vida
│   ├── pool/                     # Relay, proxies, perfiles y caché
│   ├── clients/                  # Configuración de Continue, OpenCode y Paseo
│   ├── templates/                # Catálogo y controladores
│   └── tests/                    # Pruebas locales sin consumir cuota GPU
├── .gitignore                    # Reglas de exclusión de credenciales y estado privado
└── README.md                     # Este documento
```

---

## Documentación detallada

| Guía | Contenido |
|---|---|
| [Uso del panel](docs/manual/USO.md) | Operación diaria, secciones del panel, cuentas, métricas y respaldos |
| [Arquitectura y seguridad](docs/manual/ARQUITECTURA.md) | Flujo de red, puertos internos, sesiones, autenticación y base de datos |
| [Despliegue en VPS](docs/manual/VPS.md) | Instalación en Linux con `systemd` y Caddy, mantenimiento y recuperación |
| [Configuración de clientes](docs/manual/INSTALACION.md) | Conexión de Continue, OpenCode y Paseo por HTTPS en Windows/PC |
| [Catálogo de plantillas](docs/manual/PLANTILLAS.md) | Modelos GGUF curados, paquetes de herramientas locales y prompts |
| [Diagnóstico y optimización](docs/manual/OPTIMIZACION_Y_REPOSITORIOS.md) | Perfiles `16k`/`32k`/`128k`, etapas de arranque, ahorro de horas y referencias |
| [Solución de problemas](docs/manual/PROBLEMAS.md) | Diagnóstico de errores `401`/`503`, colas de Kaggle, contexto y paradas |
| [Publicación en GitHub](docs/manual/GITHUB.md) | Qué archivos subir, exclusiones de `.gitignore` y verificación sin secretos |

---

## Desarrollo y pruebas

Requisitos: **Python 3.11+** (se recomienda **Python 3.12**).

```powershell
python -m venv sistema/.venv
sistema/.venv/Scripts/python.exe -m pip install -r sistema/requirements.lock.txt
sistema/.venv/Scripts/python.exe -m unittest discover -s sistema/tests -p "tests_*.py" -v
```

Para compilar y comprobar el frontend con Node.js 22.12 o superior:

```powershell
npm --prefix sistema/web/frontend ci
npm --prefix sistema/web/frontend run build
node --check sistema/web/dashboard.js
node --check sistema/web/chat/workspace.js
node --test sistema/tests/chat-workspace.test.cjs
```

En Linux / VPS:

```bash
/opt/kaggle-ia/sistema/.venv/bin/python -m unittest discover -s /opt/kaggle-ia/sistema/tests -p "tests_*.py" -v
```

> **Nota de seguridad:** Las pruebas utilizan dobles de prueba en directorios temporales, no requieren credenciales reales y nunca inician sesiones GPU en Kaggle. Antes de subir cambios a GitHub, ejecutá `python sistema/publicar_codigo.py` o verificá `git status` para asegurarte de no incluir nunca `sistema/.private/`, `kaggle(*.json)`, `sistema/model_profiles.json` ni notebooks `.ipynb`.

Mejoras de contexto, recuperación, almacenamiento, video y caché CPU: [guía de mejoras aplicadas](docs/manual/MEJORAS_APLICADAS_20261104.md).

Resultados por sección y alcance de la verificación: [revisión del panel](docs/manual/REVISION_PANEL_20261105.md).
