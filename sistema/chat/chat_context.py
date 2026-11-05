"""Conservative context packing; original messages remain untouched in SQLite."""
import copy,json

def cost(message):
    content=message.get('content','')
    if isinstance(content,str):return len(content.encode('utf8'))+32
    return 32+sum(len(p.get('text','').encode('utf8')) if p.get('type')=='text' else 8192 for p in content)

def pack_context(messages,context,output):
    budget=int(context)-int(output)-2048
    if budget<1024:raise ValueError('El contexto no deja espacio suficiente para entrada y respuesta.')
    systems=[copy.deepcopy(m) for m in messages if m['role']=='system']
    history=[copy.deepcopy(m) for m in messages if m['role']!='system']
    if not history:raise ValueError('No hay un mensaje para enviar.')
    fixed=sum(cost(m) for m in systems)
    if fixed+cost(history[-1])>budget:
        raise ValueError('El mensaje y sus adjuntos exceden el presupuesto conservador de contexto. Reducí archivos o texto, o elegí un perfil de contexto mayor. El historial se conserva.')
    kept=[];used=fixed
    for message in reversed(history):
        if used+cost(message)>budget:break
        kept.insert(0,message);used+=cost(message)
    omitted=len(history)-len(kept)
    # Preserve a bounded, explicitly extractive memory only when it fits.
    memory=''
    if omitted:
        fragments=[]
        for message in history[:omitted][-12:]:
            content=message['content']
            text=content if isinstance(content,str) else ' '.join(p.get('text','') for p in content if p.get('type')=='text')
            fragments.append(message['role']+': '+text[:180])
        memory='Memoria extractiva parcial de mensajes anteriores (fragmentos, no un resumen completo):\n'+'\n'.join(fragments)
        summary={'role':'system','content':memory}
        if used+cost(summary)<=budget:systems.append(summary);used+=cost(summary)
        else:memory=''
    result=systems+kept
    if len(json.dumps(result,ensure_ascii=False).encode('utf8'))>24*1024*1024:raise ValueError('Los adjuntos visuales exceden el tamaño de entrada permitido.')
    return result,{'budget':budget,'estimated_upper_tokens':used,'included_messages':len(kept),'omitted_messages':omitted,'extractive_memory':bool(memory),'method':'Cota conservadora UTF-8; imágenes estimadas a 8192 tokens. No es conteo exacto del tokenizer del modelo.'}
