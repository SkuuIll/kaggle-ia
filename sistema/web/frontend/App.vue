<script setup>
import Overview from './views/Overview.vue';
import Chat from './views/Chat.vue';
import Accounts from './views/Accounts.vue';
import Models from './views/Models.vue';
import Templates from './views/Templates.vue';
import Activity from './views/Activity.vue';
import Settings from './views/Settings.vue';
import Sidebar from './components/Sidebar.vue';
import Dialogs from './components/Dialogs.vue';
</script>

<template>
  <div
    id="mobile-nav-backdrop"
    class="mobile-nav-backdrop"
    onclick="closeMobileNav()"
    aria-hidden="true"
  ></div>
  <Sidebar />
  <div class="layout">
    <header class="topbar">
      <button
        id="mobile-menu-btn"
        aria-controls="primary-sidebar"
        aria-expanded="false"
        class="icon-btn mobile-menu-btn"
        onclick="toggleMobileNav()"
        aria-label="Abrir menú"
        title="Abrir menú"
      >
        <i data-icon="menu"></i>
      </button>
      <div class="breadcrumb"><b id="breadcrumb">Inicio</b></div>
      <div class="top-actions">
        <span class="sync" id="last-sync">Consultando Kaggle…</span
        ><button
          class="icon-btn"
          onclick="refreshNow()"
          aria-label="Actualizar estado de Kaggle"
          title="Consultar estado ahora"
        >
          <i data-icon="refresh"></i>
        </button>
        <div class="user">
          <span class="avatar" id="avatar">IA</span
          ><span class="user-name"
            ><span id="session-user">Mi espacio</span><small>Administrador</small></span
          >
        </div>
        <button
          id="logout-button"
          class="icon-btn"
          hidden
          onclick="logout()"
          aria-label="Cerrar sesión"
          title="Cerrar sesión no apaga las GPU"
        >
          <i data-icon="logout"></i>
        </button>
      </div>
    </header>
    <main id="workspace">
      <div class="page-head">
        <div>
          <div class="eyebrow" id="page-eyebrow">RESUMEN DEL ESPACIO</div>
          <h1 id="page-title">Dashboard</h1>
          <p id="page-description" class="subtitle">Tus modelos, sesiones y consumo, de un vistazo.</p>
        </div>
        <div class="page-actions">
          <button class="operation" data-hide-on="chat" onclick="navigate('chat')">
            <i data-icon="chat"></i>Chatear con IA</button
          ><button class="danger operation" data-stop="true" onclick="stopAll()">
            <i data-icon="stop"></i>Apagar todas</button
          ><button class="primary operation" onclick="openAccount()">
            <i data-icon="plus"></i>Agregar cuenta
          </button>
        </div>
      </div>
      <div id="banner" class="banner" role="status">
        <i data-icon="shield"></i
        ><span id="banner-text">Consultando el estado real de las cuentas en Kaggle…</span>
      </div>

      <Overview />
      <Chat />
      <Accounts />
      <Models />
      <Templates />
      <Activity />
      <Settings />
    </main>
  </div>
  <aside id="floating-job" class="floating" aria-label="Seguimiento de operación" hidden>
    <span class="job-indicator" aria-hidden="true"></span>
    <div class="job-summary" role="status" aria-atomic="true">
      <strong id="floating-label">Operación en curso</strong>
      <span id="floating-detail"></span>
    </div>
    <button type="button" class="quiet" onclick="navigate('actividad')">Actividad <i data-icon="arrow"></i></button>
  </aside>
  <div id="toast" class="toast" role="status" hidden></div>
  <Dialogs />
  <nav class="mobile-bottom-nav" aria-label="Navegación móvil">
    <button data-page="dashboard" onclick="navigate('dashboard')" aria-current="page">
      <i data-icon="grid"></i><span>Inicio</span>
    </button>
    <button data-page="chat" onclick="navigate('chat')"><i data-icon="chat"></i><span>Chat IA</span></button>
    <button data-page="cuentas" onclick="navigate('cuentas')">
      <i data-icon="users"></i><span>Cuentas</span>
    </button>
    <button data-page="modelos" onclick="navigate('modelos')">
      <i data-icon="cpu"></i><span>Modelos</span>
    </button>
    <button type="button" onclick="toggleMobileNav()" aria-label="Abrir menú">
      <i data-icon="menu"></i><span>Menú</span>
    </button>
  </nav>
</template>
