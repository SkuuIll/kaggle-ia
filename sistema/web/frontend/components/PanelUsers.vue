<script setup>
import { ref } from 'vue';

const users = ref([]);
const username = ref('');
const password = ref('');
const repeat = ref('');
const busy = ref(false);
const error = ref('');
const notice = ref('');
const selected = ref('');

async function request(action, name, secret) {
  busy.value = true;
  error.value = '';
  notice.value = '';
  try {
    const response = action
      ? await fetch('/api/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-IA-Token': token },
          body: JSON.stringify({ action, username: name, password: secret }),
        })
      : await fetch('/api/users');
    if (response.status === 401) {
      location.replace('/login?expired=1');
      return;
    }
    const data = await response.json();
    if (!response.ok) throw Error(data.error);
    users.value = data.users;
    if (action === 'create') {
      username.value = password.value = repeat.value = '';
      notice.value = 'Usuario creado. Ya puede ingresar con su nombre y contraseña.';
    }
    if (action === 'remove') {
      selected.value = '';
      notice.value = 'Acceso revocado y sesiones cerradas.';
    }
  } catch (failure) {
    error.value = failure.message || 'No se pudo actualizar el acceso.';
  } finally {
    busy.value = false;
  }
}

function create() {
  if (password.value !== repeat.value) {
    error.value = 'Las contraseñas no coinciden.';
    return;
  }
  request('create', username.value, password.value);
}

function toggle(event) {
  if (event.target.open) request();
  else {
    password.value = repeat.value = '';
    selected.value = '';
  }
}
</script>

<template>
  <details class="panel-users" @toggle="toggle">
    <summary>Gestionar usuarios invitados</summary>
    <p class="hint">Los invitados pueden consultar el estado de las GPU y cambiar su propia contraseña. Sus accesos no incluyen chats, claves ni controles de encendido.</p>
    <ul v-if="users.length" class="panel-user-list" aria-label="Usuarios invitados">
      <li v-for="user in users" :key="user" class="setting-row">
        <strong>{{ user }}</strong>
        <button v-if="selected !== user" type="button" :disabled="busy" @click="selected = user">Revocar acceso</button>
        <div v-else class="buttons">
          <button type="button" :disabled="busy" @click="request('remove', user)">Confirmar revocación</button>
          <button type="button" :disabled="busy" @click="selected = ''">Cancelar</button>
        </div>
      </li>
    </ul>
    <form @submit.prevent="create">
      <h3>Crear usuario</h3>
      <div class="field">
        <label for="invite-username">Nombre de usuario</label>
        <input id="invite-username" v-model="username" autocomplete="off" autocapitalize="none" spellcheck="false" required pattern="[a-z0-9][a-z0-9_.\-]{2,31}" maxlength="32" aria-describedby="invite-format" />
        <p id="invite-format" class="hint">De 3 a 32 caracteres: minúsculas, números, puntos, guiones o guiones bajos.</p>
      </div>
      <div class="form-grid">
        <div class="field">
          <label for="invite-password">Contraseña inicial</label>
          <input id="invite-password" v-model="password" type="password" autocomplete="new-password" minlength="16" maxlength="256" required />
        </div>
        <div class="field">
          <label for="invite-repeat">Repetir contraseña</label>
          <input id="invite-repeat" v-model="repeat" type="password" autocomplete="new-password" minlength="16" maxlength="256" required />
        </div>
      </div>
      <button type="submit" class="primary" :disabled="busy">{{ busy ? 'Procesando…' : 'Crear usuario' }}</button>
    </form>
    <p v-if="error" class="form-error" role="alert">{{ error }}</p>
    <p v-if="notice" class="hint" role="status">{{ notice }}</p>
  </details>
</template>
