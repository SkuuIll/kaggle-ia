# Configuración de Clientes (Continue, OpenCode y Paseo)

Los clientes de código se conectan directamente por **HTTPS** al dominio del panel (`https://ia.example.com/inference/cuentaN/v1`) utilizando una clave API Bearer dedicada por cuenta. No se requiere abrir túneles SSH locales en la PC de trabajo para usar la inferencia.

---

## 1. Preparar la configuración desde el panel web

1. Ingresá a `https://ia.example.com` y abrí **Configuración → Conexión**.
2. En **Tu configuración, lista para usar**, seleccioná la cuenta deseada y pulsá **Preparar configuración privada**.
3. Desde esa vista podés:
   - **Mostrar o copiar la clave API** de esa conexión (independiente de la contraseña del panel y del token de Kaggle).
   - **Probar API:** verifica desde el navegador que el endpoint HTTPS responda `200 OK` y enumere el modelo registrado sin generar tokens.
   - **Copiar configuración:** obtené el archivo listo para pegar en **OpenCode** (`~/.config/opencode/opencode.json`), **Paseo** (`~/.paseo/config.json`) o **Continue** (`~/.continue/config.yaml`). El botón de copiado inserta la clave real aunque esté oculta en pantalla.

---

## 2. Instalación automática en Windows (paquete privado)

Si preferís no editar archivos JSON/YAML manualmente o estás preparando otra PC con Windows x64:

1. En **Configuración → Conexión**, tras pulsar **Preparar configuración privada**, hacé clic en **Descargar paquete privado**.
2. Extraé el archivo ZIP en una carpeta privada de tu PC.
3. Ejecutá `INSTALAR.bat` (si todavía no tenés Python 3.12, OpenCode o Paseo instalados; el script de PowerShell verifica los hashes SHA-256 oficiales antes de instalar).
4. Ejecutá `CONFIGURAR_CLIENTES.bat` para combinar los proveedores HTTPS con tus configuraciones actuales de OpenCode, Paseo y Continue. Tus conversaciones previas y otros proveedores se conservan, y se guarda una copia de respaldo con fecha en `sistema/.private/client-config-backup/`.
5. Ejecutá `ABRIR_PASEO.bat` para iniciar o recargar el daemon de Paseo con `opencode` en el `PATH` y abrir la interfaz.

> **Seguridad:** El paquete de configuración de clientes incluye las claves Bearer de inferencia (`api-clients.json`), pero **nunca** incluye tus credenciales de Kaggle ni la clave privada SSH del relay. Aun así, conservá ese ZIP de forma privada.

---

## 3. Notas específicas sobre Paseo y Continue

- **Continue (en Antigravity IDE / VS Code):** utiliza el proveedor `openai` apuntando a `https://ia.example.com/inference/cuenta1/v1` o `cuenta2/v1` con capacidad `tool_use` habilitada y `reasoning_effort: none` para respuestas directas de código.
- **OpenCode y Paseo:** Paseo utiliza OpenCode como motor subyacente y se comunica localmente con su propio daemon en `127.0.0.1:6767`. Si Paseo indica que no puede conectar con su daemon local, ejecutá `paseo daemon start` o usá `ABRIR_PASEO.bat`.
- **Disponibilidad bajo demanda:** guardar o aplicar la configuración en los clientes no enciende ninguna GPU en Kaggle. Cuando quieras codificar, encendé la cuenta desde el **Dashboard** del panel web y esperá el estado **LISTO**. Mientras la GPU esté apagada, los endpoints `/inference/cuentaN/v1` responderán `503 Service Unavailable`.
