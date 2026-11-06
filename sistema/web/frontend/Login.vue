<script setup>
import { ref } from 'vue';

const query = new URLSearchParams(window.location.search);
const username = ref('');
const password = ref('');
const visible = ref(false);
const capsLock = ref(false);
const pending = ref(false);
const error = ref('');
const notice = query.has('changed')
  ? 'Contraseña actualizada. Ingresá con tu nueva contraseña.'
  : query.has('expired')
    ? 'Tu sesión terminó. Volvé a ingresar para continuar.'
    : '';

async function signIn() {
  if (pending.value) return;
  error.value = '';
  pending.value = true;
  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value.trim(),
        password: password.value,
        next: query.get('next') || '/',
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'No se pudo iniciar sesión.');
    password.value = '';
    window.location.replace(result.redirect || '/');
  } catch (failure) {
    error.value =
      failure instanceof TypeError
        ? 'No se pudo conectar. Revisá tu conexión e intentá nuevamente.'
        : failure instanceof SyntaxError
          ? 'El panel devolvió una respuesta inesperada.'
          : failure.message;
  } finally {
    pending.value = false;
  }
}
</script>

<template>
  <main class="access-shell">
    <header class="access-brand">
      <span class="brand-symbol" aria-hidden="true">KI</span>
      <div><strong>Kaggle IA</strong><small>Consola de inferencia</small></div>
    </header>
    <section class="access-card" aria-labelledby="login-title">
      <p class="eyebrow">ACCESO PRIVADO</p>
      <h1 id="login-title">Entrá a tu espacio</h1>
      <p class="intro">Administrá tus sesiones de GPU, modelos y conversaciones.</p>
      <form @submit.prevent="signIn" :aria-busy="pending">
        <label for="username">Usuario</label>
        <input
          id="username"
          v-model="username"
          name="username"
          autocomplete="username"
          maxlength="128"
          required
          autocapitalize="none"
          spellcheck="false"
        />
        <label for="password">Contraseña</label>
        <div class="password-field">
          <input
            id="password"
            v-model="password"
            name="password"
            :type="visible ? 'text' : 'password'"
            autocomplete="current-password"
            maxlength="256"
            required
            @keyup="capsLock = $event.getModifierState('CapsLock')"
          />
          <button type="button" class="visibility" :aria-pressed="visible" @click="visible = !visible">
            {{ visible ? 'Ocultar' : 'Mostrar' }}
          </button>
        </div>
        <p v-if="capsLock" class="notice">Tenés Bloq Mayús activado.</p>
        <p v-if="notice" class="notice" role="status">{{ notice }}</p>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <button class="primary submit" type="submit" :disabled="pending">
          {{ pending ? 'Ingresando…' : 'Ingresar al panel' }}
        </button>
      </form>
      <details>
        <summary>¿Necesitás ayuda para entrar?</summary>
        <p>
          Usá las credenciales del panel. Si olvidaste tu contraseña, el administrador puede restablecerla
          desde la VPS.
        </p>
      </details>
    </section>
    <footer>Sesión privada · Hasta 8 horas</footer>
  </main>
</template>
