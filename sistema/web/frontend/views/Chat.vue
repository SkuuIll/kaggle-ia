<template>
  <section data-view="chat" hidden>
    <div class="chat-workspace" id="chat-dropzone">
      <div class="chat-drop-overlay" id="chat-drop-overlay" hidden>
        <div class="chat-drop-box">
          <i data-icon="upload"></i>
          <h3>Soltá tus archivos para adjuntarlos al chat</h3>
          <p>
            Documentos (PDF, Word, Excel, PowerPoint, código, texto), fotos (PNG, JPG, WEBP, GIF), videos
            (MP4, WEBM, MOV) y audio (MP3, WAV, OGG) · hasta 15 MB por archivo.
          </p>
        </div>
      </div>

      <button
        type="button"
        id="chat-sidebar-backdrop"
        aria-label="Cerrar historial"
        onclick="setChatSidebar(false)"
        hidden
      ></button>
      <aside class="chat-sidebar" id="chat-sidebar">
        <div class="chat-sidebar-top">
          <div class="chat-sidebar-mobile-head">
            <span class="chat-sidebar-title">Historial de Chats</span>
            <button
              class="sidebar-close-btn"
              onclick="toggleChatSidebar()"
              aria-label="Cerrar lista de chats"
            >
              <i data-icon="x"></i>
            </button>
          </div>
          <h2 class="chat-history-heading">Conversaciones</h2>
          <button class="chat-new-chat-btn" onclick="createChatConversation()">
            <i data-icon="plus"></i><span>Nueva conversación</span>
          </button>
          <div class="chat-search-wrap">
            <i data-icon="search" class="chat-search-icon"></i>
            <input
              id="chat-search"
              aria-label="Buscar conversaciones"
              class="chat-search-input"
              placeholder="Buscar conversación…"
              oninput="renderChatList()"
            />
          </div>
        </div>
        <div class="chat-history-feedback">
          <p id="chat-history-status" class="hint" role="status" hidden></p>
          <button
            id="chat-history-retry"
            type="button"
            class="quiet"
            onclick="loadChatConversations()"
            hidden
          >
            Reintentar
          </button>
        </div>
        <div id="chat-list" class="chat-conv-list" role="list" aria-label="Conversaciones guardadas"></div>
      </aside>

      <div class="chat-main">
        <header class="chat-header">
          <div class="chat-heading">
            <button
              id="chat-sidebar-toggle"
              aria-controls="chat-sidebar"
              aria-expanded="false"
              class="chat-icon-btn mobile-chat-toggle"
              onclick="toggleChatSidebar()"
              title="Ver conversaciones"
              aria-label="Ver conversaciones"
            >
              <i data-icon="layers"></i>
            </button>
            <div class="chat-thread-meta">
              <h2 id="chat-active-title">Nueva conversación</h2>
            </div>
          </div>
          <div class="chat-header-actions">
            <details id="chat-more" class="chat-more">
              <summary title="Opciones de conversación" aria-label="Opciones de conversación">
                <i data-icon="settings"></i><span>Opciones</span>
              </summary>
              <div class="chat-more-panel" aria-label="Acciones de conversación">
                <button type="button" onclick="toggleChatSettings()">
                  <i data-icon="sliders"></i>Ajustes del chat
                </button>
                <button id="chat-quick-diagnose" type="button" onclick="diagnoseChatAccount()">
                  <i data-icon="shield"></i>Diagnosticar conexión
                </button>
                <button type="button" onclick="renameChatConversation()">
                  <i data-icon="edit"></i>Renombrar conversación
                </button>
                <button type="button" onclick="downloadChatMarkdown()">
                  <i data-icon="download"></i>Descargar Markdown
                </button>
                <button type="button" onclick="exportChatZip()">
                  <i data-icon="archive"></i>Exportar ZIP
                </button>
                <button type="button" class="danger" onclick="deleteChatConversation()">
                  <i data-icon="trash"></i>Archivar conversación
                </button>
              </div>
            </details>
          </div>
        </header>
        <details id="chat-server-details" class="chat-server-details">
          <summary>
            <i data-icon="cpu"></i>
            <span id="chat-server-account">Cuenta de Kaggle</span>
            <span id="chat-gpu-pill" class="badge" role="status">Consultando GPU…</span>
            <i data-icon="chevron-down"></i>
          </summary>
          <div class="chat-session-bar">
            <div class="chat-account-field">
              <label for="chat-account">Cuenta de Kaggle</label>
              <select id="chat-account" onchange="changeChatAccount(this.value)">
                <option value="">Elegí una cuenta</option>
              </select>
            </div>
          </div>
        </details>

        <dialog id="chat-settings-drawer" class="chat-drawer" aria-labelledby="chat-settings-title">
          <div class="chat-drawer-inner">
            <h2 id="chat-settings-title">Ajustes del chat</h2>
            <div class="field">
              <label for="chat-workflow-preset">Modo de trabajo</label>
              <div class="chat-pill-dropdown preset-dropdown">
                <i data-icon="sliders" class="dropdown-leading-icon"></i>
                <select
                  id="chat-workflow-preset"
                  aria-label="Modo de trabajo"
                  onchange="applyChatWorkflowPreset(this.value)"
                  class="chat-header-select"
                  title="Modo de trabajo"
                >
                  <option value="">Modo libre (sin plantilla)</option>
                  <option value="analisis-archivos">Analista multimodal</option>
                  <option value="bugfix">Corrección de bugs</option>
                  <option value="cambio-controlado">Cambio controlado</option>
                  <option value="proyecto-nuevo">Diseño de proyectos</option>
                  <option value="revision">Revisión de código</option>
                </select>
                <i data-icon="chevron-down" class="dropdown-arrow-icon"></i>
              </div>
            </div>
            <details class="chat-storage-details">
              <summary>Almacenamiento y recuperación</summary>
              <p id="chat-storage-status" class="hint" role="status">Consultando uso del chat…</p>
              <div class="form-grid">
                <div class="field">
                  <label for="chat-storage-mb">Cuota total del chat (MB)</label>
                  <input id="chat-storage-mb" type="number" min="64" max="4096" value="512" />
                </div>
                <div class="field">
                  <label for="chat-retention-days">Archivar pendientes tras días</label>
                  <input id="chat-retention-days" type="number" min="1" max="365" value="30" />
                </div>
              </div>
              <div class="buttons">
                <button onclick="saveChatStorage()">Guardar límites</button>
                <button onclick="archiveOldChatUploads()">Archivar pendientes antiguos</button>
                <button onclick="loadChatStorage()">Actualizar</button>
              </div>
              <p class="hint">
                La retención archiva adjuntos que nunca se enviaron. No borra conversaciones ni archivos.
              </p>
              <div id="chat-archive-list"></div>
            </details>
            <div class="field" style="margin-bottom: 12px">
              <label for="chat-system-prompt">Instrucción de sistema (System Prompt)</label>
              <textarea
                id="chat-system-prompt"
                rows="3"
                placeholder="Indicá cómo querés que responda el modelo (idioma, rol, formato, reglas)…"
              ></textarea>
            </div>
            <div class="form-grid" style="margin-bottom: 12px">
              <div class="field" style="margin-bottom: 0">
                <label for="chat-temperature">Temperatura (0.0 a 1.5)</label>
                <input id="chat-temperature" type="number" step="0.05" min="0" max="1.5" value="0.2" />
              </div>
              <div class="field" style="margin-bottom: 0">
                <label for="chat-max-tokens">Máximo de tokens de respuesta</label>
                <input id="chat-max-tokens" type="number" step="256" min="256" max="32768" value="4096" />
              </div>
            </div>
            <div class="field">
              <label for="chat-reasoning-effort">Nivel de razonamiento</label>
              <select id="chat-reasoning-effort">
                <option value="">Predeterminado del modelo</option>
                <option value="none">Directo</option>
                <option value="low">Breve</option>
                <option value="medium">Medio</option>
                <option value="xhigh">Profundo</option>
              </select>
            </div>
            <div class="buttons">
              <button class="primary" onclick="saveChatSettings()">
                <i data-icon="check"></i>Guardar ajustes
              </button>
              <button class="quiet" onclick="toggleChatSettings()">Cerrar</button>
            </div>
          </div>
        </dialog>

        <div class="chat-scroll-area">
          <div class="chat-stream-column">
            <div id="chat-messages" class="chat-messages" role="log" aria-live="polite"></div>
            <p id="chat-context-status" class="hint" role="status"></p>
          </div>
        </div>

        <footer class="chat-composer-wrap">
          <div class="chat-composer-box">
            <div class="chat-hidden-inputs" hidden>
              <input
                id="chat-file-all"
                type="file"
                multiple
                onchange="
                  handleChatFiles(this.files);
                  this.value = '';
                "
              />
            </div>
            <div id="chat-connection-notice" class="chat-connection-notice" hidden>
              <p id="chat-connection-status" class="hint" role="status"></p>
              <button id="chat-view-accounts" type="button" class="quiet" onclick="navigate('cuentas')" hidden>Ver cuentas</button>
            </div>
            <p id="chat-upload-status" class="hint" role="status" hidden></p>
            <div id="chat-pending-files" class="chat-pending-files" hidden></div>
            <textarea
              aria-label="Mensaje para la IA"
              aria-describedby="chat-connection-status"
              id="chat-input"
              rows="1"
              placeholder="Escribí un mensaje…"
              onkeydown="handleChatKey(event)"
              oninput="editChatDraft(this)"
            ></textarea>
            <div class="chat-composer-bottom">
              <div class="chat-composer-tools">
                <button
                  type="button"
                  class="composer-tool-btn"
                  onclick="el('chat-file-all').click()"
                  aria-label="Adjuntar archivos"
                  title="Adjuntar archivos"
                >
                  <i data-icon="paperclip"></i>
                </button>
              </div>
              <div class="chat-composer-actions">
                <button
                  id="chat-cancel-btn"
                  type="button"
                  class="danger composer-btn-stop"
                  hidden
                  onclick="cancelChatGeneration()"
                  title="Detener generación"
                >
                  <i data-icon="stop"></i><span>Detener</span>
                </button>
                <button
                  id="chat-send-btn"
                  type="button"
                  class="primary composer-btn-send"
                  onclick="sendChatMessage()"
                  aria-label="Enviar mensaje"
                  title="Enviar mensaje"
                >
                  <i data-icon="send"></i>
                </button>
              </div>
            </div>
          </div>
          <div class="composer-disclaimer">El historial y los archivos quedan guardados en tu panel.</div>
        </footer>
      </div>
    </div>
  </section>
</template>
