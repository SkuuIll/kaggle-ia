<template>
  <section data-view="dashboard">
    <article class="launch-console" aria-labelledby="launch-title">
      <div class="launch-story">
        <p class="launch-label">CONTROL DE GPU</p>
        <h1 id="launch-title">Resumen de inferencia</h1>
        <p>Administrá las sesiones de Kaggle y revisá el consumo de tus modelos.</p>
        <button type="button" class="launch-chat" onclick="navigate('chat')">
          <i data-icon="chat"></i>Continuar chat<i data-icon="arrow"></i>
        </button>
      </div>
      <div id="workflow-stepper" class="launch-status" aria-label="Estado y control del servidor">
        <p class="launch-label">ESTADO DEL SERVIDOR</p>
        <h2>Consultando Kaggle</h2>
        <p>Buscando el último estado disponible.</p>
      </div>
    </article>
    <div class="section-heading dashboard-section">
      <div>
        <h2>Uso y cuota</h2>
        <p class="hint">Consumo informado por Kaggle y solicitudes registradas por el proxy.</p>
      </div>
    </div>
    <div class="toolbar">
      <span class="small muted">Resumen de uso y telemetría</span
      ><label class="sr-only" for="dashboard-filter">Filtrar métricas por cuenta</label
      ><select id="dashboard-filter" class="filter" onchange="renderDashboard()">
        <option value="all">Todas las cuentas</option>
      </select>
    </div>
    <div class="kpis">
      <article class="kpi">
        <div class="kpi-head">Sesiones activas<i data-icon="cpu"></i></div>
        <strong id="kpi-active">—</strong>
        <div class="caption" id="kpi-active-note">Estado oficial de Kaggle</div>
      </article>
      <article class="kpi">
        <div class="kpi-head">Horas disponibles<i data-icon="clock"></i></div>
        <strong id="kpi-hours">—</strong>
        <div class="caption" id="kpi-hours-note">Cuota oficial disponible</div>
      </article>
      <article class="kpi">
        <div class="kpi-head">Tokens medidos<i data-icon="activity"></i></div>
        <strong id="kpi-tokens">—</strong>
        <div class="caption">Entrada + salida · historial registrado</div>
      </article>
      <article class="kpi">
        <div class="kpi-head">Solicitudes<i data-icon="code"></i></div>
        <strong id="kpi-requests">—</strong>
        <div class="caption" id="kpi-requests-note">A través de la conexión medida</div>
      </article>
    </div>
    <div class="split">
      <article class="panel">
        <div class="panel-title">
          <div>
            <h2>Cuota y renovación</h2>
            <p>Horas y fecha de renovación por cuenta</p>
          </div>
          <i data-icon="clock"></i>
        </div>
        <div id="quota-list"></div>
        <p class="hint">Las horas reservadas reducen el saldo. Kaggle informa el límite y la renovación de cada cuenta.</p>
      </article>
      <article class="panel">
        <div class="panel-title">
          <div>
            <h2>Actividad de tokens</h2>
            <p>Últimos 7 días · agrupación por día UTC</p>
          </div>
          <div class="legend" id="chart-legend" hidden>
            <span><i></i>Entrada</span><span><i class="out"></i>Salida</span>
          </div>
        </div>
        <div id="usage-chart"></div>
        <p class="hint" id="chart-note"></p>
      </article>
    </div>
    <details class="panel connection-details" id="operation-mode-card">
      <summary>Endpoints para clientes</summary>
      <div class="panel-title">
        <div>
          <h2>Conexión por pool o por cuenta</h2>
          <p class="hint">Elegí cómo usar tus modelos en Paseo, Continue, OpenCode o agentes (Hermes)</p>
        </div>
        <div id="pool-status-pill" class="badge good">Consultando estado</div>
      </div>
      <div class="split" style="margin-top: 14px; gap: 16px">
        <div
          style="
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
            background: var(--card-bg);
          "
        >
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px">
            <i data-icon="refresh"></i>
            <b style="font-size: 15px">Pool de inferencia</b>
          </div>
          <p class="small muted" style="margin: 0 0 10px 0; line-height: 1.4">
            Un endpoint compartido para las cuentas que ya responden. Iniciá una cuenta desde el panel si no
            hay un servidor disponible.
          </p>
          <code
            style="
              display: block;
              padding: 6px 10px;
              background: var(--bg);
              border-radius: 6px;
              font-size: 12px;
              margin-bottom: 8px;
            "
            >https://ia.example.com/inference/pool/v1</code
          >
          <div style="display: flex; align-items: center; justify-content: space-between">
            <small class="muted" id="pool-active-info">Consultando conexiones</small>
          </div>
        </div>
        <div
          style="
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px;
            background: var(--card-bg);
          "
        >
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px">
            <i data-icon="cpu"></i>
            <b style="font-size: 15px">Modo Cuenta Individual</b>
          </div>
          <p class="small muted" style="margin: 0 0 10px 0; line-height: 1.4">
            Control manual directo por cuenta (Cuenta 1 a 8). Podés encender, apagar, cambiar de modelo o
            probar una cuenta específica por separado.
          </p>
          <code
            style="
              display: block;
              padding: 6px 10px;
              background: var(--bg);
              border-radius: 6px;
              font-size: 12px;
              margin-bottom: 8px;
            "
            >https://ia.example.com/inference/cuentaN/v1</code
          >
          <div style="display: flex; align-items: center; justify-content: space-between">
            <small class="muted">Cuentas preparadas: <span id="individual-accounts-count">—</span></small>
            <span class="badge" style="font-size: 11px">Manual</span>
          </div>
        </div>
      </div>
    </details>
    <article class="panel" style="margin-top: 22px">
      <div class="panel-title">
        <div>
          <h2>Actividad reciente</h2>
          <p>Operaciones realizadas desde este panel</p>
        </div>
        <button class="quiet" onclick="navigate('actividad')">Ver todo <i data-icon="arrow"></i></button>
      </div>
      <div id="recent-events"></div>
    </article>
    <p class="footnote">
      Los tokens incluyen solo solicitudes que pasan por el proxy medido. Las conversaciones del Chat Web se
      guardan en privado dentro del servidor y nunca se incluyen en exportaciones públicas. Configurar un
      contexto no garantiza que entre en la VRAM asignada.
    </p>
  </section>
</template>
