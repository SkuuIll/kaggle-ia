# Chat y arranque web

## Abrir una sesión

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

## Visor de adjuntos

Pulsá **Vista previa** en la tarjeta del archivo para abrir el visor sin salir de la conversación.

- Las imágenes se amplían y los videos y audios compatibles se reproducen con los controles del navegador.
- El visor de documentos y código muestra el texto extraído al subirlos. Para PDF, **Abrir PDF** abre el original en otra pestaña, incluso cuando el documento es un escaneo.
- **Descargar original** está disponible también para archivos sin texto extraíble o con formatos que el navegador no reproduce.

## Pool de inferencia

El endpoint compartido `https://ia.example.com/inference/pool/v1` dirige las solicitudes a una cuenta cuyo relay ya responde. El historial del Chat IA se guarda en la VPS y se puede consultar con la GPU apagada. Cuando no hay un relay disponible, iniciá una cuenta desde el panel. La rotación automática y el precalentamiento aparecen en notas históricas como diseño, pero el servicio actual no ejecuta ese orquestador.

## Mantenimiento

El HTML principal carga primero `sistema/web/chat/workspace.js` y después `sistema/web/dashboard.js`. El módulo del chat contiene el editor, historial, adjuntos y seguimiento. El tablero mantiene navegación, arranque y sesión. Ambos se sirven con autenticación desde rutas de assets explícitas.

Revisá las comprobaciones locales del [README](../../README.md) y la [guía de VPS](VPS.md). Para validar una actualización, comprobá el login, las siete vistas, el chat en móvil, las rutas de assets y el estado autenticado de las cuentas. Registrá por separado si hubo envío al controlador, generación real, parada confirmada y reinicio probado.
