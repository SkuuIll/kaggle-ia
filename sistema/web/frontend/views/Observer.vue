<script setup>
import { onMounted, onUnmounted, ref } from 'vue';

const statuses = {
  ready: 'Lista',
  loading: 'Preparando modelo',
  queued: 'En espera',
  off: 'Apagada',
  unknown: 'Sin confirmar',
};
const username = ref('');
const accounts = ref(null);
const error = ref('');
const formError = ref('');
const editing = ref(false);
const busy = ref(false);
const current = ref('');
const password = ref('');
const repeat = ref('');
let csrf;
let timer;

async function json(path, data) {
  const response = await fetch(path, data ? {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-IA-Token': csrf },
    body: JSON.stringify(data),
  } : undefined);
  if (response.status === 401) {
    location.replace('/login?expired=1');
    throw Error('Tu sesión terminó.');
  }
  const payload = await response.json();
  if (!response.ok) throw Error(payload.error || 'No se pudo completar la operación.');
  return payload;
}
async function refresh() {
  try {
    accounts.value = (await json('/api/overview')).accounts;
    error.value = '';
  } catch {
    error.value = 'No se pudo actualizar el estado de las GPU.';
    accounts.value = null;
  }
}
function reset() {
  current.value = password.value = repeat.value = formError.value = '';
  editing.value = false;
}
async function submit(change) {
  formError.value = '';
  if (change && password.value !== repeat.value) {
    formError.value = 'Las contraseñas nuevas no coinciden.';
    return;
  }
  busy.value = true;
  try {
    await json(change ? '/api/password' : '/api/logout', change ? { current: current.value, password: password.value } : {});
    reset();
    location.replace(change ? '/login?changed=1' : '/login');
  } catch (failure) {
    formError.value = failure.message;
  } finally {
    busy.value = false;
  }
}
onMounted(async () => {
  try {
    const session = await json('/api/session');
    username.value = session.username;
    csrf = session.csrf;
    await refresh();
    timer = setInterval(refresh, 30000);
  } catch {
    error.value = 'No se pudo cargar tu sesión. Recargá la página.';
  }
});
onUnmounted(() => clearInterval(timer));
</script>

<template>
  <main class="observer-shell">
    <header class="observer-header">
      <img :src="'/favicon.svg'" width="40" height="40" alt="" />
      <div><strong>Kaggle IA</strong><p class="hint">Acceso de invitado</p></div>
    </header>
    <section class="panel" aria-labelledby="observer-title">
      <h1 id="observer-title">Estado de las GPU</h1>
      <p class="hint">La vista se actualiza cada 30 segundos.</p>
      <p v-if="error" role="alert">{{ error }}</p>
      <p v-else-if="!accounts" role="status">Consultando…</p>
      <p v-else-if="!accounts.length">Todavía no hay GPU configuradas.</p>
      <ul v-else class="panel-user-list">
        <li v-for="account in accounts" :key="account.account" class="setting-row">
          <strong>Cuenta {{ account.account }}</strong>
          <span class="badge" :class="{ good: account.status === 'ready' }">{{ statuses[account.status] }}</span>
        </li>
      </ul>
    </section>
    <section v-if="username" class="panel" aria-labelledby="observer-session">
      <h2 id="observer-session">Tu sesión</h2>
      <p class="hint">{{ username }}</p>
      <div class="buttons">
        <button v-if="!editing" :disabled="busy" @click="editing = true">Cambiar contraseña</button>
        <button :disabled="busy" @click="submit(false)">Cerrar sesión</button>
      </div>
      <form v-if="editing" @submit.prevent="submit(true)">
        <div class="field">
          <label for="observer-current">Contraseña actual</label>
          <input id="observer-current" v-model="current" type="password" autocomplete="current-password" required maxlength="256" />
        </div>
        <div class="field">
          <label for="observer-new">Contraseña nueva</label>
          <input id="observer-new" v-model="password" type="password" autocomplete="new-password" required minlength="16" maxlength="256" />
        </div>
        <div class="field">
          <label for="observer-repeat">Repetir contraseña nueva</label>
          <input id="observer-repeat" v-model="repeat" type="password" autocomplete="new-password" required minlength="16" maxlength="256" />
        </div>
        <div class="buttons">
          <button type="submit" class="primary" :disabled="busy">Guardar contraseña</button>
          <button type="button" :disabled="busy" @click="reset">Cancelar</button>
        </div>
      </form>
      <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>
    </section>
  </main>
</template>
