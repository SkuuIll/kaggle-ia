# Solución de Problemas Frecuentes

## 1. Diferenciar el estado del panel web y el estado del modelo

El panel web (`https://ia.example.com`) corre de forma permanente en la VPS, incluso cuando todas las GPUs de Kaggle están apagadas.
- **`HTTP 503` en `/inference/cuentaN/v1`:** significa que el modelo de esa cuenta está apagado o todavía está en proceso de arranque/descarga. Revisá la sección **Actividad** o usá **Diagnosticar conexión** en **Configuración → Conexión**.
- **`HTTP 401` en `/inference/cuentaN/v1`:** falta la clave API Bearer de esa conexión o estás usando la clave de la Cuenta 1 en la URL de la Cuenta 2 (o viceversa). Copiá nuevamente la configuración desde **Configuración → Conexión**.
- **`ECONNREFUSED 127.0.0.1:17860` o `18134`:** tu cliente conserva una configuración antigua que apuntaba a `localhost`. Actualizá la configuración de Continue, OpenCode o Paseo para usar las URLs HTTPS (`https://ia.example.com/inference/cuentaN/v1`) y abrí un chat nuevo.

---

## 2. La cuenta figura `RUNNING` pero todavía no responde

Cuando Kaggle asigna la máquina, el estado pasa a `RUNNING`, pero el notebook aún debe:
1. Instalar Ollama si no está presente.
2. Descargar el archivo GGUF desde Hugging Face a `/kaggle/temp`.
3. Registrar el modelo, levantar el túnel SSH inverso y cargar los pesos en las GPUs T4.

Seguí el progreso real en la sección **Actividad** del panel y esperá hasta ver **LISTO**. Evitá reiniciar repetidamente la cuenta durante la carga, ya que cada ejecución consume cuota y reinicia la descarga.

---

## 3. No se pudo confirmar el apagado desde el panel

El botón **Apagar** envía la orden a `/control/stop` a través del túnel SSH inverso y luego consulta a Kaggle hasta confirmar un estado final (`COMPLETE`, `CANCEL_ACKNOWLEDGED` o `ERROR`).
- Si el notebook sigue en cola (`QUEUED`), está en las primeras celdas de instalación (antes de abrir el túnel SSH) o perdió conectividad de red, el canal `/control/stop` aún no estará disponible.
- En ese caso, abrí **Kaggle → Active Events** en tu navegador, pulsá **Stop Session** sobre el notebook activo y luego pulsá el botón de actualizar en el panel hasta que figure **Apagada**.
- **Nunca** publiques un notebook vacío para intentar detener una sesión.

---

## 4. Paseo no muestra el modelo o no conecta

1. Verificá en el **Dashboard** que la cuenta elegida esté encendida y en estado **LISTO**.
2. En **Configuración → Conexión**, pulsá **Diagnosticar conexión** o **Probar API** para confirmar que la API HTTPS responde `200 OK` con el modelo cargado.
3. Si Paseo informa que su daemon local (`127.0.0.1:6767`) está detenido, ejecutá `paseo daemon start` en tu terminal de Windows o usá `ABRIR_PASEO.bat` del paquete de clientes.
4. Iniciá siempre una **conversación nueva** después de cambiar de cuenta o recargar proveedores, ya que los chats anteriores de Paseo conservan el proveedor con el que fueron creados.

---

## 5. Error `Message exceeds context limit`

El límite de contexto (`num_ctx`) incluye el prompt del sistema, las definiciones de herramientas (`tool_use`), los archivos adjuntos, el historial de la conversación y los tokens reservados para la respuesta (`output_tokens`).
- Iniciá un chat nuevo o utilizá la compactación automática del cliente.
- Si estás usando el perfil de `16k` o `32k`, podés cambiar al perfil **Contexto largo (`128k`)** en **Configuración → Conexión** para el próximo inicio (siempre que el modelo y la VRAM asignada lo soporten).

---

## 6. Credenciales de Kaggle rechazadas (`Usuario o token incorrecto`)

- Con un token moderno `KGAT_...`, el panel detecta automáticamente el nombre de usuario mediante introspección OAuth.
- Si usás una clave legacy de 32 caracteres hexadecimales, debés subir el archivo `kaggle.json` completo o completar tanto el campo **Usuario** como el campo **Token o API key**.
- Si la validación falla, el panel conserva intacta la credencial anterior sin modificar la cuenta.

---

## 7. Pérdida de contraseña del panel web (`HTTP 401` en `/login`)

Las credenciales del panel web son independientes de Kaggle. Si olvidaste la contraseña del administrador, conectate por SSH a la VPS y ejecutá:

```bash
sudo -u kaggle-ia /opt/kaggle-ia/sistema/.venv/bin/python /opt/kaggle-ia/sistema/panel_password.py
sudo systemctl restart kaggle-ia
```

Ingresá una contraseña nueva (entre 16 y 256 caracteres). El reinicio de `kaggle-ia` aplica el nuevo hash `scrypt` y cierra las sesiones web previas sin apagar las GPUs de Kaggle que estén en ejecución.
