# Chat y arranque web

## Abrir una sesión

En **Inicio**, la consola muestra el estado de una cuenta y el acceso directo a **Iniciar servidor**. Debajo, **Servidores** reúne los controles por cuenta y **Uso y cuota** reúne las métricas.

1. Entrá al panel HTTPS. En **Cuentas**, comprobá que la cuenta tenga credenciales válidas.
2. Abrí **Chat IA**. El selector superior define la cuenta y el perfil del chat actual.
3. Pulsá **Iniciar servidor**. Si ya hay otra cuenta activa, leé el aviso de cambio antes de confirmar.
4. Seguí **Actividad** para ver la publicación del notebook, la cola, la preparación del modelo y el resultado del controlador. La cola de Kaggle tiene duración variable.
5. Cuando el chat indique **Servidor conectado**, enviá un mensaje breve. Ese primer resultado comprueba la generación de extremo a extremo.

| Estado | Qué podés hacer |
| --- | --- |
| Apagado | Iniciar el servidor y preparar el mensaje |
| En cola | Preparar el mensaje y seguir Actividad |
| Preparando el servidor | Esperar a que aparezca el relay de inferencia |
| Servidor conectado | Enviar el mensaje o abrir el cliente IDE con su URL HTTPS y API key |
| Estado sin confirmar | Consultar Actividad y ejecutar el diagnóstico |

## Conversaciones y contexto

- En el teléfono, abrí **Ver conversaciones** para cambiar de chat. El editor conserva el borrador de cada conversación mientras la página esté abierta. Usá **Enviar** para mandar el mensaje.
- En escritorio, **Enter** envía y **Mayús + Enter** agrega una línea. El botón **Enviar** también está disponible.
- En **Opciones → Ajustes del chat**, elegí un modo de trabajo o guardá una instrucción de sistema. El menú **Opciones** también agrupa diagnóstico, nombre, exportación y archivo.
- Podés adjuntar hasta 8 archivos, de 15 MB como máximo por archivo y 30 MB en total por mensaje. El modelo recibe el texto que se pudo extraer, las imágenes compatibles, muestras del video o la transcripción del audio cuando está disponible.
- El historial completo se guarda en el panel. Si se supera el presupuesto de contexto, se omiten mensajes antiguos del envío al modelo y el chat indica cuántos. Las respuestas fallidas siguen visibles para diagnóstico.
- **Cancelar** solicita cerrar una generación. Para terminar la sesión GPU, elegí **Apagar** en Cuentas y comprobá la parada en Actividad.

## Velocidad de una respuesta

Cuando el motor devuelve el conteo de tokens, la respuesta muestra los **TPS promedio**, los tokens de salida y el tiempo transcurrido hasta recibir ese conteo. Es el rendimiento observado desde el panel e incluye la espera y el razonamiento de la solicitud. El dato queda guardado junto a la respuesta. Para obtener una medición, iniciá una cuenta y enviá un mensaje.

## Visor de adjuntos

Pulsá **Vista previa** en la tarjeta del archivo para abrir el visor sin salir de la conversación.

- Las imágenes se amplían y los videos y audios compatibles se reproducen con los controles del navegador.
- El visor de documentos y código muestra el texto extraído al subirlos. Para PDF, **Abrir PDF** abre el original en otra pestaña, incluso cuando el documento es un escaneo.
- **Descargar original** está disponible también para archivos sin texto extraíble o con formatos que el navegador no reproduce.

## Pool de inferencia

El endpoint compartido `https://ia.example.com/inference/pool/v1` dirige las solicitudes a una cuenta cuyo relay ya responde. El historial del Chat IA se guarda en la VPS y se puede consultar con la GPU apagada. Cuando no hay un relay disponible, iniciá una cuenta desde el panel. La rotación automática y el precalentamiento aparecen en notas históricas como diseño, pero el servicio actual no ejecuta ese orquestador.

## Retomar un chat

El navegador recuerda la última conversación, la cuenta elegida y hasta 20 borradores de texto en este dispositivo. El historial del servidor conserva los mensajes enviados. En el menú de cada conversación podés renombrarla o archivarla.

Encendé o apagá la GPU desde **Inicio → Servidores**. El chat muestra el estado de la cuenta seleccionada y permite escribir durante la espera. En Actividad, el panel distingue la preparación, la descarga y la carga cuando el notebook informa esas etapas. **GPU lista** requiere la confirmación del controlador.

## Cuota de GPU

Inicio y Cuentas muestran las horas y la fecha de renovación que informa Kaggle. El contador se actualiza en el navegador y muestra la fecha en la zona horaria del dispositivo. Al llegar la hora, el panel espera una nueva lectura de Kaggle antes de mostrar la siguiente renovación. Si falta la fecha o la cuota, se indica que el dato sigue sin confirmar.

## Mantenimiento

El frontend está en `sistema/web/frontend/`. `App.vue` arma el panel con componentes para la navegación, diálogos y siete vistas. `Login.vue` gestiona el formulario público y su estado. El panel monta las vistas antes de inicializar `chat/workspace.js` y `dashboard.js`, que conservan los contratos de la API, el historial, el envío de mensajes y las operaciones de GPU. Si modificás una vista, conservá los IDs que usan esos controladores o actualizá ambas partes juntas.

`design-system.css` define la paleta oscura, los controles y los estados compartidos. `frontend/workspace.css` define el diseño del panel y del chat sobre los estilos funcionales de `panel.css`. En escritorio el chat deja visibles la navegación principal y el historial. En móvil las dos barras laterales se abren por separado, Escape cierra la que está abierta y el historial de mensajes se desplaza dentro del chat.

Tocá la fila de cuenta y estado en el chat para cambiar de cuenta. El selector muestra el número y el nombre de la cuenta. El modelo se identifica debajo del título de la conversación. Los controles Encender y Apagar están en la tarjeta del servidor en Inicio. Apagar pide confirmación. El panel muestra el envío y sigue la operación hasta que el controlador confirma el resultado. Encender distingue la cola y la carga del modelo. Apagar puede esperar a que termine la operación anterior y después verifica el estado en Kaggle. La notificación final distingue el resultado confirmado de un error. Actividad muestra la etapa actual y ofrece el registro técnico desplegable. Inicio y Cuentas muestran los mismos estados de GPU.

### Compilar

Desde la raíz del proyecto, con Node.js 22.12 o superior:

```powershell
npm --prefix sistema/web/frontend ci
npm --prefix sistema/web/frontend run build
```

El resultado queda en `sistema/web/dist/ui/` y `sistema/web/dist/login/`. Para iterar con el servidor local abierto, `npm --prefix sistema/web/frontend run dev` recompila el panel al guardar y `run dev:login` hace lo mismo con el acceso. Recargá el navegador para ver el resultado. Modificá los fuentes y regenerá los bundles antes de distribuir.

### Instalar en la VPS

Publicá en conjunto los cuatro archivos de `dist/`, los dos HTML, los controladores del navegador y `sistema/core/panel_server.py`. Python sirve el resultado en el mismo origen que las APIs. Node se usa en la máquina de compilación. La VPS solo necesita los archivos ya compilados.

La primera actualización requiere recargar el servicio Python para incorporar las nuevas rutas de assets. Ese servicio también atiende las APIs de inferencia. Hacé la actualización cuando no haya solicitudes u operaciones en curso. La compilación pública de acceso está separada del panel y de sus controladores, que requieren sesión.

### Verificar

Probá el acceso con sesión vencida y con un error de credenciales, las siete vistas, el historial vacío y con mensajes, el editor y los adjuntos. Revisá el desplazamiento de tablas y código largos en pantallas angostas, el foco de los controles y el cierre de los menús con Escape. Registrá por separado el estado de la web, la generación real y las operaciones de inicio o parada.

Consultá las comprobaciones del [README](../../README.md) y la [guía de VPS](VPS.md).
