<template>
  <section data-view="modelos" hidden>
    <div class="models-layout">
      <div class="models-col">
        <article class="panel">
          <div class="panel-title">
            <div>
              <h2>Modelo Único Activo · Qwen3.8 27B RVN Heretic (Multilingual MTP)</h2>
              <p>
                Instalado y unificado en Cuenta 1 y Cuenta 2 (128k activos / 262k nativos · 0bserverx
                RVN-Q4_K_M-multilingual-mtp.gguf).
              </p>
            </div>
            <span class="badge on"><i data-icon="activity"></i> DeltaNet + MTP ×4 · 128k</span>
          </div>
          <div class="field">
            <label for="model-account">Cuenta de destino</label>
            <select id="model-account" onchange="loadModel(true)"></select>
          </div>
          <div id="model-current" class="notice"></div>
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
              Aplicar detiene el modelo anterior si estaba encendido. Kaggle decide la cola; la descarga se
              realiza directamente en los servidores de Google/Kaggle.
            </div>
            <button type="submit" class="primary operation">
              <i data-icon="play"></i>Aplicar modelo y arrancar
            </button>
          </form>
        </article>
      </div>

      <aside class="models-col">
        <article class="panel">
          <div class="panel-title">
            <div>
              <h2>Arquitectura de GPUs en Kaggle y cómo triplicar tus TPS</h2>
              <p>Investigación técnica para NVIDIA Tesla T4 ×2 (Turing sm_75)</p>
            </div>
            <i data-icon="activity"></i>
          </div>
          <div class="gpu-specs">
            <div class="spec-box">
              <small>GPUs asignadas</small><strong>2 × Tesla T4</strong
              ><span>16 GB GDDR6 c/u (32 GB total)</span>
            </div>
            <div class="spec-box">
              <small>Ancho de banda</small><strong>320 GB/s</strong
              ><span>Por GPU · Cuello de botella real</span>
            </div>
            <div class="spec-box">
              <small>Optimizaciones activas</small><strong>FlashAttn + Q8_0</strong
              ><span>50% menos VRAM en caché KV</span>
            </div>
          </div>
          <div class="tps-explain">
            <h3>1. Abliteración ARA de 3 pasadas (0–1% rechazos · KL ≈ 0.0085)</h3>
            <p>
              El modelo <strong>Qwen3.8 27B RVN Heretic</strong> de <code>0bserverx</code> aplica optimización
              matricial <strong>ARA (Arbitrary-Rank Ablation)</strong> en 3 pasadas completas sobre los pesos
              base, reduciendo los rechazos al 0–1% sin degradar el razonamiento ni la capacidad de
              programación.
            </p>
            <h3>2. Cabezal MTP embebido (Multi-Token Prediction ×4)</h3>
            <p>
              El archivo <code>RVN-Q4_K_M-multilingual-mtp.gguf</code> (17.0 GB) incluye el cabezal oficial
              MTP/NextN de 15 tensores con <code>draft_num_predict=4</code> activado en ambas cuentas para
              acelerar la generación en las 2× Tesla T4.
            </p>
            <h3>3. 48 capas Gated DeltaNet (-75% de caché KV en 128k–262k)</h3>
            <p>
              Gracias a su arquitectura híbrida (48 capas de atención lineal DeltaNet + 16 GQA con
              <code>OLLAMA_KV_CACHE_TYPE=q8_0</code>), la ventana de
              <strong>131.072 (128k) tokens</strong> deja <strong>15 GB de VRAM libres</strong> en las dos
              placas T4.
            </p>
          </div>
        </article>
      </aside>
    </div>
  </section>
</template>
