<template>
  <dialog id="account-dialog" aria-labelledby="account-dialog-title">
    <h2 id="account-dialog-title">Agregar cuenta</h2>
    <p class="desc">Validamos la API y reconocemos el usuario sin encender una GPU.</p>
    <div class="segmented">
      <button id="mode-token" aria-selected="true" onclick="credentialMode('token')">Pegar API</button
      ><button id="mode-json" aria-selected="false" onclick="credentialMode('json')">
        Cargar kaggle.json
      </button>
    </div>
    <form id="account-form">
      <div class="field">
        <label for="account-name">Nombre para identificarla (opcional)</label
        ><input id="account-name" maxlength="48" placeholder="Por ejemplo, Código principal" />
      </div>
      <div id="credential-token">
        <div class="field">
          <label for="account-token">Token o API key</label
          ><input
            id="account-token"
            type="password"
            autocomplete="new-password"
            maxlength="2048"
            placeholder="KGAT_…"
          />
          <p class="hint">Con un KGAT_ detectamos el usuario automáticamente.</p>
        </div>
        <div class="field">
          <label for="account-username">Usuario (solo para una key legacy)</label
          ><input
            id="account-username"
            autocomplete="off"
            maxlength="64"
            placeholder="Tu usuario de Kaggle"
          />
        </div>
      </div>
      <div id="credential-json" class="file-zone" hidden>
        <p class="small muted">Seleccioná el archivo descargado desde Kaggle.</p>
        <input
          id="account-file"
          type="file"
          accept=".json"
          aria-label="Archivo kaggle.json"
          onchange="readAccountFile(this)"
        />
        <p id="credential-file-note" class="hint">La clave no se muestra en pantalla.</p>
      </div>
      <div id="account-error" class="error-text" role="alert"></div>
      <div class="buttons">
        <button type="button" class="quiet" onclick="closeDialog('account-dialog')">Cancelar</button
        ><button type="submit" class="primary operation">Validar y guardar</button>
      </div>
    </form>
  </dialog>
  <dialog id="rename-dialog" aria-labelledby="rename-title">
    <h2 id="rename-title">Nombre de la cuenta</h2>
    <p class="desc">Este nombre te ayuda a identificarla en el panel.</p>
    <form id="rename-form">
      <label for="rename-input">Nombre</label><input id="rename-input" maxlength="48" required />
      <div class="buttons">
        <button type="button" class="quiet" onclick="closeDialog('rename-dialog')">Cancelar</button
        ><button type="submit" class="primary operation">Guardar nombre</button>
      </div>
    </form>
  </dialog>
  <dialog id="confirm-dialog" aria-labelledby="confirm-title">
    <h2 id="confirm-title"></h2>
    <p id="confirm-description" class="desc"></p>
    <div class="buttons">
      <button id="confirm-cancel" autofocus>Cancelar</button
      ><button id="confirm-ok" class="primary">Confirmar</button>
    </div>
  </dialog>
  <dialog id="password-dialog" aria-labelledby="password-title">
    <h2 id="password-title">Cambiar contraseña</h2>
    <p class="desc">Se cierran todas las sesiones al guardar. Tus modelos siguen funcionando.</p>
    <form id="password-form">
      <div class="field">
        <label for="current-password">Contraseña actual</label
        ><input
          id="current-password"
          type="password"
          autocomplete="current-password"
          maxlength="256"
          required
        />
      </div>
      <div class="field">
        <label for="new-password">Nueva contraseña</label
        ><input
          id="new-password"
          type="password"
          autocomplete="new-password"
          minlength="16"
          maxlength="256"
          required
        />
        <p class="hint">Entre 16 y 256 caracteres. Podés usar una frase larga.</p>
      </div>
      <div class="field">
        <label for="repeat-password">Repetir nueva contraseña</label
        ><input
          id="repeat-password"
          type="password"
          autocomplete="new-password"
          minlength="16"
          maxlength="256"
          required
        />
      </div>
      <div id="password-error" class="error-text" role="alert"></div>
      <div class="buttons">
        <button type="button" class="quiet" onclick="closeDialog('password-dialog')">Cancelar</button
        ><button id="password-save" type="submit" class="primary">Guardar contraseña</button>
      </div>
    </form>
  </dialog>
  <dialog id="palette-dialog" class="palette-dialog" aria-labelledby="palette-title">
    <div class="palette-head">
      <h2 id="palette-title" class="sr-only">Acciones rápidas</h2>
      <input
        id="palette-search"
        placeholder="Escribí una acción, sección o modelo (ej. chatear, tps, encender, diagnosticar)…"
        oninput="renderPalette()"
      />
    </div>
    <div id="palette-list" class="palette-list"></div>
    <div class="palette-foot">
      <small>Hacé clic en cualquier acción para ejecutarla · Esc para cerrar</small
      ><button class="quiet" onclick="closeDialog('palette-dialog')">Cerrar</button>
    </div>
  </dialog>
  <dialog id="lightbox-dialog" class="lightbox-dialog" aria-labelledby="lightbox-caption">
    <div class="lightbox-top">
      <span id="lightbox-caption">Archivo adjunto</span>
      <div class="buttons">
        <a id="lightbox-original" target="_blank" rel="noopener noreferrer" hidden>Abrir PDF</a>
        <a id="lightbox-download" class="download" style="margin: 0" download>Descargar original</a>
        <button onclick="closeDialog('lightbox-dialog')">Cerrar</button>
      </div>
    </div>
    <div class="lightbox-body" id="lightbox-body" tabindex="0"></div>
  </dialog>
</template>
