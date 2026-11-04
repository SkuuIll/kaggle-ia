# Kaggle IA — Panel de Administración e Inferencia en VPS

Plataforma privada alojada en VPS para administrar, monitorear y exponer servidores de inferencia LLM sobre GPUs gratuitas de Kaggle mediante túneles SSH inversos restringidos y endpoints HTTPS compatibles con OpenAI.

---

## Antes de instalar

Este repositorio contiene código y plantillas, no acceso a una instalación existente. No incluye cuentas, tokens, claves SSH, conversaciones, archivos adjuntos ni respaldos. `ia.example.com` es un dominio de ejemplo: reemplazalo por uno propio. La interfaz permanece autenticada aunque el código sea público.

Requiere una VPS Linux x86_64 con SSH y un dominio, una cuenta Kaggle habilitada para aceleradores, Python 3.11+ y configuración privada propia. La GPU gratuita tiene cuotas y disponibilidad variables; la VPS puede tener costo. No se garantizan 30 horas, un contexto concreto, TPS ni tiempos de arranque. No uses cuentas múltiples para eludir cuotas o las condiciones de Kaggle; los dos conectores son opcionales y el panel limita la GPU simultánea.

1. Cloná `https://github.com/SkuuIll/kaggle-ia.git`.
2. Revisá [Primer despliegue](docs/manual/PRIMER_DESPLIEGUE.md): explica qué configuración falta y qué requiere intervención del administrador.
3. Configurá el relay, las credenciales y el dominio antes de ejecutar [el instalador VPS](docs/manual/VPS.md). El instalador no aprovisiona automáticamente el relay SSH.
4. Ingresá al panel, verificá la conexión y descargá la configuración HTTPS para tus clientes.

Los modelos son referencias externas: cada proveedor conserva su licencia, disponibilidad y restricciones. Una etiqueta «uncensored» no garantiza ausencia de rechazos ni precisión. La interpretación de imágenes requiere un modelo con visión; video usa muestras, no todos los fotogramas, y la transcripción de audio requiere componentes opcionales.

## Arquitectura general

```
[ Kaggle GPU (T4 x2) ]
   │  Ollama (127.0.0.1:11434) + Gateway de control
   │  Túnel SSH inverso restringido (loopback)
   â–¼
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
- **Gestión multicuentas:** soporte para dos conexiones configurables (`kaggle.json` legacy o token `KGAT_` con detección automática de usuario), manteniendo una única sesión GPU activa a la vez para proteger la cuota.
- **Selector y catálogo de modelos GGUF:** inspección directa de repositorios en Hugging Face con revisión SHA fija, más un catálogo curado de **Plantillas** con 6 modelos de código de baja restricción (*abliterated/uncensored*), 3 paquetes de herramientas aisladas (Aider, cliente HTTPX, chat Streamlit) y 5 flujos de instrucciones.
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
│   ├── fonts/                    # Tipografía Geist autoalojada y licencia OFL
│   ├── panel_server.py           # Servidor HTTP del panel, rutas de chat y proxies medidos
│   ├── chat_engine.py            # Motor de chat multimodal, extracción de documentos y ZIP
│   ├── coding_control.py         # Controlador de ciclo de vida en Kaggle y relay SSH
│   ├── build_single_notebook.py  # Generador de notebooks privados con validación AST
│   ├── inference_proxy.py        # Proxy loopback con conteo de tokens SSE/JSON
│   ├── templates.py              # Catálogo curado de modelos GGUF, herramientas y prompts
│   ├── portability.py            # Exportación pública por lista blanca y respaldos
│   ├── publicar_codigo.py        # Generador de árbol público verificado para GitHub
│   └── tests_*.py                # Suite de pruebas unitarias (sin consumir GPU)
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
sistema/.venv/Scripts/python.exe -m unittest discover -s sistema -p "tests_*.py" -v
```

En Linux / VPS:

```bash
/opt/kaggle-ia/sistema/.venv/bin/python -m unittest discover -s /opt/kaggle-ia/sistema -p "tests_*.py" -v
```

> **Nota de seguridad:** Las pruebas utilizan dobles de prueba en directorios temporales, no requieren credenciales reales y nunca inician sesiones GPU en Kaggle. Antes de subir cambios a GitHub, ejecutá `python sistema/publicar_codigo.py` o verificá `git status` para asegurarte de no incluir nunca `sistema/.private/`, `kaggle(*.json)`, `sistema/model_profiles.json` ni notebooks `.ipynb`.

Mejoras de contexto, recuperación, almacenamiento, video y caché CPU: [guía de mejoras aplicadas](docs/manual/MEJORAS_APLICADAS_20261104.md).
