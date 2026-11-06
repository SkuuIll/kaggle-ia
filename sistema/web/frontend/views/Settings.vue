<script setup>
import PanelUsers from '../components/PanelUsers.vue';
</script>

<template>
  <section data-view="configuracion" hidden>
    <nav class="subnav" aria-label="Secciones de configuración">
      <button data-setting="general" aria-selected="true" onclick="setting('general')">General</button
      ><button data-setting="timers" aria-selected="false" onclick="setting('timers')">Autoapagado</button
      ><button data-setting="connection" aria-selected="false" onclick="setting('connection')">
        Conexión</button
      ><button data-setting="backups" aria-selected="false" onclick="setting('backups')">Respaldos</button
      ><button data-setting="security" aria-selected="false" onclick="setting('security')">Seguridad</button>
    </nav>
    <div class="editor">
      <article class="panel" data-setting-view="general">
        <h2>Preferencias del espacio</h2>
        <div class="setting-row">
          <div>
            <h3>Avisos de uso</h3>
            <p>
              Recibí avisos cuando una GPU sigue activa o queda poca cuota. Requiere dejar el panel abierto.
            </p>
          </div>
          <button id="notify" onclick="enableNotifications()">Activar avisos</button>
        </div>
        <div class="setting-row">
          <div>
            <h3>Modo de instalación</h3>
            <p id="installation-mode">Consultando…</p>
          </div>
          <span class="badge good">SSH privado</span>
        </div>
        <div class="setting-row">
          <div>
            <h3>Uso simultáneo</h3>
            <p>
              Una sola sesión GPU a la vez. Cambiar de cuenta detiene la anterior antes de iniciar la
              siguiente.
            </p>
          </div>
        </div>
        <div class="setting-row">
          <div>
            <h3>Cuotas y métricas</h3>
            <p>Las horas se consultan en Kaggle. Los tokens son estadísticas del proxy, no otra cuota.</p>
          </div>
          <button class="quiet" onclick="navigate('dashboard')">Ver consumo</button>
        </div>
      </article>
      <article class="panel" data-setting-view="timers" hidden>
        <div class="panel-title">
          <div>
            <h2>Protegé tus horas de GPU</h2>
            <p>Los cambios se aplican al próximo arranque.</p>
          </div>
          <i data-icon="clock"></i>
        </div>
        <form id="timer-form">
          <div class="field">
            <label for="timer-account">Cuenta</label
            ><select id="timer-account" onchange="loadTimers(true)"></select>
          </div>
          <div class="form-grid">
            <div class="field">
              <label for="timer-idle">Sin inferencia, en minutos</label
              ><input id="timer-idle" type="number" min="1" max="120" required />
            </div>
            <div class="field">
              <label for="timer-maximum">Límite de sesión, en minutos</label
              ><input id="timer-maximum" type="number" min="5" max="120" required />
            </div>
          </div>
          <div class="notice">
            Se ejecuta dentro de Kaggle, aunque cierres el navegador. El límite absoluto puede terminar una
            generación larga. Los valores nuevos no cambian una sesión ya encendida.
          </div>
          <button type="submit" class="primary operation">Guardar autoapagado</button>
        </form>
      </article>
      <article class="panel" data-setting-view="connection" hidden>
        <h2>Diagnóstico y ahorro</h2>
        <p class="small muted">
          Comprobá la conexión sin generar texto ni encender una GPU. Los cambios de rendimiento se aplican al
          próximo arranque.
        </p>
        <div class="field">
          <label for="ops-account">Cuenta para revisar</label
          ><select id="ops-account" onchange="renderOperationControls()"></select>
        </div>
        <div class="buttons">
          <button onclick="diagnoseAccount()">Diagnosticar conexión</button
          ><button class="primary operation" onclick="prepareWork()">Preparar para trabajar</button
          ><button id="extend-work" class="operation" onclick="extendWork()">
            Seguir trabajando · +30 min
          </button>
        </div>
        <p id="ops-result" class="notice" role="status">
          El diagnóstico revisa Kaggle, la API HTTPS y el modelo cargado. Paseo se comprueba desde tu PC con
          ABRIR_PASEO.bat.
        </p>
        <div class="field">
          <label for="performance-profile">Perfil para el próximo inicio</label
          ><select id="performance-profile">
            <option value="rapido">Respuesta rápida · 16k contexto / 1k salida</option>
            <option value="codigo">Código · 32k contexto / 4k salida</option>
            <option value="contexto" selected>Contexto largo · 128k contexto / 4k salida</option>
          </select>
        </div>
        <button class="operation" onclick="savePerformanceProfile()">Guardar perfil</button>
        <p class="hint">
          Un contexto menor puede reducir memoria y procesamiento. La velocidad real depende del modelo, la
          GPU y el contenido del chat.
        </p>
        <hr />
        <details style="margin: 18px 0">
          <summary>Preparar pesos con CPU para ahorrar arranques</summary>
          <p class="hint">
            La cuenta seleccionada arriba prepara un notebook CPU privado. Cuando termine, verificá y adjuntá
            la caché al próximo arranque. No enciende GPU. Las salidas permanecen en Kaggle; no se descargan
            los pesos a esta VPS. Disponible para archivos de hasta 18 GiB.
          </p>
          <div class="buttons">
            <button class="operation" onclick="cacheAction('cache_launch')">Preparar caché con CPU</button
            ><button class="operation" onclick="cacheAction('cache_status')">Consultar estado</button
            ><button class="operation" onclick="cacheAction('cache_attach')">Verificar y usar caché</button
            ><button class="operation" onclick="cacheAction('cache_detach')">Desactivar caché</button>
          </div>
          <p class="hint">
            El estado PREPARED indica solamente configuración; COMPLETE con manifiesto verificado permite
            adjuntarla. Si cambia el modelo o la revisión, se prepara una caché nueva. El diagnóstico del
            próximo notebook informará GPU, controlador, Python, motor y origen de los pesos.
          </p>
        </details>
        <h2>Conectar Paseo, OpenCode y Continue</h2>
        <p class="small muted">
          Los clientes usan las direcciones HTTPS y la clave API de su cuenta. Podés preparar sus
          configuraciones completas en este apartado.
        </p>
        <div id="connection-list"></div>
        <hr />
        <h2>Tu configuración, lista para usar</h2>
        <p class="small muted">
          Elegí la cuenta y prepará sus ejemplos. La clave de la API es distinta de tu contraseña del panel y
          del token de Kaggle.
        </p>
        <div class="field">
          <label for="client-account">Cuenta para los ejemplos</label
          ><select id="client-account" onchange="clearClientConfig()"></select>
        </div>
        <button id="client-prepare" class="primary" onclick="prepareClientConfig()">
          Preparar configuración privada
        </button>
        <div id="client-config-area" hidden>
          <div class="notice">
            La vista oculta la clave. Al usar Copiar configuración o descargar el paquete se incluye la clave
            real. Guardá estos archivos en privado.
          </div>
          <div class="field">
            <label for="client-api-key">Clave API de esta conexión</label
            ><input id="client-api-key" type="password" readonly autocomplete="off" />
            <div class="buttons" style="margin-top: 10px">
              <button id="client-show-key" onclick="toggleClientKey()">Mostrar clave</button
              ><button onclick="copyClientKey()">Copiar clave</button
              ><button onclick="probeClientAPI()">Probar API</button>
            </div>
          </div>
          <p id="client-probe-result" class="hint" role="status"></p>
          <div class="field">
            <label for="snippet-client">Cliente</label
            ><select id="snippet-client" onchange="renderClientSnippet()">
              <option value="opencode">OpenCode · opencode.json</option>
              <option value="paseo">Paseo · config.json</option>
              <option value="continue">Continue · config.yaml</option>
            </select>
          </div>
          <pre
            id="client-snippet"
            class="log"
            style="max-height: 370px"
            aria-label="Ejemplo de configuración"
          ></pre>
          <p id="client-snippet-help" class="hint"></p>
          <button onclick="copyClientConfig()">Copiar configuración</button>
          <hr />
          <h2>Configuración automática en Windows</h2>
          <p class="small muted">
            Descargá y descomprimí el paquete privado. Ejecutá INSTALAR.bat si faltan dependencias y después
            CONFIGURAR_CLIENTES.bat y ABRIR_PASEO.bat. Se respaldan y combinan tus configuraciones actuales;
            no se borran tus chats ni se enciende una GPU.
          </p>
          <a id="client-package" class="download">Descargar paquete privado</a>
          <p class="hint">
            Paseo usa OpenCode como motor. El instalador resuelve la ruta del ejecutable en tu PC. Si copiás
            el ejemplo de Paseo a mano, OpenCode debe estar en PATH o tenés que indicar su ruta completa.
          </p>
          <hr />
          <div class="notice">
            El autoapagado por inactividad y el límite de sesión pueden detener el modelo. Abrir Paseo no lo
            enciende automáticamente; revisá su estado en el Dashboard.
          </div>
          <h2>Si Paseo no conecta</h2>
          <p class="small muted">
            1. Si la cuenta figura apagada, encendela y esperá LISTO en Actividad.<br />2. Comprobá que el
            proveedor use la URL HTTPS y su clave.<br />3. Recargá Paseo y abrí un chat nuevo.<br />4. Si dice
            que el daemon no está iniciado, ejecutá <code>paseo daemon start</code>.
          </p>
          <p class="hint">
            El servicio de Paseo puede usar 127.0.0.1:6767 en tu PC: es su conexión con la aplicación. El
            modelo usa el dominio HTTPS del panel.
          </p>
        </div>
        <div class="notice">
          Cerrar el IDE o la conexión SSH no detiene la GPU. Usá los controles de apagado del panel.
        </div>
        <button id="open-paseo" hidden class="operation" onclick="act('paseo')">
          Abrir Paseo en esta PC
        </button>
      </article>
      <article class="panel" data-setting-view="backups" hidden>
        <h2>Respaldos y traslado</h2>
        <div class="setting-row">
          <div>
            <h3>Código para instalar o publicar</h3>
            <p>Programa y documentación, sin credenciales, registros ni notebooks privados.</p>
          </div>
          <button class="operation" onclick="act('export_program')">
            <i data-icon="download"></i>Exportar código
          </button>
        </div>
        <div class="setting-row">
          <div>
            <h3>Conexión privada</h3>
            <p>Contiene tus APIs y la clave SSH. El ZIP no está cifrado; guardalo como una contraseña.</p>
          </div>
          <button class="operation" onclick="privateBackup()">
            <i data-icon="shield"></i>Respaldar conexión
          </button>
        </div>
        <div class="setting-row">
          <div>
            <h3>Importar una conexión</h3>
            <p>Reemplaza la configuración. Primero deben estar confirmadas las paradas actuales.</p>
          </div>
          <button class="operation" onclick="document.getElementById('restore').click()">Importar ZIP</button
          ><input id="restore" type="file" accept=".zip" hidden onchange="restorePrivate(this)" />
        </div>
        <div id="backup-download"></div>
        <p class="hint">
          Cuando termine la exportación, podés descargarla acá o en Actividad. Los enlaces requieren tu
          sesión.
        </p>
      </article>
      <article class="panel" data-setting-view="security" hidden>
        <h2>Acceso y sesión</h2>
        <div class="setting-row">
          <div>
            <h3 id="security-username">Tu cuenta del panel</h3>
            <p>Independiente de las APIs de Kaggle. Sesiones de hasta 8 horas.</p>
          </div>
          <span class="badge good">HTTPS</span>
        </div>
        <div class="setting-row">
          <div>
            <h3>Contraseña</h3>
            <p>Al cambiarla se cierran las sesiones de tu usuario. Los modelos continúan funcionando.</p>
          </div>
          <button id="change-password" onclick="openPassword()">Cambiar contraseña</button>
        </div>
        <div class="setting-row">
          <div>
            <h3>Cerrar sesión</h3>
            <p>Revoca este acceso al panel. No apaga las GPU.</p>
          </div>
          <button id="security-logout" onclick="logout()">Cerrar sesión</button>
        </div>
        <div id="panel-user-management" hidden><PanelUsers /></div>
      </article>
    </div>
  </section>
</template>
