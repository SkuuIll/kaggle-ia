# Kaggle IA â€” Panel de AdministraciÃ³n e Inferencia en VPS

Plataforma privada alojada en VPS para administrar, monitorear y exponer servidores de inferencia LLM sobre GPUs gratuitas de Kaggle mediante tÃºneles SSH inversos restringidos y endpoints HTTPS compatibles con OpenAI.

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
   â”‚  Ollama (127.0.0.1:11434) + Gateway de control
   â”‚  TÃºnel SSH inverso restringido (loopback)
   â–¼
[ VPS Linux (/opt/kaggle-ia) ]
   â”œâ”€â”€ Relay interno Cuenta 1 (127.0.0.1:18134) â”€â”€â–º Proxy medido (127.0.0.1:19134)
   â”œâ”€â”€ Relay interno Cuenta 2 (127.0.0.1:17860) â”€â”€â–º Proxy medido (127.0.0.1:19860)
   â”œâ”€â”€ Panel de control (127.0.0.1:8765)
   â””â”€â”€ Caddy HTTPS (ia.example.com)
         â”œâ”€â”€ Panel Web (sesiÃ³n __Host-ia_session + CSRF + scrypt)
         â”œâ”€â”€ /inference/cuenta1/v1 (Bearer API Key dedicada Cuenta 1)
         â””â”€â”€ /inference/cuenta2/v1 (Bearer API Key dedicada Cuenta 2)
```

- **Sin costos de GPU:** aprovecha la cuota oficial gratuita de Kaggle sin contratar GPUs pagas.
- **Aislamiento de red:** los puertos de relay y proxies escuchan Ãºnicamente en `127.0.0.1`. La clave SSH de relay tiene shell deshabilitada (`nologin`) y permisos de forwarding restringidos.
- **Clientes por HTTPS:** **Continue** (en Antigravity IDE), **OpenCode**, **Paseo** y herramientas como **Aider** se conectan directamente por HTTPS a `https://ia.example.com/inference/cuentaN/v1` con claves Bearer independientes por cuenta.
- **Parada real verificada:** el apagado solicita la terminaciÃ³n de procesos al gateway del notebook y verifica en la API oficial de Kaggle que la sesiÃ³n alcance un estado terminal (`COMPLETE`, `CANCEL_ACKNOWLEDGED` o `ERROR`). Nunca se publica un notebook vacÃ­o (`stop_kernel`) para simular un apagado.

---

## CaracterÃ­sticas principales

- **Dashboard interactivo y flujo guiado:** monitoreo en tiempo real de sesiones activas, cuota oficial de GPU en Kaggle (horas usadas, reservadas, disponibles y fecha de renovaciÃ³n), solicitudes, grÃ¡fico de tokens medidos de los Ãºltimos 7 dÃ­as, barra de flujo de trabajo en 4 pasos y paleta de comandos rÃ¡pida (`Ctrl+K`).
- **Chat IA Multimodal integrado en la web:** estudio de conversaciÃ³n dentro del panel que permite chatear directamente con los modelos alojados, adjuntar **documentos** (`.pdf`, `.docx`, `.xlsx`, `.pptx`, `.txt`, `.md`, `.csv`, `.json`), **cÃ³digo fuente**, **fotos** (`.png`, `.jpg`, `.webp`, `.gif` con visor ampliado), **videos** (`.mp4`, `.webm`, `.mov` con reproductor en lÃ­nea) y **audios** (`.mp3`, `.wav`, `.ogg`), ademÃ¡s de descargar cualquier adjunto original, bloques de cÃ³digo generados, transcripciones `.md` o paquetes `.zip` completos de la conversaciÃ³n.
- **GestiÃ³n multicuentas:** soporte para dos conexiones configurables (`kaggle.json` legacy o token `KGAT_` con detecciÃ³n automÃ¡tica de usuario), manteniendo una Ãºnica sesiÃ³n GPU activa a la vez para proteger la cuota.
- **Selector y catÃ¡logo de modelos GGUF:** inspecciÃ³n directa de repositorios en Hugging Face con revisiÃ³n SHA fija, mÃ¡s un catÃ¡logo curado de **Plantillas** con 6 modelos de cÃ³digo de baja restricciÃ³n (*abliterated/uncensored*), 3 paquetes de herramientas aisladas (Aider, cliente HTTPX, chat Streamlit) y 5 flujos de instrucciones.
- **DiagnÃ³stico y ahorro de cuota:** comprobaciÃ³n de estado en tres capas (Kaggle, API HTTPS y modelo residente en VRAM) sin generar tokens ni iniciar GPUs, perfiles de contexto (`16k`, `32k`, `128k`), autoapagado configurable en el notebook (por defecto 15 min de inactividad / 120 min mÃ¡ximo) y extensiÃ³n explÃ­cita de sesiÃ³n (`+30 min`).
- **ConfiguraciÃ³n de clientes lista para usar:** generaciÃ³n de bloques copiables (`opencode.json`, `config.json` de Paseo, `config.yaml` de Continue) y descarga de paquete instalador privado para Windows desde el navegador.
- **Portabilidad y publicaciÃ³n segura:** separaciÃ³n estricta entre la exportaciÃ³n pÃºblica de cÃ³digo (`sistema/publicar_codigo.py`, escaneada contra secretos locales) y los respaldos privados de conexiÃ³n.

---

## Estructura del proyecto

```text
kaggle/
â”œâ”€â”€ .github/workflows/tests.yml   # IntegraciÃ³n continua (unittest en Python 3.12)
â”œâ”€â”€ deployment/                   # ConfiguraciÃ³n de producciÃ³n para VPS Linux
â”‚   â”œâ”€â”€ Caddyfile                 # Proxy inverso HTTPS, cabeceras y rutas /inference/
â”‚   â”œâ”€â”€ install-vps.sh            # Instalador reproducible con verificaciÃ³n SHA256
â”‚   â”œâ”€â”€ kaggle-ia.service         # Servicio systemd del panel y proxies de inferencia
â”‚   â””â”€â”€ kaggle-ia-web.service     # Servicio systemd de Caddy HTTPS
â”œâ”€â”€ docs/manual/                  # DocumentaciÃ³n tÃ©cnica y operativa
â”œâ”€â”€ sistema/                      # NÃºcleo del servidor, controladores, interfaz y tests
â”‚   â”œâ”€â”€ fonts/                    # TipografÃ­a Geist autoalojada y licencia OFL
â”‚   â”œâ”€â”€ panel_server.py           # Servidor HTTP del panel, rutas de chat y proxies medidos
â”‚   â”œâ”€â”€ chat_engine.py            # Motor de chat multimodal, extracciÃ³n de documentos y ZIP
â”‚   â”œâ”€â”€ coding_control.py         # Controlador de ciclo de vida en Kaggle y relay SSH
â”‚   â”œâ”€â”€ build_single_notebook.py  # Generador de notebooks privados con validaciÃ³n AST
â”‚   â”œâ”€â”€ inference_proxy.py        # Proxy loopback con conteo de tokens SSE/JSON
â”‚   â”œâ”€â”€ templates.py              # CatÃ¡logo curado de modelos GGUF, herramientas y prompts
â”‚   â”œâ”€â”€ portability.py            # ExportaciÃ³n pÃºblica por lista blanca y respaldos
â”‚   â”œâ”€â”€ publicar_codigo.py        # Generador de Ã¡rbol pÃºblico verificado para GitHub
â”‚   â””â”€â”€ tests_*.py                # Suite de pruebas unitarias (sin consumir GPU)
â”œâ”€â”€ .gitignore                    # Reglas de exclusiÃ³n de credenciales y estado privado
â””â”€â”€ README.md                     # Este documento
```

---

## DocumentaciÃ³n detallada

| GuÃ­a | Contenido |
|---|---|
| [Uso del panel](docs/manual/USO.md) | OperaciÃ³n diaria, secciones del panel, cuentas, mÃ©tricas y respaldos |
| [Arquitectura y seguridad](docs/manual/ARQUITECTURA.md) | Flujo de red, puertos internos, sesiones, autenticaciÃ³n y base de datos |
| [Despliegue en VPS](docs/manual/VPS.md) | InstalaciÃ³n en Linux con `systemd` y Caddy, mantenimiento y recuperaciÃ³n |
| [ConfiguraciÃ³n de clientes](docs/manual/INSTALACION.md) | ConexiÃ³n de Continue, OpenCode y Paseo por HTTPS en Windows/PC |
| [CatÃ¡logo de plantillas](docs/manual/PLANTILLAS.md) | Modelos GGUF curados, paquetes de herramientas locales y prompts |
| [DiagnÃ³stico y optimizaciÃ³n](docs/manual/OPTIMIZACION_Y_REPOSITORIOS.md) | Perfiles `16k`/`32k`/`128k`, etapas de arranque, ahorro de horas y referencias |
| [SoluciÃ³n de problemas](docs/manual/PROBLEMAS.md) | DiagnÃ³stico de errores `401`/`503`, colas de Kaggle, contexto y paradas |
| [PublicaciÃ³n en GitHub](docs/manual/GITHUB.md) | QuÃ© archivos subir, exclusiones de `.gitignore` y verificaciÃ³n sin secretos |

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

> **Nota de seguridad:** Las pruebas utilizan dobles de prueba en directorios temporales, no requieren credenciales reales y nunca inician sesiones GPU en Kaggle. Antes de subir cambios a GitHub, ejecutÃ¡ `python sistema/publicar_codigo.py` o verificÃ¡ `git status` para asegurarte de no incluir nunca `sistema/.private/`, `kaggle(*.json)`, `sistema/model_profiles.json` ni notebooks `.ipynb`.

Mejoras de contexto, recuperaciÃ³n, almacenamiento, video y cachÃ© CPU: [guÃ­a de mejoras aplicadas](docs/manual/MEJORAS_APLICADAS_20261104.md).
