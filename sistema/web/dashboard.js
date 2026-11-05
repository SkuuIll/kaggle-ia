function setChatSidebar(open,restoreFocus=false){
  const sidebar=el('chat-sidebar'),toggle=el('chat-sidebar-toggle');
  sidebar.classList.toggle('open',open);
  el('chat-sidebar-backdrop').hidden=!open;
  toggle.setAttribute('aria-expanded',String(open));
  if(open)el('chat-search').focus();
  else if(restoreFocus||sidebar.contains(document.activeElement))toggle.focus();
}
function toggleChatSidebar(){
  setChatSidebar(!el('chat-sidebar').classList.contains('open'));
}
function toggleMobileNav(){
  const s=document.querySelector('.sidebar');
  const b=el('mobile-nav-backdrop');
  if(!s)return;
  const isOpen=s.classList.toggle('mobile-open');
  if(b)b.classList.toggle('open',isOpen);
}
function closeMobileNav(){
  const s=document.querySelector('.sidebar');
  const b=el('mobile-nav-backdrop');
  if(s)s.classList.remove('mobile-open');
  if(b)b.classList.remove('open');
}
/* Dashboard, T4 TPS Advisor & Multimodal Chat UI. All counters come from authenticated server data. */
const uiText=v=>String(v??'').replace(/[\p{Extended_Pictographic}\uFE0F]/gu,'').trim();
const el=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),fmt=n=>Number(n||0).toLocaleString('es-AR'),hours=s=>s==null?'—':(Number(s)/3600).toFixed(2)+' h';
/* Lucide Static 1.68.0 — https://lucide.dev — vendored SVG subset, no CDN.
ISC License

Copyright (c) 2026 Lucide Icons and Contributors

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

---

The following Lucide icons are derived from the Feather project:

airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out

The MIT License (MIT) (for the icons listed above)

Copyright (c) 2013-present Cole Bemis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

*/
const lucideGlyphs={"grid":"<rect width=\"7\" height=\"7\" x=\"3\" y=\"3\" rx=\"1\" />\n  <rect width=\"7\" height=\"7\" x=\"14\" y=\"3\" rx=\"1\" />\n  <rect width=\"7\" height=\"7\" x=\"14\" y=\"14\" rx=\"1\" />\n  <rect width=\"7\" height=\"7\" x=\"3\" y=\"14\" rx=\"1\" />","layers":"<path d=\"M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z\" />\n  <path d=\"M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12\" />\n  <path d=\"M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17\" />","chat":"<path d=\"M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z\" />","users":"<path d=\"M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2\" />\n  <path d=\"M16 3.128a4 4 0 0 1 0 7.744\" />\n  <path d=\"M22 21v-2a4 4 0 0 0-3-3.87\" />\n  <circle cx=\"9\" cy=\"7\" r=\"4\" />","cpu":"<path d=\"M12 20v2\" />\n  <path d=\"M12 2v2\" />\n  <path d=\"M17 20v2\" />\n  <path d=\"M17 2v2\" />\n  <path d=\"M2 12h2\" />\n  <path d=\"M2 17h2\" />\n  <path d=\"M2 7h2\" />\n  <path d=\"M20 12h2\" />\n  <path d=\"M20 17h2\" />\n  <path d=\"M20 7h2\" />\n  <path d=\"M7 20v2\" />\n  <path d=\"M7 2v2\" />\n  <rect x=\"4\" y=\"4\" width=\"16\" height=\"16\" rx=\"2\" />\n  <rect x=\"8\" y=\"8\" width=\"8\" height=\"8\" rx=\"1\" />","activity":"<path d=\"M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2\" />","settings":"<path d=\"M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915\" />\n  <circle cx=\"12\" cy=\"12\" r=\"3\" />","plus":"<path d=\"M5 12h14\" />\n  <path d=\"M12 5v14\" />","play":"<path d=\"M5 5a2 2 0 0 1 3.008-1.728l11.997 6.998a2 2 0 0 1 .003 3.458l-12 7A2 2 0 0 1 5 19z\" />","stop":"<rect width=\"18\" height=\"18\" x=\"3\" y=\"3\" rx=\"2\" />","clock":"<circle cx=\"12\" cy=\"12\" r=\"10\" />\n  <path d=\"M12 6v6l4 2\" />","refresh":"<path d=\"M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8\" />\n  <path d=\"M21 3v5h-5\" />\n  <path d=\"M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16\" />\n  <path d=\"M8 16H3v5\" />","trash":"<path d=\"M10 11v6\" />\n  <path d=\"M14 11v6\" />\n  <path d=\"M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6\" />\n  <path d=\"M3 6h18\" />\n  <path d=\"M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2\" />","edit":"<path d=\"M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z\" />\n  <path d=\"m15 5 4 4\" />","download":"<path d=\"M12 15V3\" />\n  <path d=\"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4\" />\n  <path d=\"m7 10 5 5 5-5\" />","upload":"<path d=\"M12 3v12\" />\n  <path d=\"m17 8-5-5-5 5\" />\n  <path d=\"M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4\" />","logout":"<path d=\"m16 17 5-5-5-5\" />\n  <path d=\"M21 12H9\" />\n  <path d=\"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4\" />","shield":"<path d=\"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z\" />\n  <path d=\"m9 12 2 2 4-4\" />","copy":"<rect width=\"14\" height=\"14\" x=\"8\" y=\"8\" rx=\"2\" ry=\"2\" />\n  <path d=\"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2\" />","check":"<path d=\"M20 6 9 17l-5-5\" />","x":"<path d=\"M18 6 6 18\" />\n  <path d=\"m6 6 12 12\" />","code":"<path d=\"m18 16 4-4-4-4\" />\n  <path d=\"m6 8-4 4 4 4\" />\n  <path d=\"m14.5 4-5 16\" />","search":"<path d=\"m21 21-4.34-4.34\" />\n  <circle cx=\"11\" cy=\"11\" r=\"8\" />","paperclip":"<path d=\"m16 6-8.414 8.586a2 2 0 0 0 2.829 2.829l8.414-8.586a4 4 0 1 0-5.657-5.657l-8.379 8.551a6 6 0 1 0 8.485 8.485l8.379-8.551\" />","image":"<rect width=\"18\" height=\"18\" x=\"3\" y=\"3\" rx=\"2\" ry=\"2\" />\n  <circle cx=\"9\" cy=\"9\" r=\"2\" />\n  <path d=\"m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21\" />","video":"<rect width=\"18\" height=\"18\" x=\"3\" y=\"3\" rx=\"2\" />\n  <path d=\"M7 3v18\" />\n  <path d=\"M3 7.5h4\" />\n  <path d=\"M3 12h18\" />\n  <path d=\"M3 16.5h4\" />\n  <path d=\"M17 3v18\" />\n  <path d=\"M17 7.5h4\" />\n  <path d=\"M17 16.5h4\" />","send":"<path d=\"M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z\" />\n  <path d=\"m21.854 2.147-10.94 10.939\" />","file":"<path d=\"M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z\" />\n  <path d=\"M14 2v5a1 1 0 0 0 1 1h5\" />\n  <path d=\"M10 9H8\" />\n  <path d=\"M16 13H8\" />\n  <path d=\"M16 17H8\" />","mic":"<path d=\"M12 19v3\" />\n  <path d=\"M19 10v2a7 7 0 0 1-14 0v-2\" />\n  <rect x=\"9\" y=\"2\" width=\"6\" height=\"13\" rx=\"3\" />","external":"<path d=\"M15 3h6v6\" />\n  <path d=\"M10 14 21 3\" />\n  <path d=\"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6\" />","arrow":"<path d=\"M5 12h14\" />\n  <path d=\"m12 5 7 7-7 7\" />","menu":"<line x1=\"4\" x2=\"20\" y1=\"12\" y2=\"12\" />\n  <line x1=\"4\" x2=\"20\" y1=\"6\" y2=\"6\" />\n  <line x1=\"4\" x2=\"20\" y1=\"18\" y2=\"18\" />","chevron-down":"<path d=\"m6 9 6 6 6-6\" />","chevron-left":"<path d=\"m15 18-6-6 6-6\" />","chevron-right":"<path d=\"m9 18 6-6-6-6\" />","sliders":"<line x1=\"4\" x2=\"4\" y1=\"21\" y2=\"14\" />\n  <line x1=\"4\" x2=\"4\" y1=\"10\" y2=\"3\" />\n  <line x1=\"12\" x2=\"12\" y1=\"21\" y2=\"12\" />\n  <line x1=\"12\" x2=\"12\" y1=\"8\" y2=\"3\" />\n  <line x1=\"20\" x2=\"20\" y1=\"21\" y2=\"16\" />\n  <line x1=\"20\" x2=\"20\" y1=\"12\" y2=\"3\" />\n  <line x1=\"1\" x2=\"7\" y1=\"14\" y2=\"14\" />\n  <line x1=\"9\" x2=\"15\" y1=\"8\" y2=\"8\" />\n  <line x1=\"17\" x2=\"23\" y1=\"16\" y2=\"16\" />","archive":"<rect width=\"20\" height=\"5\" x=\"2\" y=\"3\" rx=\"1\" />\n  <path d=\"M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8\" />\n  <path d=\"M10 12h4\" />","user":"<path d=\"M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2\" />\n  <circle cx=\"12\" cy=\"7\" r=\"4\" />"};
const icon=n=>`<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${lucideGlyphs[n]||lucideGlyphs.grid}</svg>`;
function renderIcons(container=document){
  container.querySelectorAll('[data-icon]').forEach(n=>{
    const svg=document.createElement('template');
    svg.innerHTML=icon(n.dataset.icon).trim();
    if(svg.content.firstElementChild) n.replaceWith(svg.content.firstElementChild);
  });
}
renderIcons();
const pages={
  dashboard:['Dashboard','RESUMEN DEL ESPACIO','Tus modelos, flujo de trabajo, sesiones y consumo, de un vistazo.'],
  chat:['Chat IA','ESTUDIO MULTIMODAL Y DOCUMENTOS','Conversá con tus modelos, medí TPS en vivo, enviá documentos, fotos o videos y descargá resultados.'],
  cuentas:['Cuentas','CONEXIONES DE KAGGLE','Agregá, identificá y administrá tus cuentas desde un solo lugar.'],
  modelos:['Modelos y TPS','OPTIMIZACIÓN PARA TESLA T4 ×2','Cambiá a arquitecturas MoE A3B o 1× GPU para alcanzar de 45 a 65 tokens por segundo.'],
  plantillas:['Plantillas','CATÁLOGO DE TU ESPACIO','Instalá modelos optimizados y prepará herramientas con configuraciones listas para usar.'],
  actividad:['Actividad','OPERACIONES Y MONITOREO','Seguí el progreso y consultá los resultados de tus operaciones.'],
  configuracion:['Configuración','PREFERENCIAS DEL ESPACIO','Protegé tus horas, conectá tus herramientas y guardá tus respaldos.']
};
const states={RUNNING:'Ejecutando en Kaggle',QUEUED:'En cola',COMPLETE:'Apagada',CANCEL_ACKNOWLEDGED:'Apagada',ERROR:'Finalizada con error',MISSING:'Sin notebook',NOT_CONFIGURED:'Sin API',UNKNOWN:'Sin confirmar',CHECKING:'Consultando'};
const actions={start:'Iniciar modelo',stop:'Apagar modelo',stop_all:'Apagar todas las IA',model:'Cambiar modelo',credentials:'Actualizar API',timers:'Configurar autoapagado',accounts:'Configurar conexiones',paseo:'Abrir Paseo',add_account:'Agregar cuenta',remove_account:'Quitar cuenta',rename_account:'Cambiar nombre',export_program:'Exportar código',export_private:'Respaldar conexión',restore:'Importar conexión',cache_launch:'Preparar pesos con CPU',cache_prepare:'Preparar caché CPU',cache_status:'Consultar caché CPU',cache_attach:'Verificar caché para el próximo arranque',cache_detach:'Desactivar caché',install_template:'Instalar plantilla de IA',tool_package:'Preparar herramienta privada',profile:'Cambiar perfil de rendimiento',extend:'Extender sesión 30 minutos',runtime_stop_inactividad:'Autoapagado por inactividad','runtime_stop_limite de sesion':'Autoapagado por límite de sesión',runtime_stop_solicitado:'Procesos finalizando por pedido',runtime_stop_error_runtime:'Error en el servidor GPU',client_config:'Preparar configuración de clientes'};
let latest=null,page='dashboard',accountKey=null,renameKey=null,credentialType='token',fileCredential=null,inspected=null,modelLoaded=null,timersLoaded=null,seenJob=null,toastTimer=null,refreshBusy=false;
const alerts=new Set();
const account=k=>latest?.accounts.find(a=>a.key===k),name=a=>a.nickname||a.username||'Cuenta '+a.account,active=a=>['RUNNING','QUEUED'].includes(a.state),unknown=a=>['UNKNOWN','CHECKING'].includes(a.state),busy=()=>latest?.job?.status==='running';
function html(id,value){const n=el(id);if(n&&n.innerHTML!==value&&!n.contains(document.activeElement))n.innerHTML=value;}
function badge(a){return `<span class="badge ${active(a)?'on':unknown(a)||a.state==='ERROR'?'bad':a.configured?'good':''}">${esc(states[a.state]||a.state)}</span>`;}
function toast(message,error=false){clearTimeout(toastTimer);el('toast').textContent=message;el('toast').className='toast'+(error?' error':'');el('toast').hidden=false;toastTimer=setTimeout(()=>el('toast').hidden=true,error?8000:4500);}
function navigate(value){
  if(!(value in pages))value='dashboard';
  closeMobileNav();
  if(value!=='chat')setChatSidebar(false);
  page=value;document.body.dataset.currentPage=value;
  document.querySelectorAll('[data-view]').forEach(n=>n.hidden=n.dataset.view!==value);
  document.querySelectorAll('[data-page]').forEach(n=>{if(n.dataset.page===value)n.setAttribute('aria-current','page');else n.removeAttribute('aria-current');});
  const [title,eyebrow,description]=pages[value];
  el('page-title').textContent=title;el('breadcrumb').textContent=title;el('page-eyebrow').textContent=eyebrow;el('page-description').textContent=description;
  document.title=title+' · Kaggle IA';
  if(location.hash!=='#'+value)history.replaceState(null,'','#'+value);
  if(latest){renderJob();renderQuickTpsModels();}
  if(value==='chat')loadChatConversations();
}
window.addEventListener('hashchange',()=>navigate(location.hash.slice(1)));
function setting(value){document.querySelectorAll('[data-setting]').forEach(n=>n.setAttribute('aria-selected',String(n.dataset.setting===value)));document.querySelectorAll('[data-setting-view]').forEach(n=>n.hidden=n.dataset.settingView!==value);}
async function post(path,data){const send=()=>fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-IA-Token':token},body:JSON.stringify(data)});let r=await send();if(r.status===403){const state=await fetch('/api/session',{cache:'no-store'});if(state.ok){const session=await state.json();if(session.csrf&&session.csrf!==token){token=session.csrf;r=await send();}}}if(r.status===401){location.replace('/login?expired=1');throw Error('Tu sesión terminó.');}const d=await r.json();if(!r.ok)throw Error(d.error||'No se pudo completar la operación.');return d;}
async function act(action,key=null,extra={},showActivity=false){try{await post('/api/action',{action,key,...extra});if(showActivity)navigate('actividad');await refresh();return true;}catch(e){toast(e.message,true);return false;}}
async function refresh(){if(refreshBusy)return;refreshBusy=true;try{const r=await fetch('/api/state',{cache:'no-store'});if(r.status===401){location.replace('/login?expired=1');return;}if(!r.ok)throw Error('No se pudo consultar el estado.');latest=await r.json();render();el('server-dot').className='dot';el('server-status').textContent=latest.server_mode==='vps'?'Panel en la VPS':'Panel local';}catch(e){el('server-dot').className='dot off';el('server-status').textContent='Conexión interrumpida';el('banner').className='banner error';el('banner-text').textContent='No se pudo actualizar el panel. El estado de Kaggle sigue sin confirmar; revisá tu conexión.';}finally{refreshBusy=false;}}
async function refreshNow(){try{await post('/api/refresh',{});toast('Solicitamos una nueva consulta a Kaggle.');await refresh();}catch(e){toast(e.message,true);}}
function select(id,accounts,all=false){const n=el(id);if(!n)return;const previous=n.value;const options=(all?'<option value="all">Todas las cuentas</option>':'')+accounts.map(a=>`<option value="${esc(a.key)}">${esc(name(a))} · ${esc(a.label.split(' ')[0]||'IA')}</option>`).join('');if(n.innerHTML!==options){n.innerHTML=options;if([...n.options].some(o=>o.value===previous))n.value=previous;}}

function modelTelemetry(a){
  const t=templateCatalog?.models?.find(m=>m.id===a.template_id||m.filename===a.filename);
  if(t)return {tps:'TPS sin medir',arch:t.arch||'MoE / GGUF'};
  if(a.filename.includes('A3B'))return {tps:'TPS sin medir',arch:'MoE A3B (3B activos)'};
  if(a.filename.includes('27B')||a.filename.includes('32B'))return {tps:'TPS sin medir',arch:'Denso 27B+'};
  return {tps:'TPS sin medir',arch:'GGUF T4'};
}

function renderWorkflowStepper(){
  if(!latest)return;
  const configured=latest.accounts.filter(a=>a.configured);
  const running=configured.filter(active);
  const primary=running[0]||configured[0];
  const tm=primary?modelTelemetry(primary):null;
  const step1=`<div class="wf-step ${configured.length?'ready':''}" onclick="navigate('cuentas')"><div class="wf-top"><span>Paso 1 · Cuentas</span><span class="wf-num">1</span></div><div class="wf-title">${configured.length?`${configured.length} cuenta${configured.length>1?'s':''} lista${configured.length>1?'s':''}`:'Agregar API Kaggle'}</div><div class="wf-sub">${configured.length?configured.map(name).join(' · '):'Conectá tu token KGAT_ o kaggle.json'}</div></div>`;
  const step2=`<div class="wf-step ${primary?'ready':''}" onclick="navigate('modelos')"><div class="wf-top"><span>Paso 2 · Modelo &amp; TPS</span><span class="wf-num">2</span></div><div class="wf-title">${primary?esc(uiText(primary.label.slice(0,26))):'Elegir modelo'}</div><div class="wf-sub">${primary?`${icon('activity')} ${esc(tm.tps)} · ${fmt(primary.context)} ctx`:'MoE A3B de alto TPS para Tesla T4'}</div></div>`;
  const step3=`<div class="wf-step ${running.length?'active':''}" onclick="${primary?(running.length?`navigate('actividad')`:`startAccount('${primary.key}')`):`navigate('cuentas')`}"><div class="wf-top"><span>Paso 3 · Sesión GPU</span><span class="wf-num">3</span></div><div class="wf-title">${running.length?`Activa: ${esc(name(running[0]))}`:'GPU apagada'}</div><div class="wf-sub">${running.length?'Clic para ver monitoreo en vivo':primary?'Clic para encender '+esc(name(primary)):'Configurá una cuenta primero'}</div></div>`;
  const step4=`<div class="wf-step ready" onclick="navigate('chat')"><div class="wf-top"><span>Paso 4 · Trabajar</span><span class="wf-num">4</span></div><div class="wf-title">Abrir Chat Multimodal</div><div class="wf-sub">Documentos, fotos, videos, código y TPS en vivo ${icon('arrow')}</div></div>`;
  html('workflow-stepper',step1+step2+step3+step4);
}

function render(){
  const configured=latest.accounts.filter(a=>a.configured);
  el('account-count').textContent=configured.length;
  const running=latest.accounts.filter(active),uncertain=configured.filter(unknown);
  el('banner').className='banner'+(running.length?' active':uncertain.length?' error':'');
  el('banner-text').textContent=running.length?`GPU activa o en cola: ${running.map(name).join(', ')}. Una GPU encendida consume horas aunque no estés escribiendo.`:uncertain.length?'No se confirmó el estado de todas las cuentas. Revisá Kaggle antes de dar una sesión por apagada.':configured.length?'No hay sesiones activas en las cuentas consultadas. Encendé un modelo cuando lo necesites.':'Conectá tu primera cuenta para empezar. Agregar una API no enciende la GPU.';
  const checked=configured.map(a=>a.checked_at).filter(Number.isFinite);
  el('last-sync').textContent=checked.length?'Kaggle · '+new Date(Math.min(...checked)*1000).toLocaleTimeString('es-AR',{hour:'2-digit',minute:'2-digit'}):'Consultando Kaggle…';
  select('dashboard-filter',configured,true);
  select('model-account',configured);
  select('timer-account',configured);
  select('client-account',configured);
  select('ops-account',configured);
  select('template-account',configured);
  select('chat-account',configured);
  if(!clientDefaultSet&&configured.length){el('client-account').value=(configured.find(active)||configured[0]).key;clientDefaultSet=true;}
  if(clientConfig&&clientConfig.profile_key!==el('client-account').value)clearClientConfig();
  renderWorkflowStepper();
  loadModel();loadTimers();renderDashboard();renderAccounts();renderHistory();renderJob();renderConnection();renderChatHeaderStatus();
  el('installation-mode').textContent=latest.server_mode==='vps'?'Servidor en la VPS. Los clientes usan HTTPS; Kaggle se conecta al relay por SSH.':'Controlador local en esta PC.';
  el('open-paseo').hidden=latest.server_mode==='vps';
  document.querySelectorAll('.operation').forEach(b=>b.disabled=(busy()&&!b.dataset.stop)||b.dataset.unavailable==='true');
  for(const a of configured){
    if(active(a))notify('active-'+a.key+'-'+Math.floor(Date.now()/900000),'GPU activa',name(a)+' sigue activa o en cola en Kaggle.');
    const q=a.quota;
    if(q?.allowed_seconds&&q.available_seconds!=null&&q.available_seconds<q.allowed_seconds*.1)notify('quota-'+a.key+'-'+q.refresh,'Poca cuota disponible','Queda menos del 10% de la cuota de '+name(a)+'.');
  }
}

function renderDashboard(){
  if(!latest)return;
  const key=el('dashboard-filter').value,accounts=latest.accounts.filter(a=>a.configured&&(key==='all'||a.key===key));
  el('kpi-active').textContent=accounts.filter(active).length;
  const uncertain=accounts.filter(unknown).length,queued=accounts.filter(a=>a.state==='QUEUED').length;
  el('kpi-active-note').textContent=uncertain?`${uncertain} sin confirmar`:queued?`${queued} en cola de Kaggle`:'Estado oficial de Kaggle';
  const quotas=accounts.map(a=>a.quota?.available_seconds);
  el('kpi-hours').textContent=quotas.length&&quotas.every(v=>v!=null)?hours(quotas.reduce((n,v)=>n+v,0)):'—';
  el('kpi-hours-note').textContent=accounts.length>1?'Suma de cuotas · una GPU a la vez':'Cuota oficial de la cuenta';
  el('kpi-tokens').textContent=fmt(accounts.reduce((n,a)=>n+a.usage.input_tokens+a.usage.output_tokens,0));
  el('kpi-requests').textContent=fmt(accounts.reduce((n,a)=>n+a.usage.requests,0));
  const errors=accounts.reduce((n,a)=>n+(a.usage.failed_requests||0),0);
  el('kpi-requests-note').textContent=errors?`${fmt(errors)} con error · historial registrado`:'A través de la conexión medida';
  renderChart(accounts);
  const poolReady=latest.accounts.some(a=>a.state==='RUNNING'&&a.live?.capabilities?.includes('session-v1'));
  el('pool-active-info').textContent=poolReady?'Hay un relay conectado.':'Iniciá una cuenta para usar el pool.';
  el('pool-status-pill').textContent=poolReady?'Relay detectado':'Sin relay detectado';
  el('pool-status-pill').className=poolReady?'badge good':'badge';
  el('individual-accounts-count').textContent=latest.accounts.filter(a=>a.configured).length+' configuradas';
  html('quota-list',accounts.length?accounts.map(a=>{const q=a.quota,p=q?.allowed_seconds?100*((q.used_seconds||0)+(q.reserved_seconds||0))/q.allowed_seconds:0;return `<div class="quota"><div class="quota-head"><b>${esc(name(a))}</b><small>${hours(q?.used_seconds)} / ${hours(q?.allowed_seconds)}</small></div><div class="bar" role="img" aria-label="${esc(name(a))}: ${p.toFixed(1)} por ciento utilizado o reservado"><i class="${p>=80?'warn':''}" style="width:${Math.max(0,Math.min(100,p))}%"></i></div><div class="quota-foot"><span>${q?'Renueva '+(q.refresh?new Date(q.refresh).toLocaleDateString('es-AR'):'sin fecha'):'Cuota sin confirmar'}</span><strong>${hours(q?.available_seconds)} libres</strong></div>${q?.reserved_seconds?`<p class="hint">${hours(q.reserved_seconds)} reservadas</p>`:''}</div>`;}).join(''):'<div class="empty">Agregá una cuenta para consultar su cuota.</div>');
  html('model-cards',accounts.length?accounts.map(a=>{
    const tm=modelTelemetry(a);
    return `<article class="model-card"><div class="card-head"><div><div class="account-name">${esc(name(a))}</div><div class="account-caption">Conexión ${a.account}${a.username?' · @'+esc(a.username):''}</div></div>${badge(a)}</div><div class="model-label">${esc(uiText(a.label))}</div><div class="chips"><span class="chip tps">${icon('activity')} ${esc(tm.tps)}</span><span class="chip">${esc(uiText(tm.arch))}</span><span class="chip">${fmt(a.context)} ctx</span><span class="chip">${esc(a.filename.match(/Q[0-9][A-Z0-9_]*/i)?.[0]||'GGUF')}</span><span class="chip">${hours(a.quota?.available_seconds)} libres</span></div><div class="card-quick-actions"><button onclick="openChatForAccount('${a.key}')">${icon('chat')}Chatear</button><button onclick="openModelsForAccount('${a.key}')">${icon('cpu')}Cambiar / TPS</button><button onclick="quickDiagnose('${a.key}')">${icon('shield')}Diagnosticar</button><button onclick="openClientSetupForAccount('${a.key}')">${icon('code')}Clientes IDE</button></div><div class="card-foot"><small>${a.live&&!a.live.error?'Canal de control disponible':'FlashAttention + KV Q8_0'}</small><div class="buttons"><button class="operation" data-stop="true" onclick="stopAccount('${a.key}')">${icon('stop')}Apagar</button><button class="primary operation" data-unavailable="${active(a)}" onclick="startAccount('${a.key}')" ${active(a)?'disabled':''}>${icon('play')}Encender</button></div></div></article>`;
  }).join(''):'<article class="panel empty"><b>Tu próximo modelo empieza acá.</b>Conectá una API de Kaggle para preparar tu espacio.<br><button class="primary operation" style="margin-top:15px" onclick="openAccount()">Agregar cuenta</button></article>');
}

function openChatForAccount(key){
  if(key&&el('chat-account'))el('chat-account').value=key;
  navigate('chat');
  if(activeChatId&&chatState.conversation&&chatState.conversation.account!==key){
    changeChatAccount(key);
  }
}
function openModelsForAccount(key){
  navigate('modelos');
  if(key&&el('model-account')){el('model-account').value=key;loadModel(true);}
}
function openClientSetupForAccount(key){
  navigate('configuracion');
  setting('connection');
  if(key&&el('client-account')){el('client-account').value=key;clearClientConfig();}
  if(key&&el('ops-account')){el('ops-account').value=key;renderOperationControls();}
}
async function quickDiagnose(key){
  toast('Comprobando estado en Kaggle, API HTTPS y memoria…');
  try{
    const d=await post('/api/diagnose',{key});
    toast(`${name(account(key))}: ${d.message} (Kaggle: ${d.state}, API: ${d.api_status||'sin conexión'}, en RAM: ${d.model_loaded?'sí':'no'})`);
  }catch(e){toast(e.message,true);}
}

function renderChart(accounts){const days=Array.from({length:7},(_,i)=>{const d=new Date();d.setUTCDate(d.getUTCDate()-6+i);return {day:d.toISOString().slice(0,10),input:0,output:0,requests:0};});for(const a of accounts)for(const row of a.daily||[]){const d=days.find(d=>d.day===row.day);if(d){d.input+=row.input_tokens;d.output+=row.output_tokens;d.requests+=row.requests;}}const max=Math.max(1,...days.map(d=>d.input+d.output)),left=43,plot=590,base=198,height=158;let svg='<svg viewBox="0 0 660 235" role="img" aria-labelledby="chart-title"><title id="chart-title">Tokens de entrada y salida medidos en los últimos siete días</title>';for(let i=0;i<=4;i++){const y=base-i*height/4;svg+=`<line x1="${left}" x2="633" y1="${y}" y2="${y}" stroke="rgba(255,255,255,0.06)"/><text x="34" y="${y+3}" text-anchor="end" fill="#8b95a7" font-size="9">${Math.round(max*i/4).toLocaleString('es-AR')}</text>`;}days.forEach((d,i)=>{const x=left+i*plot/7+plot/14-14,hIn=d.input/max*height,hOut=d.output/max*height;svg+=`<g><title>${d.day}: ${fmt(d.input)} entrada, ${fmt(d.output)} salida; ${fmt(d.requests)} solicitudes</title><rect x="${x}" y="${base-hIn}" width="28" height="${hIn}" rx="3" fill="#60a5fa"/><rect x="${x}" y="${base-hIn-hOut}" width="28" height="${hOut}" rx="3" fill="#334155"/></g><text x="${x+14}" y="220" text-anchor="middle" fill="#8b95a7" font-size="9">${d.day.slice(8)}/${d.day.slice(5,7)}</text>`;});html('usage-chart',svg+'</svg>');const requests=days.reduce((n,d)=>n+d.requests,0);el('chart-note').textContent=requests?`${fmt(requests)} solicitudes en el período. Los días vacíos muestran cero solicitudes registradas.`:'Todavía no hay solicitudes medidas en este período. El gráfico se completa con uso real.';}
function renderAccounts(){if(!latest)return;const search=el('account-search').value.toLowerCase(),configured=latest.accounts.filter(a=>a.configured),accounts=configured.filter(a=>(name(a)+' '+a.username+' '+a.label).toLowerCase().includes(search));el('accounts-empty').hidden=configured.length>0;html('account-rows',accounts.map(a=>{const tm=modelTelemetry(a);return `<tr><td><b>${esc(name(a))}</b><small>@${esc(a.username||'sin usuario')} · Conexión ${a.account}</small></td><td>${badge(a)}</td><td><div class="table-model" title="${esc(uiText(a.label))}">${esc(uiText(a.label))}</div><small>${icon('activity')} ${esc(tm.tps)} · ${fmt(a.context)} tokens ctx</small></td><td><b>${hours(a.quota?.available_seconds)}</b><small>${a.quota?'Cuota de Kaggle':'Sin confirmar'}</small></td><td><div class="row-actions"><button class="icon-btn" title="Chatear con esta cuenta" onclick="openChatForAccount('${a.key}')">${icon('chat')}</button><button class="icon-btn operation" data-unavailable="${active(a)}" aria-label="Encender ${esc(name(a))}" title="Encender" onclick="startAccount('${a.key}')" ${active(a)?'disabled':''}>${icon('play')}</button><button class="icon-btn operation" data-stop="true" aria-label="Apagar ${esc(name(a))}" title="Apagar" onclick="stopAccount('${a.key}')">${icon('stop')}</button><button class="icon-btn operation" aria-label="Actualizar API de ${esc(name(a))}" title="Actualizar API" onclick="openAccount('${a.key}')">${icon('shield')}</button><button class="icon-btn operation" aria-label="Renombrar ${esc(name(a))}" title="Cambiar nombre" onclick="renameAccount('${a.key}')">${icon('edit')}</button><button class="icon-btn danger operation" aria-label="Quitar ${esc(name(a))}" title="Quitar cuenta" onclick="removeAccount('${a.key}')">${icon('trash')}</button></div></td></tr>`;}).join('')||(configured.length?'<tr><td colspan="5" class="empty">No hay cuentas que coincidan con la búsqueda.</td></tr>':''));}
function eventRows(events){return events.length?events.map(e=>`<div class="event"><span class="event-icon ${e.status==='error'?'bad':''}">${icon(e.status==='error'?'x':'check')}</span><div class="event-main">${esc(actions[e.action]||'Operación del panel')}<small>${e.profile?'Conexión '+(account(e.profile)?.account||'')+' · ':''}${e.status==='done'?'Completada':'No se completó; revisá el resultado'}${e.detail?' · '+esc(e.detail):''}</small></div><time datetime="${new Date(e.timestamp*1000).toISOString()}">${new Date(e.timestamp*1000).toLocaleString('es-AR',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'})}</time></div>`).join(''):'<div class="empty"><b>Todavía no hay operaciones registradas.</b>Los inicios, apagados y cambios aparecerán acá.</div>';}
function renderHistory(){if(!latest)return;const filter=el('history-filter').value,events=latest.history||[];html('recent-events',eventRows(events.slice(0,4)));const filtered=events.filter(e=>filter==='all'||e.status===filter);html('operation-history',filtered.length||filter==='all'?eventRows(filtered):'<div class="empty"><b>No hay operaciones con este resultado.</b>Podés cambiar el filtro para ver las demás.</div>');}
function renderJob(){if(!latest)return;const j=latest.job,running=j.status==='running';el('jobtitle').textContent=running?(actions[j.action]||'Operación')+' en curso':j.status==='done'?'Operación completada':j.status==='error'?'No se completó la operación':'Sin operaciones en curso';el('job-pulse').hidden=!running;el('job-note').textContent=running?'La cola no tiene un tiempo predecible. El inicio y la parada se confirman con Kaggle.':j.status==='error'?'La operación no terminó correctamente. No se anuncia inicio o parada confirmados.':'El inicio y el apagado se confirman contra Kaggle.';const node=el('progress'),text=j.lines?.length?j.lines.join('\n'):'Todavía no hay una operación en esta sesión del servidor.';if(node.textContent!==text){const bottom=node.scrollHeight-node.scrollTop-node.clientHeight<30;node.textContent=text;if(bottom)node.scrollTop=node.scrollHeight;}el('job-duration').textContent=j.started_at?`${Math.max(0,Math.floor(((j.finished_at||Date.now()/1000)-j.started_at)/60))} min transcurridos`:'';el('floating-job').hidden=!running||page==='actividad';el('floating-label').textContent=(actions[j.action]||'Operación')+' en curso';const download=j.download&&j.status==='done'?`<a class="download" href="/api/download/${encodeURIComponent(j.download.id)}">${icon('download')}Descargar ${esc(j.download.filename)}</a>${j.download.private?'<p class="hint">Respaldo privado: contiene claves. No lo publiques.</p>':''}`:'';html('job-download',download);if(download)html('backup-download',download);if(seenJob?.status==='running'&&['done','error'].includes(j.status))toast(j.status==='done'?'Operación completada. Revisá el resultado en Actividad.':'No se completó la operación. Revisá Actividad.',j.status==='error');seenJob={id:j.id,status:j.status};}

function renderQuickTpsModels(){
  const box=el('quick-tps-models');
  if(!box||!templateCatalog||!latest)return;
  const key=el('model-account')?.value;
  const a=account(key);
  const fastModels=templateCatalog.models;
  const fmtCtx=n=>n>=1000000?'1M':Math.round(n/1024)+'k';
  html('quick-tps-models',fastModels.map(t=>{
    const isCurrent=a&&(a.template_id===t.id||a.filename===t.filename);
    return `<div class="tps-card ${isCurrent?'current':''}"><div class="tps-card-top"><b>${esc(uiText(t.name))}</b><span class="chip tps">${icon('activity')} ${esc('Sin medición GPU')}</span></div><div class="tps-card-meta">${esc(t.arch||'MoE / GGUF')} · ${(t.size_bytes/1e9).toFixed(1)} GB · ${fmtCtx(t.context)} activo (${fmtCtx(t.native_context||t.context)} nativo)</div><div class="tps-card-meta">${esc(t.vram_fit||'Tesla T4 ×2')}</div><div class="buttons"><button type="button" class="${isCurrent?'':'primary'} operation" ${busy()||isCurrent?'disabled':''} onclick="installTemplateForAccount('${esc(key)}','${esc(t.id)}')">${isCurrent?'Configurado en esta cuenta':'Cambiar a este modelo'}</button></div></div>`;
  }).join(''));
}

function loadModel(force=false){
  const a=account(el('model-account').value);
  el('model-form').hidden=!a;
  if(!a){el('model-current').textContent='Agregá una cuenta para configurar su modelo.';return;}
  const tm=modelTelemetry(a);
  el('model-current').innerHTML=`<strong>Activo en ${esc(name(a))}:</strong> ${esc(uiText(a.label))} · <strong>${icon('activity')} ${esc(tm.tps)}</strong> (${esc(uiText(tm.arch))})`;
  renderQuickTpsModels();
  const signature=a.key+'|'+a.repo+'|'+a.context;
  if(!force&&modelLoaded===signature)return;
  if(!force&&modelLoaded&&el('model-form').contains(document.activeElement))return;
  modelLoaded=signature;
  el('model-repo').value=a.repo;
  el('model-file').innerHTML=`<option value="${esc(a.filename)}">${esc(a.filename)}</option>`;
  el('model-context').value=a.context;
  el('inspect-result').textContent='';
  inspected=null;
}
function loadTimers(force=false){const a=account(el('timer-account').value);el('timer-form').hidden=!a;if(!a)return;const signature=a.key+'|'+a.idle_minutes+'|'+a.max_session_minutes;if(!force&&timersLoaded===signature)return;if(!force&&timersLoaded&&el('timer-form').contains(document.activeElement))return;timersLoaded=signature;el('timer-idle').value=a.idle_minutes;el('timer-maximum').value=a.max_session_minutes;}
function renderConnection(){html('connection-list',latest.accounts.filter(a=>a.configured).map(a=>`<div class="setting-row"><div><h3>${esc(name(a))}</h3><code class="code">${esc(a.client_url)}</code></div><button onclick="copyEndpoint('${a.key}')">${icon('copy')}Copiar</button></div>`).join('')||'<p class="small muted">Agregá una cuenta para ver sus conexiones.</p>');}
async function copyEndpoint(key){try{await navigator.clipboard.writeText(account(key).client_url);toast('Dirección copiada.');}catch(e){toast('No se pudo copiar. Podés seleccionar la dirección manualmente.',true);}}
function closeDialog(id){el(id).close();}
function ask(title,description,label='Confirmar',danger=false){return new Promise(resolve=>{const d=el('confirm-dialog');el('confirm-title').textContent=title;el('confirm-description').textContent=description;el('confirm-ok').textContent=label;el('confirm-ok').className=danger?'danger':'primary';let answer=false;el('confirm-cancel').onclick=()=>d.close();el('confirm-ok').onclick=()=>{answer=true;d.close();};d.onclose=()=>resolve(answer);d.showModal();});}
async function startAccount(key,showActivity=true){const a=account(key),other=latest?.accounts.find(b=>b.key!==key&&active(b));if(!a?.configured||active(a)||busy())return;if(other&&!await ask('Cambiar de cuenta',`Primero se apagará ${name(other)}. Después se iniciará ${name(a)}. La GPU consume horas mientras está encendida.`,'Apagar anterior y encender'))return;await act('start',key,{switch:Boolean(other),open_paseo:latest.server_mode!=='vps'},showActivity);}
async function stopAccount(key){const a=account(key);if(a&&await ask('Apagar '+name(a),'Se solicitará la parada y esperaremos la confirmación de Kaggle. Las solicitudes en curso pueden interrumpirse.','Apagar modelo',true))await act('stop',key,{},true);}
async function stopAll(){if(await ask('Apagar todas las IA','Se solicitará y comprobará la parada de los modelos configurados en este panel.','Apagar todas',true))await act('stop_all',null,{},true);}
function openAccount(key=null){if(!latest)return;accountKey=key;const a=account(key);el('account-form').reset();fileCredential=null;el('account-name').value=a?.nickname||'';el('account-username').value=a?.username||'';el('account-dialog-title').textContent=a?'Actualizar API':'Agregar cuenta';el('account-dialog').querySelector('.desc').textContent=!a&&latest.accounts.filter(b=>b.configured).length===2?'Ya usás las dos conexiones. Una API existente se actualizará; para agregar otro usuario, quitá una cuenta desde Cuentas.':'Validamos la API y reconocemos el usuario sin encender una GPU.';el('account-error').textContent='';el('credential-file-note').textContent='La clave no se muestra en pantalla.';credentialMode('token');el('account-dialog').showModal();}
function credentialMode(mode){credentialType=mode;el('mode-token').setAttribute('aria-selected',String(mode==='token'));el('mode-json').setAttribute('aria-selected',String(mode==='json'));el('credential-token').hidden=mode!=='token';el('credential-json').hidden=mode!=='json';el('account-token').required=mode==='token';}
async function readAccountFile(input){try{if(!input.files[0])return;if(input.files[0].size>65536)throw Error('El archivo es demasiado grande para un kaggle.json.');const d=JSON.parse(await input.files[0].text());if(!(d.key||d.api_token))throw Error('No se encontró key o api_token en el JSON.');fileCredential={username:d.username||'',key_value:d.key||d.api_token};el('credential-file-note').textContent='Archivo listo para validar. La clave no se muestra.';el('account-error').textContent='';}catch(e){fileCredential=null;el('account-error').textContent='No se pudo leer el kaggle.json. Revisá que incluya username y key, o api_token.';}}
el('account-form').onsubmit=async e=>{e.preventDefault();el('account-error').textContent='';const data=credentialType==='json'?fileCredential:{username:el('account-username').value.trim(),key_value:el('account-token').value.trim()};if(!data?.key_value){el('account-error').textContent='Cargá el JSON o pegá una API válida.';return;}if(await act(accountKey?'credentials':'add_account',accountKey,{...data,name:el('account-name').value.trim()},true)){e.target.reset();fileCredential=null;el('account-dialog').close();}};
el('account-dialog').addEventListener('close',()=>{fileCredential=null;el('account-token').value='';el('account-file').value='';});
function renameAccount(key){renameKey=key;el('rename-input').value=name(account(key));el('rename-dialog').showModal();}
el('rename-form').onsubmit=async e=>{e.preventDefault();if(await act('rename_account',renameKey,{name:el('rename-input').value.trim()}))el('rename-dialog').close();};
async function removeAccount(key){const a=account(key);if(await ask('Quitar '+name(a),'Primero se comprobará su apagado. Si está activa, se intentará detenerla.\nLa credencial se archivará en privado para recuperación y se liberará la conexión. La cuenta de Kaggle se conserva.','Apagar y quitar cuenta',true))await act('remove_account',key,{stop:true},true);}
async function inspectModel(){const button=el('inspect-button');button.disabled=true;el('inspect-result').textContent='Consultando Hugging Face…';try{const info=await post('/api/model/inspect',{repo:el('model-repo').value});inspected=info;el('model-repo').value=info.repo;el('model-file').innerHTML=info.files.map(f=>`<option value="${esc(f)}">${esc(f)}</option>`).join('');el('inspect-result').textContent=`${info.files.length} archivos disponibles.${info.native_context?' Contexto nativo informado: '+fmt(info.native_context)+'.':''} Elegí un GGUF.`;}catch(e){el('inspect-result').textContent=e.message;}finally{button.disabled=false;}}
el('model-form').onsubmit=async e=>{e.preventDefault();const key=el('model-account').value,a=account(key),other=latest.accounts.find(b=>b.key!==key&&active(b));if(!a)return;if(el('model-repo').value.trim()!==a.repo&&inspected?.repo!==el('model-repo').value.trim()){toast('Buscá los archivos del repositorio antes de aplicar el modelo.',true);return;}if(await ask('Aplicar modelo y arrancar',`Se detendrá el modelo de ${name(a)}${other?' y también la sesión de '+name(other):''}. Después se descargará el archivo elegido en Kaggle. El inicio consume horas de GPU.`,'Aplicar e iniciar'))await act('model',key,{repo:el('model-repo').value,filename:el('model-file').value,context:Number(el('model-context').value),start:true,switch:Boolean(other)},true);};
el('timer-form').onsubmit=async e=>{e.preventDefault();if(await act('timers',el('timer-account').value,{idle:Number(el('timer-idle').value),maximum:Number(el('timer-maximum').value)}))toast('Cambio enviado. Se aplicará al próximo arranque.');};
async function privateBackup(){if(await ask('Respaldar conexión privada','El ZIP contiene tus APIs y la clave SSH y no está cifrado. Guardalo en privado y no lo publiques.','Crear respaldo privado'))await act('export_private');}
async function restorePrivate(input){try{const file=input.files[0];if(!file)return;if(file.size>16*1024*1024)throw Error('El ZIP es demasiado grande.');if(!await ask('Importar conexión','Se reemplazará la conexión. Todas las cuentas actuales deben tener su apagado confirmado.','Importar conexión'))return;const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(const v of bytes)binary+=String.fromCharCode(v);await act('restore',null,{zip:btoa(binary)},true);}catch(e){toast(e.message,true);}finally{input.value='';}}
function notify(id,title,body){if(!('Notification'in window)||Notification.permission!=='granted'||alerts.has(id))return;alerts.add(id);new Notification(title,{body});}
async function enableNotifications(){if(!('Notification'in window)){toast('Este navegador no admite avisos. El indicador de GPU sigue disponible.',true);return;}const p=await Notification.requestPermission();el('notify').textContent=p==='granted'?'Avisos activados':'Avisos no permitidos';if(p==='granted'){alerts.clear();await refresh();}}
function openPassword(){el('password-form').reset();el('password-error').textContent='';el('password-dialog').showModal();}
el('password-form').onsubmit=async e=>{e.preventDefault();const error=el('password-error'),button=el('password-save');error.textContent='';if(el('new-password').value!==el('repeat-password').value){error.textContent='Las contraseñas nuevas no coinciden.';return;}button.disabled=true;try{await post('/api/password',{current:el('current-password').value,password:el('new-password').value});e.target.reset();location.replace('/login?changed=1');}catch(e){error.textContent=e.message;}finally{button.disabled=false;}};
async function logout(){try{await post('/api/logout',{});location.replace('/login');}catch(e){toast(e.message,true);}}

let clientConfig=null,clientKeyShown=false,clientDefaultSet=false;
function clearClientConfig(){clientConfig=null;clientKeyShown=false;el('client-config-area').hidden=true;el('client-api-key').value='';el('client-snippet').textContent='';el('client-probe-result').textContent='';}
async function prepareClientConfig(){const button=el('client-prepare');button.disabled=true;try{clientConfig=await post('/api/client-config',{key:el('client-account').value});if(clientConfig.profile_key!==el('client-account').value){clearClientConfig();return;}clientKeyShown=false;el('client-api-key').type='password';el('client-api-key').value=clientConfig.api_key;el('client-show-key').textContent='Mostrar clave';el('client-config-area').hidden=false;el('client-package').href='/api/download/'+encodeURIComponent(clientConfig.download.id);renderClientSnippet();}catch(e){toast(e.message,true);}finally{button.disabled=false;}}
function renderClientSnippet(){if(!clientConfig)return;const type=el('snippet-client').value,raw=clientConfig.configs[type];el('client-snippet').textContent=clientKeyShown?raw:raw.split(clientConfig.api_key).join('CLAVE_OCULTA_USA_EL_BOTON_COPIAR');el('client-snippet-help').textContent=type==='paseo'?'Archivo ~/.paseo/config.json. Primero configurá OpenCode. El ejemplo requiere opencode en PATH; el paquete automático resuelve su ruta.':type==='opencode'?'Archivo ~/.config/opencode/opencode.json. Si ya tenés otros proveedores, combiná este bloque o usá el paquete automático.':'Archivo ~/.continue/config.yaml. Conservá tus otros modelos al combinarlo; el paquete automático lo hace por vos.';}
function toggleClientKey(){if(!clientConfig)return;clientKeyShown=!clientKeyShown;el('client-api-key').type=clientKeyShown?'text':'password';el('client-show-key').textContent=clientKeyShown?'Ocultar clave':'Mostrar clave';renderClientSnippet();}
async function copyClientKey(){try{await navigator.clipboard.writeText(clientConfig.api_key);toast('Clave de la conexión copiada.');}catch(e){toast('No se pudo copiar la clave.',true);}}
async function copyClientConfig(){try{await navigator.clipboard.writeText(clientConfig.configs[el('snippet-client').value]);toast('Configuración completa copiada, incluida la clave API.');}catch(e){toast('No se pudo copiar la configuración.',true);}}
async function probeClientAPI(){if(!clientConfig)return;el('client-probe-result').textContent='Comprobando la API…';try{const r=await fetch(clientConfig.url+'/models',{headers:{Authorization:'Bearer '+clientConfig.api_key}});if(!r.ok)throw Error(r.status===503?'El modelo está apagado o cargando. Revisá Actividad.':r.status===401?'La clave de la conexión no es válida.':'La API devolvió HTTP '+r.status);const d=await r.json();el('client-probe-result').textContent='API accesible (HTTP 200). Modelos informados: '+(d.data||[]).map(m=>m.id).join(', ')+'. Esta prueba consulta modelos; no genera texto.';}catch(e){el('client-probe-result').textContent=e.message;}}

async function diagnoseAccount(){
 const button=el('ops-result');button.textContent='Revisando Kaggle, HTTPS y modelo cargado…';
 try{const d=await post('/api/diagnose',{key:el('ops-account').value});button.textContent=`${d.message} Kaggle: ${d.state}. API: ${d.api_status||'sin conexión'}. Modelo en memoria: ${d.model_loaded?'sí':'no'}. ${d.paseo}`;}catch(e){button.textContent=e.message;}
}
async function prepareWork(){const key=el('ops-account').value;if(!key)return;await startAccount(key);}
async function extendWork(){const key=el('ops-account').value;if(!key)return;if(await ask('Continuar trabajando','Agrega 30 minutos al límite de esta sesión y renueva el plazo de inactividad. La GPU seguirá consumiendo cuota. Requiere el notebook actualizado.','Extender sesión'))await act('extend',key);}
async function savePerformanceProfile(){const key=el('ops-account').value;if(!key)return;if(await act('profile',key,{preset:el('performance-profile').value}))toast('Guardado para el próximo arranque. Prepará de nuevo la configuración de tus clientes.');}

const renderBeforeOperations=render;
render=function(){
 renderBeforeOperations();renderOperationControls();renderTemplates();renderQuickTpsModels();
 const chosen=latest.accounts.find(active)||latest.accounts.find(a=>a.key===el('ops-account').value),runtime=chosen?.runtime;
 el('runtime-stage').textContent=runtime?`${name(chosen)} · ${runtime.label} · informe ${new Date(runtime.timestamp*1000).toLocaleTimeString('es-AR')}. El apagado se confirma con el estado de Kaggle.`:'Las etapas reales se reciben desde el próximo notebook actualizado. La cola de Kaggle no tiene duración predecible.';
 for(const a of latest.accounts.filter(active)){
  const live=a.live;if(!live||live.session_remaining==null)continue;
  const session=Math.max(0,live.session_remaining),idle=live.idle_remaining;
  const text=`${name(a)}: límite de sesión en ${Math.ceil(session/60)} min; ${idle==null?'generando, inactividad suspendida':'autoapagado por inactividad en '+Math.ceil(idle/60)+' min'}.`;
  el('banner-text').textContent+=' '+text;
  if(session<=300)notify(a.key+'-session-'+Math.floor(live.uptime_seconds/3600),'Se acerca el límite de la sesión',text);
  if(idle!=null&&idle<=120)notify(a.key+'-idle-'+Math.floor(live.uptime_seconds/300),'Se acerca el autoapagado',text);
 }
};

let operationsAccountInitialized=false,loadedOperationsAccount=null;
function renderOperationControls(){
 if(!operationsAccountInitialized){const initial=latest.accounts.find(active)||latest.accounts.find(a=>a.configured);if(initial){el('ops-account').value=initial.key;operationsAccountInitialized=true;}}
 const selected=account(el('ops-account').value),button=el('extend-work');
 if(selected&&loadedOperationsAccount!==selected.key){el('performance-profile').value=selected.performance_profile||'contexto';loadedOperationsAccount=selected.key;}
 const capable=selected?.live?.capabilities?.includes('session-v1');
 button.disabled=busy()||!capable;
 button.title=capable?'Extender esta sesión 30 minutos':'Disponible con el notebook actualizado, desde el próximo encendido';
}

let templateCatalog=null,templateAccountSet=false;
async function loadTemplates(){try{const r=await fetch('/api/templates',{cache:'no-store'});if(!r.ok)throw Error('No se pudo cargar el catálogo.');templateCatalog=await r.json();renderTemplates();renderQuickTpsModels();if(latest)renderDashboard();}catch(e){el('template-library').textContent=e.message;}}
function renderTemplates(){
 if(!templateCatalog||!latest)return;
 if(!templateAccountSet){const initial=latest.accounts.find(active)||latest.accounts.find(a=>a.configured);if(initial){el('template-account').value=initial.key;templateAccountSet=true;}}
 const filter=el('template-filter').value,search=el('template-search').value.trim().toLowerCase();let cards=[];
 const matches=t=>(t.name+' '+t.category+' '+(t.arch||'')+' '+(t.tps_range||'')+' '+(t.description||'')).toLowerCase().includes(search);
 const curAcc=account(el('template-account').value);
 if(filter==='all'||filter==='models'||filter==='fast'){
  const modelList=templateCatalog.models.filter(t=>matches(t)&&(filter!=='fast'||t.tps_tier==='ultra'));
  const fmtCtx=n=>n>=1000000?'1M':Math.round(n/1024)+'k';
  cards.push(...modelList.map(t=>{
    const isInstalled=curAcc&&(curAcc.template_id===t.id||curAcc.filename===t.filename);
    return `<article class="recipe"><div class="recipe-top"><span class="recipe-category">${esc(t.category)}${isInstalled?' · ACTIVA EN ESTA CUENTA':''}</span><span class="chip tps">${icon('activity')} ${esc('Sin medición GPU')}</span></div><h3>${esc(uiText(t.name))}</h3><p>${esc(uiText(t.description))}</p><dl class="recipe-facts"><div><dt>Velocidad T4</dt><dd>${esc('Sin medición GPU')}</dd></div><div><dt>Pesos GGUF</dt><dd>${(t.size_bytes/1e9).toFixed(2)} GB</dd></div><div><dt>Contexto (act/nat)</dt><dd>${fmtCtx(t.context)} / ${fmtCtx(t.native_context||t.context)}</dd></div></dl><p class="hint"><strong>Arquitectura:</strong> ${esc(t.arch||'GGUF')} · ${esc(t.vram_fit||'2× Tesla T4')}</p><p class="hint">Revisión ${esc(t.revision.slice(0,10))} · ${esc(t.filename.match(/Q\d_[A-Z0-9_]+|Q\d_K/i)?.[0]||'GGUF')} · ${esc(t.license)}</p><div class="buttons"><button class="${isInstalled?'':'primary'}" ${busy()?'disabled':''} onclick="installTemplate('${t.id}')">${isInstalled?'Reinstalar plantilla':'Instalar plantilla'}</button><a href="https://huggingface.co/${esc(t.repo)}/tree/${esc(t.revision)}" target="_blank" rel="noreferrer">Ver en HF ${icon('external')}</a></div></article>`;
  }));
 }
 if(filter==='all'||filter==='tools')cards.push(...templateCatalog.tools.filter(matches).map(t=>`<article class="recipe"><span class="recipe-category">Herramienta local</span><h3>${esc(uiText(t.name))}</h3><p>${esc(uiText(t.description))}</p><p class="hint">${esc(t.packages.join(' · '))}</p><p class="hint">Instalación en entorno aislado. Requiere Python 3.12. Sin inicio automático de GPU.</p><div class="buttons"><button onclick="prepareTool('${t.id}')">Preparar instalador privado</button><a href="${esc(t.source)}" target="_blank" rel="noreferrer">GitHub ${icon('external')}</a></div></article>`));
 if(filter==='all'||filter==='workflows')cards.push(...templateCatalog.workflows.filter(matches).map(t=>`<article class="recipe"><span class="recipe-category">Instrucciones para tu agente</span><h3>${esc(uiText(t.name))}</h3><p>${esc(t.prompt)}</p><div class="buttons"><button class="primary" onclick="useWorkflowInChat('${t.id}')">${icon('chat')}Usar en Chat Web</button><button onclick="copyWorkflow('${t.id}')">${icon('copy')}Copiar</button></div></article>`));
 html('template-library',cards.join('')||'<p class="empty">No hay plantillas que coincidan con tu búsqueda.</p>');
 html('template-sources',templateCatalog.sources.map(s=>`<article class="recipe"><h3>${esc(s.name)}</h3><p>${esc(s.use)}</p><a href="${esc(s.url)}" target="_blank" rel="noreferrer">Ver repositorio ${icon('external')}</a></article>`).join(''));
}

async function installTemplateForAccount(key,id){
 const a=account(key),t=templateCatalog?.models?.find(m=>m.id===id);
 if(!a||!t){toast('Agregá una cuenta para instalar este modelo.',true);return;}
 const stop=active(a)||unknown(a);
 if(!await ask('Cambiar a '+t.name,`${stop?'Primero se solicitará y comprobará el apagado de '+name(a)+'. ':''}Se configurará ${t.name} (${'Velocidad sin medir'}, ${t.arch||'GGUF'}) con contexto ${fmt(t.context)} y optimizaciones FlashAttention + KV Q8_0. Los pesos (${(t.size_bytes/1e9).toFixed(2)} GB) se descargarán cuando elijas Encender.`,stop?'Apagar y configurar':'Configurar sin encender',stop))return;
 await act('install_template',key,{template:id,stop},true);
}
async function installTemplate(id){
 await installTemplateForAccount(el('template-account').value,id);
}
async function prepareTool(id){
 const key=el('template-account').value;if(!key){toast('Agregá una cuenta primero.',true);return;}
 if(!await ask('Preparar herramienta para tu PC','El paquete incluye la URL y clave de inferencia de la cuenta elegida. Guardalo en privado. Extraelo y ejecutá INSTALAR.bat en tu PC; esto no enciende Kaggle.','Preparar instalador'))return;
 el('template-result').textContent='Preparando el instalador privado…';
 try{const d=await post('/api/tool-package',{key,tool:id});html('template-download',`<a class="download" href="/api/download/${encodeURIComponent(d.download.id)}">Descargar instalador privado</a>`);el('template-result').textContent='Instalador listo para '+name(account(key))+'. La herramienta todavía no está instalada en tu PC: descargá, extraé el ZIP y ejecutá INSTALAR.bat.';}catch(e){el('template-result').textContent=e.message;}
}
async function copyWorkflow(id){const w=templateCatalog.workflows.find(w=>w.id===id);if(!w)return;try{await navigator.clipboard.writeText(w.prompt);toast('Instrucciones copiadas. Completá los campos entre corchetes.');}catch{toast('No se pudo copiar.',true);}}
async function useWorkflowInChat(id){
 const w=templateCatalog?.workflows?.find(w=>w.id===id);if(!w)return;
 navigate('chat');
 await createChatConversation(w.name,w.prompt);
 toast('Conversación creada con la plantilla "'+w.name+'".');
}

/* ==========================================
   COMMAND PALETTE (Ctrl+K)
   ========================================== */
function openPalette(){
  const d=el('palette-dialog');
  el('palette-search').value='';
  renderPalette();
  d.showModal();
  setTimeout(()=>el('palette-search').focus(),30);
}
function renderPalette(){
  const q=el('palette-search').value.trim().toLowerCase();
  const configured=latest?.accounts?.filter(a=>a.configured)||[];
  const items=[
    {label:'Ir a Chat IA Multimodal',sub:'Enviar documentos, fotos, videos y código con TPS en vivo',run:()=>navigate('chat')},
    {label:'Optimizar TPS y cambiar modelo en Tesla T4',sub:'Comparar MoE A3B (45–65 TPS) vs 1× GPU vs Denso',run:()=>navigate('modelos')},
    {label:'Nueva conversación en Chat IA',sub:'Crear sesión limpia con tu modelo',run:()=>{navigate('chat');createChatConversation();}},
    {label:'Ir al Dashboard',sub:'Resumen de cuotas, tokens y sesiones',run:()=>navigate('dashboard')},
    {label:'Ir a Catálogo de Plantillas',sub:'Modelos Qwen3 Coder 30B A3B, Cyber-Tiel MTP, Qwen3.5 9B…',run:()=>navigate('plantillas')},
    {label:'Ir a Cuentas de Kaggle',sub:'Agregar o administrar tokens API',run:()=>navigate('cuentas')},
    {label:'Ir a Actividad y Logs en vivo',sub:'Ver progreso de arranque o parada en Kaggle',run:()=>navigate('actividad')},
    {label:'Configurar clientes IDE (Continue / OpenCode / Paseo)',sub:'Generar paquete privado con URL HTTPS y clave',run:()=>{navigate('configuracion');setting('connection');}},
    {label:'Exportar código público para GitHub',sub:'Generar ZIP limpio sin claves ni .private',run:()=>act('export_program')},
    {label:'Apagar todas las GPU en Kaggle',sub:'Confirmar parada de todas las sesiones',run:()=>stopAll()}
  ];
  for(const a of configured){
    items.push({label:`Chatear con ${name(a)}`,sub:a.label,run:()=>openChatForAccount(a.key)});
    items.push({label:`Encender GPU de ${name(a)}`,sub:`Estado actual: ${states[a.state]||a.state}`,run:()=>startAccount(a.key)});
    items.push({label:`Diagnosticar conexión de ${name(a)}`,sub:'Probar Kaggle + API HTTPS + modelo en memoria',run:()=>quickDiagnose(a.key)});
  }
  const filtered=items.filter(i=>(i.label+' '+i.sub).toLowerCase().includes(q));
  html('palette-list',filtered.map((item,idx)=>`<button type="button" class="palette-item" data-idx="${idx}"><span>${esc(item.label)}</span><small>${esc(item.sub)}</small></button>`).join('')||'<p class="empty">Sin coincidencias.</p>');
  el('palette-list').querySelectorAll('.palette-item').forEach(btn=>{
    btn.onclick=()=>{const idx=Number(btn.dataset.idx);closeDialog('palette-dialog');filtered[idx]?.run();};
  });
}
window.addEventListener('keydown',e=>{
  if(e.key==='Escape'&&el('chat-sidebar').classList.contains('open'))setChatSidebar(false,true);
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){
    e.preventDefault();
    if(el('palette-dialog').open)closeDialog('palette-dialog');
    else openPalette();
  }
});

async function cacheAction(action){const key=el('ops-account').value;if(!key)return;if(action==='cache_launch'&&!await ask('Preparar pesos sin GPU','Se iniciará un notebook CPU privado para descargar y verificar un modelo en Kaggle. Puede tardar; no consume cuota GPU. No se guardan credenciales en su código.','Preparar con CPU'))return;await act(action,key,{},true);}


/* Protected downloads must never save a session error as the requested file. */
async function downloadPrivateFile(event,link){
  const url=new URL(link.href,location.origin);
  if(url.origin!==location.origin||!/^\/api\/(?:chat\/attachment|download)\/[a-f0-9]+$/.test(url.pathname))return;
  if(url.pathname.startsWith('/api/chat/attachment/')&&url.searchParams.get('inline')==='1')return;
  event.preventDefault();
  if(link.dataset.downloading==='true')return;
  link.dataset.downloading='true';link.setAttribute('aria-busy','true');
  try{
    const response=await fetch(url.pathname+url.search,{credentials:'same-origin',cache:'no-store'});
    if(response.status===401){location.assign('/login?expired=1&next='+encodeURIComponent(url.pathname+url.search));return;}
    if(!response.ok)throw Error(response.status===404?'Este archivo ya no está disponible.':'No se pudo descargar el archivo. Intentá nuevamente.');
    const content=await response.blob(),objectURL=URL.createObjectURL(content),download=document.createElement('a');
    const disposition=response.headers.get('Content-Disposition')||'',headerName=disposition.match(/filename="([^"]+)"/);
    download.href=objectURL;download.download=link.download||(headerName?headerName[1]:'archivo');document.body.appendChild(download);download.click();download.remove();
    setTimeout(()=>URL.revokeObjectURL(objectURL),1500);
  }catch(error){toast(error.message||'No se pudo descargar el archivo.',true);}
  finally{delete link.dataset.downloading;link.removeAttribute('aria-busy');}
}
document.addEventListener('click',event=>{const link=event.target.closest?.('a[href]');if(link)downloadPrivateFile(event,link);});
fetch('/api/session').then(r=>r.ok?r.json():null).then(s=>{if(!s)return;if(s.csrf)token=s.csrf;el('session-user').textContent=s.username;el('avatar').textContent=s.username.slice(0,2).toUpperCase();el('security-username').textContent=s.username;el('logout-button').hidden=!s.remote;el('security-logout').disabled=!s.remote;el('change-password').disabled=!s.remote;}).catch(()=>{});
bindChatDropzone();
loadTemplates();
navigate(location.hash.slice(1)||'dashboard');
refresh();
setInterval(refresh,5000);
