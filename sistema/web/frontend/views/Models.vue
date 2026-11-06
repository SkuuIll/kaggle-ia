<template>
  <section data-view="modelos" hidden>
    <div class="models-layout">
      <div class="models-col">
        <article class="panel">
          <div class="panel-title">
            <div>
              <h2>Modelos por cuenta</h2>
              <p>Consultá qué está listo y qué se usará en el próximo inicio.</p>
            </div>
          </div>
          <div class="field">
            <label for="model-account">Cuenta de destino</label>
            <select id="model-account" onchange="loadModel(true)"></select>
          </div>
          <div id="model-current" class="notice"></div>
          <h3 class="model-section-title">Modelos disponibles</h3>
          <p class="hint">Los resultados corresponden a pruebas de código corto en dos Tesla T4. El motor, el contexto y la tarea pueden cambiar la velocidad.</p>
          <div id="quick-tps-models" class="tps-grid"></div>
        </article>

        <article class="panel">
          <div class="panel-title">
            <div>
              <h2>Repositorio personalizado (Hugging Face GGUF)</h2>
              <p>Los pesos se descargan en Kaggle, nunca en tu PC ni en la VPS.</p>
            </div>
            <i data-icon="cpu"></i>
          </div>
          <form id="model-form">
            <div class="field">
              <label for="model-repo">Repositorio de Hugging Face</label
              ><input id="model-repo" placeholder="https://huggingface.co/autor/modelo-GGUF" required />
              <p class="hint">Repositorio público con un archivo GGUF único.</p>
            </div>
            <button id="inspect-button" type="button" class="operation" onclick="inspectModel()">
              <i data-icon="refresh"></i>Buscar archivos GGUF
            </button>
            <div id="inspect-result" class="error-text" role="status"></div>
            <hr />
            <div class="field">
              <label for="model-file">Archivo y cuantización</label
              ><select id="model-file" required></select>
            </div>
            <div class="field">
              <label for="model-context">Contexto en tokens</label
              ><input id="model-context" type="number" min="4096" max="1048576" required />
              <p class="hint">
                Un contexto de 16k–32k maximiza los TPS; 128k reserva más VRAM para caché KV.
              </p>
            </div>
            <div class="notice">
              Guardar detiene la sesión anterior si estaba encendida. Los pesos se descargan cuando encendés la GPU desde Cuentas.
            </div>
            <button type="submit" class="primary operation">
              Guardar para el próximo arranque
            </button>
          </form>
        </article>
      </div>

    </div>
  </section>
</template>
