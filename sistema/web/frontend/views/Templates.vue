<template>
  <section data-view="plantillas" hidden>
    <article class="panel">
      <div class="panel-title">
        <div>
          <h2>Tu catálogo de IA y Herramientas</h2>
          <p>
            Modelos probados, herramientas y flujos de trabajo para tus cuentas.
          </p>
        </div>
      </div>
      <div class="template-toolbar">
        <div class="field">
          <label for="template-account">Cuenta de destino</label
          ><select id="template-account" onchange="renderTemplates()"></select>
        </div>
        <div class="field">
          <label for="template-filter">Categoría</label
          ><select id="template-filter" onchange="renderTemplates()">
            <option value="all">Todo el catálogo</option>
            <option value="models">
              Modelos de IA
            </option>
            <option value="tools">Herramientas y librerías</option>
            <option value="workflows">Instrucciones de trabajo</option>
          </select>
        </div>
        <div class="field">
          <label for="template-search">Buscar plantilla</label
          ><input
            id="template-search"
            placeholder="RVN, Heretic, Aider, HTTPX, código…"
            oninput="renderTemplates()"
          />
        </div>
      </div>
      <div class="notice">
        Instalar una plantilla prepara la configuración y el notebook privado con
        <code>FlashAttention</code> y caché <code>KV Q8_0</code>. Los pesos se descargan recién al encender.
      </div>
      <p id="template-result" role="status" class="hint"></p>
      <div id="template-download"></div>
      <div class="buttons" style="margin: 16px 0">
        <button onclick="navigate('cuentas')">
          <i data-icon="users"></i>Ir a Cuentas</button
        ><button onclick="openChatForAccount(el('template-account').value)">
          <i data-icon="chat"></i>Abrir en Chat Web</button
        ><button
          onclick="openClientSetupForAccount(el('template-account').value)"
        >
          Preparar configuración de clientes <i data-icon="arrow"></i>
        </button>
      </div>
      <div id="template-library" class="template-grid"><p>Cargando catálogo…</p></div>
    </article>
    <article class="panel" style="margin-top: 22px">
      <h2>Fuentes y optimizaciones del motor</h2>
      <p class="hint">
        Componentes integrados en el servidor de inferencia para maximizar los TPS y proteger tus horas de
        GPU.
      </p>
      <div id="template-sources" class="template-grid"></div>
    </article>
  </section>
</template>
