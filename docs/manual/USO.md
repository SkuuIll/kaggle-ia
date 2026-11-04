# Guía de Uso del Panel Web

El panel de control (`https://ia.example.com`) centraliza la administración de tus cuentas de Kaggle, modelos GGUF, métricas de uso y configuraciones de clientes en seis secciones principales, con botones de acción rápida (**Apagar todas** y **Agregar cuenta**) siempre visibles en el encabezado.

---

## Secciones del panel

| Sección | Funciones principales |
|---|---|
| **Dashboard** | Barra interactiva de flujo de trabajo en 4 pasos, estado en vivo de las sesiones, cuota oficial de GPU en Kaggle, KPIs de tokens y solicitudes, gráfico de actividad de los últimos 7 días (UTC), tarjetas de modelo con accesos directos (**Chatear**, **Diagnosticar**, **Clientes IDE**) y últimos eventos. |
| **Chat IA** | Estudio multimodal integrado para conversar con los modelos de tus cuentas, enviar documentos (`.pdf`, `.docx`, `.xlsx`, `.pptx`, texto y código), fotos (`.png`, `.jpg`, `.webp`, `.gif`), videos (`.mp4`, `.webm`, `.mov`) y audios (`.mp3`, `.wav`, `.ogg`), previsualizarlos en el navegador y descargar respuestas (`.md`), bloques de código individuales, archivos adjuntos originales o el paquete `.zip` completo de la conversación. |
| **Cuentas** | Búsqueda y listado de cuentas conectadas, alta por token `KGAT_` o archivo `kaggle.json`, cambio de nombre identificatorio, actualización de credenciales y retiro seguro de cuentas. |
| **Modelos** | Selección manual de cualquier repositorio GGUF compatible en Hugging Face, inspección de archivos disponibles, fijación de revisión SHA y ajuste de ventana de contexto. |
| **Plantillas** | Catálogo curado con 6 modelos GGUF de baja restricción listos para instalar, 3 paquetes descargables de herramientas para PC (Aider, HTTPX, Streamlit) y 5 plantillas de prompts. |
| **Actividad** | Consola de progreso en vivo de la operación actual, etapas de arranque informadas por el notebook y registro histórico persistente filtrable por resultado (`Completadas` / `Con errores`). |
| **Configuración** | Cinco subsecciones: **General** (avisos del navegador y modo del servidor), **Autoapagado** (límites de inactividad y sesión), **Conexión** (diagnóstico, perfiles `16k`/`32k`/`128k`, extensión `+30 min` y configuraciones HTTPS para clientes), **Respaldos** (exportación pública y respaldo privado) y **Seguridad** (cambio de contraseña y cierre de sesión). |

---

## Flujo de operación diaria

1. **Ingresar al panel:** abrí `https://ia.example.com` e iniciá sesión con tu usuario y contraseña del panel. La sesión dura hasta 8 horas.
2. **Encender un modelo:** en **Dashboard** o **Cuentas**, pulsá **Encender** sobre la cuenta que quieras utilizar.
   - Si la otra cuenta estaba encendida, el panel te pedirá confirmación para detenerla primero (solo se permite una sesión GPU activa a la vez para cuidar tus horas).
   - Seguí el avance en **Actividad** hasta que aparezca **LISTO**. Recordá que `RUNNING` en Kaggle solo indica que la máquina virtual arrancó; el modelo está disponible para responder recién cuando alcanza **LISTO**.
3. **Trabajar desde tus clientes:** abrí una conversación nueva en **Continue** (Antigravity IDE), **Paseo**, **OpenCode** o **Aider**. Todas las peticiones viajan por HTTPS al endpoint `/inference/cuentaN/v1` correspondiente.
4. **Extender sesión si necesitás más tiempo:** si te acercás al límite de sesión o de inactividad, podés pulsar **Seguir trabajando · +30 min** en **Configuración → Conexión**.
5. **Apagar al terminar:** pulsá **Apagar** en la tarjeta del modelo o **Apagar todas** en la esquina superior derecha y esperá a que el panel confirme la finalización en Kaggle.

---

## Gestión de cuentas de Kaggle

- **Agregar o actualizar cuenta:** pulsá **Agregar cuenta** y elegí entre pegar un token `KGAT_...` (detecta el usuario automáticamente) o subir el archivo `kaggle.json`. Guardar una credencial valida el acceso contra Kaggle sin iniciar ninguna GPU.
- **Aislamiento de métricas:** las estadísticas de tokens y solicitudes se asocian al nombre de usuario de Kaggle (`identity`). Si más adelante reemplazás la cuenta de una ranura por otro usuario de Kaggle, sus contadores no se mezclan.
- **Quitar una cuenta de forma segura:** al pulsar el botón de quitar cuenta en la tabla de **Cuentas**, el sistema primero solicita y verifica que su sesión en Kaggle esté completamente detenida. Una vez confirmado el estado terminal, archiva la credencial en `sistema/.private/removed-accounts/` (con permisos `0600` para recuperación administrativa) y deshabilita la ranura. Si no puede confirmar el apagado, conserva la cuenta para que no quede una GPU encendida sin control.

---

## Respaldos y portabilidad

En **Configuración → Respaldos** disponés de tres acciones:
- **Exportar código:** genera un archivo ZIP público que contiene únicamente código fuente, activos y documentación, sin claves ni notebooks generados.
- **Respaldar conexión:** genera un archivo ZIP privado con las credenciales de Kaggle, claves de inferencia, clave SSH de relay y catálogo de perfiles. **No está cifrado:** guardalo en un lugar seguro y nunca lo subas a GitHub.
- **Importar ZIP:** restaura un respaldo privado previa comprobación de que no haya sesiones GPU activas en las cuentas actuales.
