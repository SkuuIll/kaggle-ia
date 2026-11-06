<script setup>
const groups = [
  {
    label: 'Espacio de trabajo',
    items: [
      { page: 'dashboard', label: 'Inicio', icon: 'grid' },
      { page: 'chat', label: 'Chat IA', icon: 'chat', count: 'chat-count' },
    ],
  },
  {
    label: 'Operación',
    items: [
      { page: 'cuentas', label: 'Cuentas', icon: 'users', count: 'account-count' },
      { page: 'modelos', label: 'Modelos y TPS', icon: 'cpu' },
      { page: 'plantillas', label: 'Plantillas', icon: 'layers' },
      { page: 'actividad', label: 'Actividad', icon: 'activity' },
    ],
  },
  { label: 'Administración', items: [{ page: 'configuracion', label: 'Configuración', icon: 'settings' }] },
];
function open(page) {
  window.navigate(page);
}
</script>
<template>
  <aside id="primary-sidebar" class="sidebar">
    <div class="sidebar-mobile-head">
      <span class="sidebar-mobile-title">Navegación</span
      ><button class="sidebar-close-btn" onclick="closeMobileNav()" aria-label="Cerrar menú">
        <i data-icon="x"></i>
      </button>
    </div>
    <a href="#dashboard" class="brand"
      ><span class="mark" aria-hidden="true"><i data-icon="code"></i></span>
      <div><span>Kaggle IA</span><small class="brand-sub">Consola de inferencia</small></div></a
    >
    <nav class="nav" aria-label="Navegación principal">
      <template v-for="group in groups" :key="group.label">
        <div class="nav-label">{{ group.label }}</div>
        <button v-for="item in group.items" :key="item.page" :data-page="item.page" @click="open(item.page)">
          <i :data-icon="item.icon"></i>{{ item.label }}
          <span v-if="item.count" class="nav-count" :id="item.count">—</span>
        </button>
      </template>
    </nav>
    <div class="sidebar-foot">
      <button class="cmd-trigger" onclick="openPalette()" title="Atajo Ctrl+K">
        <i data-icon="search"></i><span>Acciones rápidas</span><kbd>Ctrl K</kbd>
      </button>
      <div class="server">
        <i class="dot" id="server-dot"></i><span id="server-status">Conectando al panel</span>
      </div>
      <small>Inferencia mediante relay SSH</small>
    </div>
  </aside>
</template>
