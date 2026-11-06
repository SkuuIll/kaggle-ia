/* ==========================================
   CHAT MULTIMODAL WORKSPACE
   ========================================== */
const WORKFLOW_PRESETS={
  'analisis-archivos':'Sos un asistente técnico multimodal. Cuando el usuario adjunte documentos (PDF, Word, Excel, PowerPoint, código), fotos, videos o audios, analizá minuciosamente su contenido y metadatos, citá las secciones relevantes y ofrecé respuestas estructuradas y accionables en español.',
  'bugfix':'Sos un ingeniero de software experto en depuración. Analizá el síntoma, identificá la causa raíz antes de proponer cambios, modificá solo lo indispensable y explicá cómo verificar la solución.',
  'cambio-controlado':'Sos un arquitecto de software cuidadoso. Respetá la estructura existente del proyecto, mantené los nombres y contratos actuales y proponé cambios limpios y probados.',
  'proyecto-nuevo':'Sos un arquitecto de software. Proponé primero un árbol de archivos mínimo y claro, explicá cómo ejecutarlo y luego escribí el código modular listo para descargar.',
  'revision':'Sos un revisor de seguridad y calidad de código. Buscá errores de borde, fugas de credenciales, problemas de concurrencia y oportunidades de mejora concretas.'
};

function chatPreference(key,value){
  try{
    if(value===undefined)return localStorage.getItem('kaggle-chat:'+key);
    localStorage.setItem('kaggle-chat:'+key,value);
  }catch{}
}

const chatDrafts=new Map();
try{
  for(const [id,text] of JSON.parse(localStorage.getItem('kaggle-chat:drafts')||'[]')){
    if(typeof id==='string'&&typeof text==='string')chatDrafts.set(id,text.slice(0,32000));
  }
}catch{}

function storeChatDraft(id,text){
  const key=id||'new';
  chatDrafts.delete(key);
  if(text)chatDrafts.set(key,text.slice(0,32000));
  if(chatDrafts.size>20)chatDrafts.delete(chatDrafts.keys().next().value);
  try{
    const persisted=new Map(JSON.parse(localStorage.getItem('kaggle-chat:drafts')||'[]'));
    persisted.delete(key);
    if(text)persisted.set(key,chatDrafts.get(key));
    if(persisted.size>20)persisted.delete(persisted.keys().next().value);
    localStorage.setItem('kaggle-chat:drafts',JSON.stringify([...persisted]));
  }catch{}
}

function editChatDraft(input){
  storeChatDraft(activeChatId,input.value);
  autoGrowChatInput(input);
}
let creatingChat=false,uploadingChatFiles=false,sendingChatMessage=false,chatSelection=0,chatRequestConversation=null;
let chatConversations=[],activeChatId=null,chatState={conversation:null,messages:[]},pendingAttachments=[],activeRequestId=null,chatPollTimer=null,codeBlocksStore=[];

async function loadChatConversations(){
  const status=el('chat-history-status');
  const retry=el('chat-history-retry');
  status.textContent='Cargando conversaciones…';
  status.hidden=false;
  retry.hidden=true;
  try{
    const r=await fetch('/api/chat/conversations',{cache:'no-store'});
    if(r.status===401){location.replace('/login?expired=1&next=%2F%23chat');return;}
    if(!r.ok)throw Error('No se pudo consultar el historial.');
    const d=await r.json();
    chatConversations=d.conversations||[];
    el('chat-count').textContent=chatConversations.length;
    renderChatList();
    if(!activeChatId&&chatConversations.length){
      const last=chatConversations.find(chat=>chat.id===chatPreference('conversation'));
      await selectChatConversation((last||chatConversations[0]).id);
    }else{
      if(!activeChatId){
        el('chat-input').value=chatDrafts.get('new')||'';
        autoGrowChatInput(el('chat-input'));
      }
      renderChatHeaderStatus();
      renderChatMessages();
    }
    status.hidden=true;
  }catch{
    status.textContent='No se pudo cargar el historial.';
    retry.hidden=false;
  }
}

function renderChatList(){
  const q=(el('chat-search')?.value||'').trim().toLowerCase();
  const list=chatConversations.filter(c=>c.title.toLowerCase().includes(q));
  html('chat-list',list.length?list.map(c=>{
    const acc=account(c.account);
    const accLabel=acc?'Cuenta '+acc.account:'Cuenta sin configurar';
    const date=new Date(c.updated_at*1000);
    const dateLabel=date.toLocaleDateString('es-AR',{day:'numeric',month:'short'});
    const current=c.id===activeChatId;
    return `<div role="listitem" class="chat-conv-item ${current?'active':''}">
      <button type="button" class="chat-conv-open" ${current?'aria-current="true"':''} onclick="selectChatConversation('${esc(c.id)}')">
        ${icon('chat')}<span class="chat-conv-meta"><span class="chat-conv-title" title="${esc(c.title)}">${esc(c.title)}</span>
        ${c.preview&&!/^\s*<think>/i.test(c.preview)?`<span class="chat-conv-preview">${esc(c.preview)}</span>`:''}<span class="chat-conv-sub"><span>${esc(accLabel)}</span><span>${esc(dateLabel)}</span></span></span>
      </button>
      <details class="chat-history-menu">
        <summary aria-label="Opciones de ${esc(c.title)}">⋯</summary>
        <div><button type="button" onclick="renameChatConversation('${esc(c.id)}')">Renombrar</button>
        <button type="button" class="danger" onclick="deleteChatConversation('${esc(c.id)}')">Archivar</button></div>
      </details>
    </div>`;
  }).join(''):`<p class="chat-history-empty">${q?'No hay chats que coincidan.':'Tus conversaciones van a aparecer acá.'}</p>`);
}

async function createChatConversation(customTitle='',customPrompt=''){
  if(creatingChat)return;
  const configured=latest?.accounts?.filter(a=>a.configured)||[];
  if(!configured.length){toast('Agregá una cuenta en Cuentas antes de crear una conversación.',true);return;}
  creatingChat=true;
  const chosenKey=el('chat-account')?.value||(configured.find(active)||configured[0])?.key||'rapido';
  const presetKey=el('chat-workflow-preset')?.value||'';
  const sysPrompt=customPrompt||(WORKFLOW_PRESETS[presetKey]||'');
  try{
    const created=await post('/api/chat/conversations',{account:chosenKey,title:customTitle,system_prompt:sysPrompt});
    if(!activeChatId){
      storeChatDraft(created.id,el('chat-input').value);
      storeChatDraft(null,'');
    }
    await selectChatConversation(created.id);
    await loadChatConversations();
  }catch(e){toast(e.message,true);}
  finally{creatingChat=false;}
}

async function selectChatConversation(id){
  const selection=++chatSelection;
  try{
    const r=await fetch('/api/chat/conversations/'+encodeURIComponent(id),{cache:'no-store'});
    if(!r.ok)throw Error('No se pudo abrir la conversación.');
    const conversation=await r.json();
    if(selection!==chatSelection)return;
    const input=el('chat-input');
    const switched=activeChatId!==id;
    if(switched){
      if(activeChatId)storeChatDraft(activeChatId,input.value);
      input.value=chatDrafts.get(id)||'';
      autoGrowChatInput(input);
    }
    chatState=conversation;
    activeChatId=chatState.conversation.id;
    chatPreference('conversation',activeChatId);
    chatPreference('account',chatState.conversation.account);
    setChatSidebar(false);
    pendingAttachments=chatState.pending_attachments||[];renderPendingFiles();
    if(el('chat-account')&&chatState.conversation.account)el('chat-account').value=chatState.conversation.account;
    const promptText=chatState.conversation.system_prompt||'';
    el('chat-system-prompt').value=promptText;
    el('chat-workflow-preset').value=Object.keys(WORKFLOW_PRESETS).find(key=>WORKFLOW_PRESETS[key]===promptText)||'';
    renderChatList();
    renderChatHeaderStatus();
    renderChatMessages(switched);
    const last=chatState.latest_request;
    showChatContext(last?.context);
    if(last?.status==='running'&&!activeRequestId){activeRequestId=last.id;chatRequestConversation=activeChatId;pollChatRequest(last.id,last.message_id);}
    renderChatHeaderStatus();
  }catch(e){toast(e.message,true);}
}

function renderChatHeaderStatus(){
  if(!el('chat-active-title'))return;
  const conv=chatState.conversation;
  el('chat-active-title').textContent=conv?conv.title:'Nueva conversación';
  const accKey=conv?.account||el('chat-account')?.value||'rapido';
  const acc=account(accKey);
  const pill=el('chat-gpu-pill');
  const startBtn=el('chat-quick-start'),stopBtn=el('chat-quick-stop');
  const ready=acc?.state==='RUNNING'&&acc.live?.model_ready===true;
  let status='Elegí una cuenta configurada para usar el chat.';
  if(acc?.configured){
    if(ready)status='';
    else if(acc.state==='QUEUED')status='Kaggle puso la sesión en cola. Podés preparar tu mensaje mientras esperás.';
    else if(acc.state==='RUNNING')status='Kaggle está preparando el modelo. Podés escribir mientras esperás.';
    else if(busy())status='Hay una operación en curso. Podés seguirla en Actividad.';
    else if(unknown(acc))status='El estado de Kaggle todavía no se confirmó. Revisá Actividad o ejecutá el diagnóstico.';
    else status='GPU apagada';
  }
  if(activeRequestId&&chatRequestConversation!==activeChatId)status='Hay una respuesta en curso en otra conversación.';
  const operation=powerSubmission||visibleJob();
  if(operation?.status==='running'&&powerActions.has(operation.action))status=describePower(operation).join(' · ');
  const statusNode=el('chat-connection-status');
  if(statusNode.textContent!==status)statusNode.textContent=status;
  statusNode.hidden=!status;
  const [gpuState,tone]=gpuStatus(acc);
  pill.className='badge '+tone;
  if(pill.textContent!==gpuState)pill.textContent=gpuState;
  const accountName=acc?'Cuenta '+acc.account+(acc.nickname||acc.username?' · '+name(acc):''):'Elegí una cuenta';
  setJobText('chat-server-account',accountName);
  el('chat-server-account').title=accountName;
  const stopping=operation?.status==='running'&&['stop','stop_all'].includes(operation.action);
  el('chat-active-subtitle').textContent=acc?uiText(acc.label)+' · '+fmt(acc.context)+' de contexto':'Seleccioná una cuenta para empezar.';
  const inlineStart=el('chat-compose-start');
  inlineStart.hidden=!acc?.configured||active(acc)||unknown(acc)||busy();
  startBtn.hidden=!acc?.configured||active(acc);
  startBtn.disabled=busy()||!acc||unknown(acc);
  stopBtn.hidden=!acc?.configured||(!active(acc)&&!unknown(acc));
  stopBtn.disabled=stopping||Boolean(powerSubmission);
  const stopTargetsAccount=stopping&&(operation.action==='stop_all'||operation.key===accKey);
  el('chat-send-btn').disabled=!ready||stopTargetsAccount||sendingChatMessage||uploadingChatFiles||Boolean(activeRequestId);
  el('chat-cancel-btn').hidden=!activeRequestId||chatRequestConversation!==activeChatId;
}

async function changeChatAccount(newKey){
  const conversation=chatState.conversation;
  if(!newKey)return;
  if(!conversation){chatPreference('account',newKey);renderChatHeaderStatus();return;}
  try{
    const updated=await post('/api/chat/rename',{id:conversation.id,account:newKey});
    chatPreference('account',newKey);
    if(activeChatId===conversation.id)chatState.conversation.account=updated.account;
    renderChatHeaderStatus();
    await loadChatConversations();
    toast('Cuenta de la conversación actualizada.');
  }catch(e){
    if(activeChatId===conversation.id)el('chat-account').value=chatState.conversation.account;
    toast(e.message,true);
  }
}

async function applyChatWorkflowPreset(presetKey){
  const promptText=WORKFLOW_PRESETS[presetKey]||'';
  const conversation=chatState.conversation;
  if(!conversation)return;
  try{
    const updated=await post('/api/chat/rename',{id:conversation.id,system_prompt:promptText});
    if(activeChatId===conversation.id){
      chatState.conversation.system_prompt=updated.system_prompt;
      el('chat-system-prompt').value=updated.system_prompt;
    }
    toast(presetKey?'Modo de trabajo aplicado a esta conversación.':'Modo libre activado.');
  }catch(e){
    if(activeChatId===conversation.id){
      el('chat-workflow-preset').value=Object.keys(WORKFLOW_PRESETS).find(key=>WORKFLOW_PRESETS[key]===chatState.conversation.system_prompt)||'';
    }
    toast(e.message,true);
  }
}

function toggleChatSettings(){
  const drawer=el('chat-settings-drawer');
  if(drawer.open){drawer.close();return;}
  el('chat-reasoning-effort').value=localStorage.getItem('chat-reasoning-effort')||'';
  drawer.showModal();
  loadChatStorage();
}

async function saveChatSettings(){
  if(!activeChatId)return;
  try{
    const sys=el('chat-system-prompt').value.trim();
    const updated=await post('/api/chat/rename',{id:activeChatId,system_prompt:sys});
    if(chatState.conversation)chatState.conversation.system_prompt=updated.system_prompt;
    localStorage.setItem('chat-reasoning-effort',el('chat-reasoning-effort').value);
    el('chat-settings-drawer').close();
    toast('Ajustes del chat guardados.');
  }catch(e){toast(e.message,true);}
}

async function renameChatConversation(id=activeChatId){
  const conversation=chatConversations.find(c=>c.id===id)|| (id===activeChatId?chatState.conversation:null);
  if(!conversation)return;
  const nextTitle=prompt('Nuevo título para la conversación:',conversation.title)?.trim();
  if(!nextTitle)return;
  try{
    const updated=await post('/api/chat/rename',{id,title:nextTitle});
    if(activeChatId===id)chatState.conversation.title=updated.title;
    document.querySelectorAll('.chat-history-menu[open]').forEach(menu=>menu.open=false);
    await loadChatConversations();
  }catch(e){toast(e.message,true);}
}

async function deleteChatConversation(targetId=null){
  const cid=targetId||activeChatId;
  if(!cid)return;
  if(!await ask('Archivar conversación','La conversación se quitará de la lista activa del Chat Web.','Archivar',true))return;
  try{
    await post('/api/chat/delete',{id:cid});
    document.querySelectorAll('.chat-history-menu[open]').forEach(menu=>menu.open=false);
    storeChatDraft(cid,'');
    if(activeChatId===cid){activeChatId=null;chatState={conversation:null,messages:[]};el('chat-input').value='';}
    await loadChatConversations();
    toast('Conversación archivada.');
  }catch(e){toast(e.message,true);}
}

async function startChatAccount(){
  const key=chatState.conversation?.account||el('chat-account')?.value;
  if(key)await startAccount(key,false);
}
async function stopChatAccount(){
  const key=chatState.conversation?.account||el('chat-account')?.value;
  if(key)await stopAccount(key,false);
}
async function diagnoseChatAccount(){
  const key=chatState.conversation?.account||el('chat-account')?.value;
  if(key)await quickDiagnose(key);
}

/* File Uploads & Drag-and-Drop */
function bindChatDropzone(){
  const more=el('chat-more');
  const viewport=window.visualViewport;
  if(viewport){
    const resize=()=>{
      const focused=document.activeElement===el('chat-input')&&viewport.scale===1;
      document.documentElement.style.setProperty('--chat-viewport',focused?viewport.height+'px':'');
      document.body.classList.toggle('chat-keyboard-open',focused&&viewport.height<480&&window.innerHeight-viewport.height>80);
    };
    viewport.addEventListener('resize',resize);
    el('chat-input').addEventListener('focus',resize);
    el('chat-input').addEventListener('blur',resize);
  }
  el('chat-settings-drawer').addEventListener('close',()=>more.querySelector('summary').focus());
  more.addEventListener('click',event=>{
    if(event.target.closest('button')){
      more.open=false;
      if(!el('chat-settings-drawer').open)more.querySelector('summary').focus();
    }
  });
  document.addEventListener('click',event=>{
    if(more.open&&!more.contains(event.target))more.open=false;
  });
  more.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&more.open){
      more.open=false;
      more.querySelector('summary').focus();
    }
  });
  el('lightbox-dialog').addEventListener('close',resetAttachmentViewer);
  const dropzone=el('chat-dropzone'),dropOverlay=el('chat-drop-overlay');
  if(!dropzone)return;
  let dragCounter=0;
  dropzone.addEventListener('dragenter',e=>{e.preventDefault();dragCounter++;dropOverlay.hidden=false;});
  dropzone.addEventListener('dragover',e=>{e.preventDefault();});
  dropzone.addEventListener('dragleave',e=>{e.preventDefault();dragCounter=Math.max(0,dragCounter-1);if(!dragCounter)dropOverlay.hidden=true;});
  dropzone.addEventListener('drop',async e=>{
    e.preventDefault();dragCounter=0;dropOverlay.hidden=true;
    if(e.dataTransfer?.files?.length)await handleChatFiles(e.dataTransfer.files);
  });
}

async function handleChatFiles(fileList){
  const files=[...fileList];
  if(!files.length||uploadingChatFiles)return;
  uploadingChatFiles=true;
  renderChatHeaderStatus();
  const statusNode=el('chat-upload-status');
  try{
    if(!activeChatId)await createChatConversation();
    const conversation=activeChatId;
    if(!conversation)return;
    if(pendingAttachments.length+files.length>8){
      toast('Podés adjuntar hasta 8 archivos por mensaje.',true);
      return;
    }
    for(const file of files){
      if(file.size>15*1024*1024){
        toast(`"${file.name}" supera el límite de 15 MB.`,true);
        continue;
      }
      statusNode.hidden=false;
      statusNode.textContent=`Procesando ${file.name}…`;
      try{
        const b64=await fileToBase64(file);
        const uploaded=await post('/api/chat/upload',{conversation,name:file.name,mime:file.type||'application/octet-stream',data:b64});
        if(activeChatId===conversation){
          pendingAttachments.push(uploaded);
          renderPendingFiles();
        }
      }catch(e){
        toast(`Error al subir ${file.name}: ${e.message}`,true);
      }
    }
  }finally{
    uploadingChatFiles=false;
    statusNode.hidden=true;
    statusNode.textContent='';
    renderChatHeaderStatus();
  }
}

function fileToBase64(file){
  return new Promise((resolve,reject)=>{
    const reader=new FileReader();
    reader.onload=()=>{
      const res=String(reader.result||'');
      const comma=res.indexOf(',');
      resolve(comma>=0?res.slice(comma+1):res);
    };
    reader.onerror=()=>reject(new Error('No se pudo leer el archivo.'));
    reader.readAsDataURL(file);
  });
}

function removePendingFile(id){
  pendingAttachments=pendingAttachments.filter(a=>a.id!==id);
  renderPendingFiles();
}

function renderPendingFiles(){
  const box=el('chat-pending-files');
  if(!box)return;
  if(!pendingAttachments.length){box.hidden=true;box.innerHTML='';return;}
  box.hidden=false;
  box.innerHTML=pendingAttachments.map(a=>`<span class="pending-pill"><b>${esc(a.name)}</b><small>${esc(a.summary)}</small><button type="button" title="Quitar adjunto" aria-label="Quitar adjunto" onclick="removePendingFile('${esc(a.id)}')">×</button></span>`).join('');
}

/* Markdown, Code Blocks & Media Rendering */
const EXT_BY_LANG={python:'py',py:'py',javascript:'js',js:'js',typescript:'ts',ts:'ts',html:'html',css:'css',json:'json',sql:'sql',bash:'sh',sh:'sh',shell:'sh',powershell:'ps1',yaml:'yml',yml:'yml',markdown:'md',md:'md',cpp:'cpp',c:'c',csharp:'cs',java:'java',go:'go',rust:'rs'};

function renderMarkdown(text,msgIndex){
  if(!text)return '';
  let thinkHtml='';
  let content=String(text);
  const thinkMatch=content.match(/<think>([\s\S]*?)(?:<\/think>|$)/i);
  if(thinkMatch){
    const rawThinking=thinkMatch[1].trim();
    content=content.replace(/<think>[\s\S]*?(?:<\/think>|$)/i,'').trim();
    if(rawThinking){
      const isStillThinking=!thinkMatch[0].includes('</think>');
      const label=isStillThinking?'Pensando…':'Proceso de razonamiento';
      const iconHtml=isStillThinking?'<i class="pulse"></i>':icon('cpu');
      thinkHtml=`<details class="chat-think-box" ${isStillThinking?'open':''}><summary>${iconHtml} <span>${label}</span></summary><div class="chat-think-content">${formatProse(rawThinking)}</div></details>`;
    }
  }
  if(!content&&thinkHtml)return thinkHtml;
  const parts=content.split(/```([a-zA-Z0-9_-]*)\n?([\s\S]*?)```/g);
  let out=thinkHtml;
  for(let i=0;i<parts.length;i+=3){
    const prose=parts[i];
    if(prose)out+=formatProse(prose);
    if(i+2<parts.length){
      const lang=(parts[i+1]||'txt').toLowerCase();
      const code=parts[i+2]||'';
      const idx=codeBlocksStore.push({lang,code})-1;
      const ext=EXT_BY_LANG[lang]||'txt';
      out+=`<div class="code-block"><div class="code-block-bar"><span>${esc(lang||'código')}</span><div class="buttons"><button type="button" id="copy-btn-${idx}" onclick="copyCodeBlock(${idx})">${icon('copy')}Copiar</button><button type="button" onclick="downloadCodeBlock(${idx},'snippet-${idx+1}.${ext}')">${icon('download')}.${ext}</button></div></div><pre><code>${esc(code.replace(/\n$/,''))}</code></pre></div>`;
    }
  }
  return out;
}

function formatProse(raw){
  const lines=raw.trim().split('\n'),result=[];
  const cells=line=>line.trim().replace(/^\|/,'').replace(/\|$/,'').split(/(?<!\\)\|/).map(value=>value.trim().replace(/\\\|/g,'|'));
  const divider=line=>/^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line||'');
  let i=0;
  while(i<lines.length){
    const line=lines[i];if(!line.trim()){i++;continue;}
    if(line.includes('|')&&divider(lines[i+1])){
      const headers=cells(line);i+=2;const rows=[];
      while(i<lines.length&&lines[i].trim()&&lines[i].includes('|')){const row=cells(lines[i++]);rows.push('<tr>'+headers.map((_,n)=>'<td>'+inlineFormat(row[n]||'')+'</td>').join('')+'</tr>');}
      result.push('<div class="chat-table-wrap" tabindex="0" role="region" aria-label="Tabla de la respuesta"><table><thead><tr>'+headers.map(h=>'<th scope="col">'+inlineFormat(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table></div>');continue;
    }
    const heading=line.match(/^(#{1,4})\s+(.+)$/);
    if(heading){result.push('<h'+Math.min(4,heading[1].length+1)+'>'+inlineFormat(heading[2])+'</h'+Math.min(4,heading[1].length+1)+'>');i++;continue;}
    const ordered=/^\s*\d+\.\s+/.test(line),unordered=/^\s*[-*]\s+/.test(line);
    if(ordered||unordered){const tag=ordered?'ol':'ul',pattern=ordered?/^\s*\d+\.\s+/:/^\s*[-*]\s+/;const items=[];while(i<lines.length&&pattern.test(lines[i]))items.push('<li>'+inlineFormat(lines[i++].replace(pattern,''))+'</li>');result.push('<'+tag+'>'+items.join('')+'</'+tag+'>');continue;}
    if(/^>\s?/.test(line)){const quote=[];while(i<lines.length&&/^>\s?/.test(lines[i]))quote.push(inlineFormat(lines[i++].replace(/^>\s?/,'')));result.push('<blockquote>'+quote.join('<br>')+'</blockquote>');continue;}
    const paragraph=[inlineFormat(line)];i++;
    while(i<lines.length&&lines[i].trim()&&!/^(#{1,4}\s|\s*[-*]\s|\s*\d+\.\s|>)/.test(lines[i])&&!(lines[i].includes('|')&&divider(lines[i+1])))paragraph.push(inlineFormat(lines[i++]));
    result.push('<p>'+paragraph.join('<br>')+'</p>');
  }
  return result.join('');
}

function inlineFormat(str){
  let s=esc(str);
  s=s.replace(/`([^`]+)`/g,'<code class="inline-code">$1</code>');
  s=s.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
  return s;
}

async function copyCodeBlock(idx){
  const item=codeBlocksStore[idx];
  if(!item)return;
  try{
    await navigator.clipboard.writeText(item.code);
    const b=el('copy-btn-'+idx);
    if(b){const orig=b.innerHTML;b.innerHTML=icon('check')+' Copiado';setTimeout(()=>{if(b)b.innerHTML=orig;},2000);}
    else{toast('Código copiado al portapapeles.');}
  }catch{toast('No se pudo copiar el código.',true);}
}

function downloadBlob(content,filename,mime='text/plain;charset=utf-8'){
  const blob=new Blob([content],{type:mime});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;a.download=filename;
  document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1500);
}

function downloadCodeBlock(idx,filename){
  const item=codeBlocksStore[idx];
  if(!item)return;
  downloadBlob(item.code,filename);
}

function resetAttachmentViewer(){
  const body=el('lightbox-body');
  const media=body.querySelector('video,audio');
  if(media){
    media.pause();
    media.removeAttribute('src');
    media.load();
  }
  body.replaceChildren();
}

async function openAttachmentViewer(button){
  const {attachmentId,attachmentName,attachmentKind,attachmentMime}=button.dataset;
  const url='/api/chat/attachment/'+encodeURIComponent(attachmentId);
  const inlineUrl=url+'?inline=1';
  const dialog=el('lightbox-dialog'),body=el('lightbox-body');
  const original=el('lightbox-original');
  resetAttachmentViewer();
  el('lightbox-caption').textContent=attachmentName;
  el('lightbox-download').href=url;
  el('lightbox-download').download=attachmentName;
  original.hidden=attachmentMime!=='application/pdf';
  if(!original.hidden)original.href=inlineUrl;
  dialog.showModal();

  const mediaTag={image:'img',video:'video',audio:'audio'}[attachmentKind];
  if(mediaTag){
    const media=document.createElement(mediaTag);
    if(mediaTag==='img')media.alt=attachmentName;
    else{
      media.controls=true;
      media.preload='metadata';
      if(mediaTag==='video')media.playsInline=true;
    }
    media.addEventListener('error',()=>{
      const note=document.createElement('p');
      note.textContent='El navegador no pudo abrir este archivo. Podés descargar el original.';
      media.replaceWith(note);
    },{once:true});
    media.src=inlineUrl;
    body.append(media);
    return;
  }
  const preview=document.createElement('pre');
  preview.textContent='Cargando vista previa…';
  body.append(preview);
  try{
    const response=await fetch(url+'?preview=1',{cache:'no-store'});
    if(!response.ok)throw Error(response.status===401?'Tu sesión terminó. Volvé a ingresar al panel.':'No se pudo abrir la vista previa.');
    const data=await response.json();
    preview.textContent=data.text||'Este archivo no tiene texto extraíble. Podés descargar el original.';
  }catch(error){
    preview.textContent=error.message;
  }
}

function renderAttachmentCard(a){
  const inlineUrl=`/api/chat/attachment/${encodeURIComponent(a.id)}?inline=1`;
  const downloadUrl=`/api/chat/attachment/${encodeURIComponent(a.id)}`;
  const thumbnail=a.kind==='image'? `<img class="chat-att-thumb" onerror="attachmentPreviewError(this)" src="${inlineUrl}" alt="${esc(a.name)}" loading="lazy">`:'';
  const attributes=`data-attachment-id="${esc(a.id)}" data-attachment-name="${esc(a.name)}" data-attachment-kind="${esc(a.kind)}" data-attachment-mime="${esc(a.mime)}"`;
  return `<div class="chat-att-card">${thumbnail}<div class="chat-att-info"><div><div class="chat-att-name">${esc(a.name)}</div><div class="chat-att-sum">${esc(a.summary)}</div></div></div><div class="chat-att-actions"><button type="button" ${attributes} onclick="openAttachmentViewer(this)">Vista previa</button><a href="${downloadUrl}" download="${esc(a.name)}">${icon('download')}Descargar</a></div></div>`;
}

function renderChatMessages(scrollBottom=false){
  const box=el('chat-messages');
  if(!box)return;
  const msgs=chatState.messages||[];
  codeBlocksStore=[];
  if(!msgs.length){
    box.innerHTML=`<div class="chat-hero">
      <div class="chat-hero-ring">${icon('cpu')}</div>
      <div class="chat-start-label">ESPACIO DE CHAT</div>
      <h3 class="chat-hero-title">¿Qué querés resolver?</h3>
      <p class="chat-hero-sub">Empezá con un mensaje, un archivo o una de estas ideas.</p>
      <div class="chat-starter-grid">
        <button type="button" class="chat-starter" onclick="fillChatStarter('Analizá el documento adjunto, resumí sus puntos clave y extraé los datos más importantes.')">
          <div class="starter-icon-box">${icon('file')}</div>
          <div class="starter-content">
            <b>Analizar documentos y datos</b>
            <span>Resumí un PDF o extraé datos de una planilla.</span>
          </div>
        </button>
        <button type="button" class="chat-starter" onclick="fillChatStarter('Inspeccioná la imagen o captura adjunta y explicame qué muestra o qué problema visual detectás.')">
          <div class="starter-icon-box">${icon('image')}</div>
          <div class="starter-content">
            <b>Inspeccionar fotos o capturas</b>
            <span>Revisá una captura, un diagrama o un diseño.</span>
          </div>
        </button>
        <button type="button" class="chat-starter" onclick="fillChatStarter('Escribí un script limpio, tipado y modular en Python con tests unitarios para: ')">
          <div class="starter-icon-box">${icon('code')}</div>
          <div class="starter-content">
            <b>Programar código y tests</b>
            <span>Prepará un script y sus pruebas.</span>
          </div>
        </button>
        <button type="button" class="chat-starter" onclick="fillChatStarter('Revisá este archivo multimedia o log y ayudame a documentar o procesar su contenido.')">
          <div class="starter-icon-box">${icon('activity')}</div>
          <div class="starter-content">
            <b>Diagnóstico y multimedia</b>
            <span>Revisá un log, un audio o un video.</span>
          </div>
        </button>
      </div>
    </div>`;
    return;
  }
  const scroll=box.closest('.chat-scroll-area');
  const nearBottom=scrollBottom||scroll.scrollHeight-scroll.scrollTop-scroll.clientHeight<90;
  box.innerHTML=msgs.map((m,i)=>{
    const isUser=m.role==='user';
    const roleLabel=isUser?`<span class="chat-msg-role user"><span class="chat-avatar-pill user">${icon('user')} Vos</span></span>`:`<span class="chat-msg-role assistant"><span class="chat-avatar-pill assistant">${icon('cpu')} Asistente</span></span>`;
    const timeStr=m.created_at?new Date(m.created_at*1000).toLocaleTimeString('es-AR',{hour:'2-digit',minute:'2-digit'}):'';
    const tele=m.measurement;
    const native=tele?.measurement_kind==='generation';
    const tpsBadge=tele&&tele.tps>0?`<span class="tps-pill" title="${native?'Velocidad de generación informada por el motor':'Promedio de la solicitud, incluida la espera'}">${icon('activity')} ${fmt(tele.tps)} TPS ${native?'de generación':'promedio'} · ${fmt(tele.tokens)} tokens</span>`:'';
    const atts=(m.attachments||[]).length?`<div class="chat-att-grid">${m.attachments.map(renderAttachmentCard).join('')}</div>`:'';
    const waiting=m.thinking?'El modelo está razonando…':'Esperando respuesta del modelo…';
    const body=m.content?`<div class="chat-msg-body">${renderMarkdown(m.status==='error'?m.content.replace(/^\u26a0\uFE0F?\s*/,''):m.content,i)}</div>`:(m.status==='running'?`<div class="chat-msg-body muted"><i class="pulse"></i> ${waiting}</div>`:'');
    return `<article class="chat-msg ${esc(m.role)}"><div class="chat-msg-head">${roleLabel}<div class="chat-msg-meta">${tpsBadge}<span class="chat-time-tag">${m.status==='running'?'Generando…':timeStr}</span></div></div>${atts}${body}<div class="chat-msg-foot"><button type="button" class="chat-foot-btn" onclick="copyChatMessage(${i})">${icon('copy')}<span>Copiar</span></button>${!isUser?`<button type="button" class="chat-foot-btn" onclick="downloadChatMessage(${i})">${icon('download')}<span>Descargar .md</span></button>`:''}</div></article>`;
  }).join('');
  if(nearBottom)scroll.scrollTop=scroll.scrollHeight;
}

function autoGrowChatInput(t){
  if(!t)return;
  t.style.height='auto';
  t.style.height=Math.min(t.scrollHeight,180)+'px';
}

function fillChatStarter(text){
  const input=el('chat-input');
  if(!input)return;
  input.value=text;
  editChatDraft(input);
  input.focus();
}

async function copyChatMessage(idx){
  const m=chatState.messages?.[idx];
  if(!m)return;
  try{await navigator.clipboard.writeText(m.content||'');toast('Mensaje copiado.');}
  catch{toast('No se pudo copiar.',true);}
}

function downloadChatMessage(idx){
  const m=chatState.messages?.[idx];
  if(!m)return;
  downloadBlob(m.content||'',`respuesta-${idx+1}.md`,'text/markdown;charset=utf-8');
}

function downloadChatMarkdown(){
  const conv=chatState.conversation;
  const msgs=chatState.messages||[];
  if(!conv||!msgs.length){toast('Todavía no hay mensajes para descargar.',true);return;}
  const lines=[`# ${conv.title}`,`- Cuenta: ${conv.account}`,`- Fecha: ${new Date().toLocaleString('es-AR')}`,''];
  if(conv.system_prompt)lines.push('## Instrucción de sistema',conv.system_prompt,'');
  for(const m of msgs){
    lines.push(`### ${m.role==='user'?'Usuario':'Asistente'}`);
    if(m.content)lines.push(m.content);
    for(const a of m.attachments||[])lines.push(`- Adjunto: ${a.name} (${a.summary})`);
    lines.push('');
  }
  const safe=(conv.title||'conversacion').toLowerCase().replace(/[^a-z0-9_-]+/g,'-').slice(0,40)||'chat';
  downloadBlob(lines.join('\n'),`${safe}.md`,'text/markdown;charset=utf-8');
}

async function exportChatZip(){
  if(!activeChatId){toast('Seleccioná una conversación primero.',true);return;}
  try{
    const d=await post('/api/chat/export',{id:activeChatId});
    const a=document.createElement('a');
    a.href='/api/download/'+encodeURIComponent(d.download.id);
    a.download=d.download.filename;
    document.body.appendChild(a);a.click();a.remove();
    toast('Descargando ZIP con conversación y archivos adjuntos.');
  }catch(e){toast(e.message,true);}
}

function handleChatKey(e){
  if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing&&matchMedia('(pointer:fine)').matches){
    e.preventDefault();
    sendChatMessage();
  }
}

async function sendChatMessage(){
  if(el('chat-send-btn').disabled||sendingChatMessage)return;
  const input=el('chat-input');
  const draft=input.value;
  const content=draft.trim();
  if(!content&&!pendingAttachments.length){
    toast('Escribí un mensaje o adjuntá al menos un archivo.',true);
    return;
  }
  sendingChatMessage=true;
  renderChatHeaderStatus();
  try{
    if(!activeChatId)await createChatConversation();
    const conversation=activeChatId;
    if(!conversation)return;
    const res=await post('/api/chat/send',{
      conversation,
      account:chatState.conversation.account,
      content,
      attachments:pendingAttachments.map(a=>a.id),
      temperature:Number(el('chat-temperature')?.value||0.2),
      reasoning_effort:localStorage.getItem('chat-reasoning-effort')||undefined,
      max_tokens:Number(el('chat-max-tokens')?.value||4096)
    });
    if(chatDrafts.get(conversation)===draft)storeChatDraft(conversation,'');
    activeRequestId=res.request_id;
    chatRequestConversation=conversation;
    if(activeChatId===conversation){
      if(input.value===draft){input.value='';storeChatDraft(conversation,'');}
      autoGrowChatInput(input);
      pendingAttachments=[];
      renderPendingFiles();
      await selectChatConversation(conversation);
    }
    pollChatRequest(res.request_id,res.assistant_message_id);
    await loadChatConversations();
  }catch(e){
    toast(e.message,true);
  }finally{
    sendingChatMessage=false;
    renderChatHeaderStatus();
  }
}

async function pollChatRequest(reqId,asstMsgId){
  clearTimeout(chatPollTimer);
  try{
    const r=await fetch('/api/chat/requests/'+encodeURIComponent(reqId),{cache:'no-store'});
    if(r.status===401){location.replace('/login?expired=1');return;}
    if(!r.ok&&r.status!==404)throw Error('No se pudo actualizar la respuesta.');
    const st=r.ok?await r.json():{status:'interrupted',error:'La solicitud ya no está disponible.'};
    const msg=chatState.messages?.find(m=>m.id===asstMsgId);
    const content=st.content||(st.error?'No se completó la respuesta: '+st.error:'');
    if(msg&&(msg.content!==content||msg.status!==st.status||Boolean(msg.thinking)!==Boolean(st.thinking))){
      msg.content=content;
      msg.status=st.status;
      msg.thinking=st.thinking;
      if(st.status==='done'&&st.measurement_kind)msg.measurement=st;
      renderChatMessages();
    }
    if(st.status==='running'){
      chatPollTimer=setTimeout(()=>pollChatRequest(reqId,asstMsgId),400);
      return;
    }
  }catch(e){
    chatPollTimer=setTimeout(()=>pollChatRequest(reqId,asstMsgId),2500);
    return;
  }
  const finishedConversation=chatRequestConversation;
  activeRequestId=null;
  chatRequestConversation=null;
  renderChatHeaderStatus();
  if(activeChatId===finishedConversation)await selectChatConversation(activeChatId);
  await loadChatConversations();
}

async function cancelChatGeneration(){
  if(!activeRequestId)return;
  try{
    await post('/api/chat/cancel',{request_id:activeRequestId});
    toast('Cancelado en el panel; se solicitó cerrar la conexión. Esto no apaga Kaggle.');
  }catch(e){toast(e.message,true);}
}

function showChatContext(context){if(!el('chat-context-status'))return;if(!context){el('chat-context-status').textContent='';return;}el('chat-context-status').textContent=`Contexto: ${fmt(context.estimated_upper_tokens)} estimados de ${fmt(context.budget)} disponibles. ${context.omitted_messages?context.omitted_messages+' mensajes antiguos fuera del envío; historial completo guardado.':''}${context.extractive_memory?' Se incluyó memoria extractiva parcial.':''}`;}
async function loadChatStorage(){try{const r=await fetch('/api/chat/storage',{cache:'no-store'});if(!r.ok)throw Error('No se pudo consultar almacenamiento.');const d=await r.json(),s=d.storage;el('chat-storage-status').textContent=`${(s.used_bytes/1048576).toFixed(1)} MB de ${s.max_bytes/1048576} MB. Video por fotogramas: ${d.media.video_frames?'disponible':'sin configurar'}. Transcripción de audio: ${d.media.audio_transcription?'modelo local disponible':'sin configurar'}.`;el('chat-storage-mb').value=s.max_bytes/1048576;el('chat-retention-days').value=s.retention_days;html('chat-archive-list',[...d.archived.conversations.map(c=>`<div class="setting-row"><span>${esc(c.title)}</span><button onclick="restoreChatItem('conversation','${esc(c.id)}')">Restaurar conversación</button></div>`),...d.archived.attachments.map(a=>`<div class="setting-row"><span>${esc(a.name)}</span><button onclick="restoreChatItem('attachment','${esc(a.id)}')">Restaurar adjunto</button></div>`)].join('')||'<p class="hint">No hay elementos archivados.</p>');}catch(e){el('chat-storage-status').textContent=e.message;}}
async function saveChatStorage(){try{await post('/api/chat/storage',{maximum_mb:Number(el('chat-storage-mb').value),retention_days:Number(el('chat-retention-days').value)});await loadChatStorage();toast('Política de almacenamiento guardada.');}catch(e){toast(e.message,true);}}
async function archiveOldChatUploads(){try{const r=await post('/api/chat/retention',{});toast(r.notice);await loadChatStorage();}catch(e){toast(e.message,true);}}
async function restoreChatItem(kind,id){try{await post('/api/chat/restore',{kind,id});await loadChatStorage();await loadChatConversations();toast('Elemento restaurado.');}catch(e){toast(e.message,true);}}
function attachmentPreviewError(media){
  const card=media.closest('.chat-att-card');if(!card||card.querySelector('.preview-error'))return;
  const notice=document.createElement('p');notice.className='preview-error';notice.setAttribute('role','status');notice.textContent='No se pudo mostrar la vista previa. Si tu sesión terminó, volvé a ingresar; también podés descargar el original.';
  media.insertAdjacentElement('afterend',notice);
}
