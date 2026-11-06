import { createApp } from 'vue';
import App from './App.vue';
import '../design-system.css';
import '../panel.css';
import './workspace.css';

const root = document.getElementById('app');

function loadController(url) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = url;
    script.onload = resolve;
    script.onerror = reject;
    document.head.append(script);
  });
}

try {
  createApp(App).mount(root);
  await loadController('/assets/chat/workspace.js');
  await loadController('/assets/dashboard.js');
} catch {
  const message = document.createElement('p');
  message.className = 'boot-status';
  message.setAttribute('role', 'alert');
  message.textContent = 'No se pudo cargar el panel. Recargá la página para reintentar.';
  root.replaceChildren(message);
}
