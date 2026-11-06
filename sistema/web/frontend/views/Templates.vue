<template>
  <section data-view="plantillas" hidden>
    <article class="panel">
      <div class="panel-title">
        <div>
          <h2>Tu catálogo de IA y Herramientas</h2>
          <p>
            Modelo único oficial Qwen3.8 27B RVN Heretic · Multilingual MTP (128k), paquetes locales y flujos
            de trabajo.
          </p>
        </div>
        <a
          href="https://huggingface.co/0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF"
          target="_blank"
          rel="noreferrer"
          >Repositorio 0bserverx <i data-icon="external"></i
        ></a>
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
              <i data-icon="check"></i> Modelo IA (Qwen3.8 27B RVN Heretic · 128k)
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
        <button class="primary operation" onclick="startAccount(el('template-account').value)">
          <i data-icon="play"></i>Encender cuenta elegida</button
        ><button onclick="openChatForAccount(el('template-account').value)">
          <i data-icon="chat"></i>Abrir en Chat Web</button
        ><button
          onclick="
            navigate('configuracion');
            setting('connection');
          "
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
