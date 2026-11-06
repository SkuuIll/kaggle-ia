<template>
  <section data-view="cuentas" hidden>
    <article class="panel">
      <div class="toolbar">
        <div>
          <h2>Cuentas conectadas</h2>
          <p class="hint">Administrá las credenciales, modelos y sesiones de tus cuentas.</p>
        </div>
        <label class="sr-only" for="account-search">Buscar cuenta</label
        ><input
          id="account-search"
          class="search"
          placeholder="Buscar por nombre o usuario…"
          oninput="renderAccounts()"
        />
      </div>
      <div class="table-wrap" tabindex="0" role="region" aria-label="Cuentas conectadas">
        <table>
          <thead>
            <tr>
              <th>Cuenta</th>
              <th>Estado</th>
              <th>Modelo</th>
              <th>Disponible</th>
              <th style="text-align: right">Acciones</th>
            </tr>
          </thead>
          <tbody id="account-rows"></tbody>
        </table>
      </div>
      <div id="accounts-empty" class="empty" hidden>
        <b>Tu espacio está listo para una cuenta.</b>Agregá un kaggle.json o un token KGAT_. Guardarlo no
        inicia una GPU.<br /><button
          class="primary operation"
          style="margin-top: 15px"
          onclick="openAccount()"
        >
          Agregar cuenta
        </button>
      </div>
    </article>
    <div class="notice">
      Quitar cuenta confirma primero la parada y archiva la credencial en privado para recuperación. La cuenta
      de Kaggle se conserva.
    </div>
    <article class="panel">
      <h2>Conectar una cuenta</h2>
      <p class="small muted">
        1. Agregá la API · 2. Elegí el modelo · 3. Encendé y esperá la confirmación.<br />Al terminar, usá
        Apagar y verificá el resultado en Actividad.
      </p>
      <a class="small" href="https://www.kaggle.com/settings" target="_blank" rel="noreferrer"
        >Abrir configuración de Kaggle <i data-icon="external"></i
      ></a>
    </article>
  </section>
</template>
