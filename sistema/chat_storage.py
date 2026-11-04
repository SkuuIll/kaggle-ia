"""Bounded storage policies; retention archives metadata and never deletes history."""
import json,shutil,time

DEFAULT={'max_bytes':512*1024*1024,'retention_days':30,'min_free_bytes':256*1024*1024}

def policy(store):
    with store._conn() as db:
        db.execute('CREATE TABLE IF NOT EXISTS chat_settings(id INTEGER PRIMARY KEY CHECK(id=1),payload TEXT NOT NULL)')
        row=db.execute('SELECT payload FROM chat_settings WHERE id=1').fetchone()
    return {**DEFAULT,**(json.loads(row['payload']) if row else {})}

def save_policy(store,maximum_mb,retention_days):
    maximum_mb=int(maximum_mb);retention_days=int(retention_days)
    if not 64<=maximum_mb<=4096 or not 1<=retention_days<=365:raise ValueError('Cuota de 64 a 4096 MB y retención de 1 a 365 días.')
    value={**DEFAULT,'max_bytes':maximum_mb*1024*1024,'retention_days':retention_days}
    with store._conn() as db:
        db.execute('CREATE TABLE IF NOT EXISTS chat_settings(id INTEGER PRIMARY KEY CHECK(id=1),payload TEXT NOT NULL)')
        db.execute('INSERT OR REPLACE INTO chat_settings VALUES(1,?)',(json.dumps(value),))
    return value

def storage_status(store):
    value=policy(store)
    used=sum(p.stat().st_size for p in store.files_dir.iterdir() if p.is_file())
    used+=sum(p.stat().st_size for p in store.private.glob('chat.sqlite*') if p.is_file())
    with store._conn() as db:
        archived=db.execute('SELECT COUNT(*) FROM conversations WHERE archived=1').fetchone()[0]
        pending=db.execute('SELECT COUNT(*) FROM attachments WHERE message_id IS NULL AND archived=0').fetchone()[0]
        reserved=sum(json.loads(r['payload']).get('reserved_bytes',0) for r in db.execute("SELECT payload FROM chat_requests WHERE status='running'"))
    return {**value,'used_bytes':used,'available_bytes':max(0,value['max_bytes']-used),'disk_free_bytes':shutil.disk_usage(store.private).free,'archived_conversations':archived,'pending_attachments':pending,'reserved_bytes':reserved}

def check_capacity(store,required):
    state=storage_status(store)
    if state['used_bytes']+state['reserved_bytes']+required>state['max_bytes']:raise ValueError('La cuota del chat no alcanza para esta operación. El historial se conserva; revisá almacenamiento.')
    if state['disk_free_bytes']-state['reserved_bytes']-required<state['min_free_bytes']:raise ValueError('El servidor necesita conservar espacio libre. No se modificó el historial.')

def check_upload(store,raw_size):
    state=storage_status(store)
    # Original file + base64 in SQLite + transaction overhead.
    required=int(raw_size)*3+65536
    check_capacity(store,required)
    if state['used_bytes']+required>state['max_bytes']:raise ValueError('La cuota de almacenamiento del chat no alcanza para este adjunto. Revisá Almacenamiento antes de continuar; no se borró contenido.')
    if state['disk_free_bytes']-required<state['min_free_bytes']:raise ValueError('El servidor debe conservar espacio libre. La subida se rechazó sin borrar conversaciones.')

def archived_items(store):
    with store._conn() as db:
        conversations=[dict(r) for r in db.execute('SELECT id,title,updated_at FROM conversations WHERE archived=1 ORDER BY updated_at DESC LIMIT 100')]
        attachments=[dict(r) for r in db.execute('SELECT id,conversation_id,name,size,created_at FROM attachments WHERE archived=1 ORDER BY created_at DESC LIMIT 100')]
    return {'conversations':conversations,'attachments':attachments}

def archive_stale(store):
    days=policy(store)['retention_days'];cutoff=time.time()-days*86400
    with store._conn() as db:
        count=db.execute('UPDATE attachments SET archived=1 WHERE message_id IS NULL AND archived=0 AND created_at<?',(cutoff,)).rowcount
    return {'archived_attachments':count,'notice':'Los pendientes antiguos se archivaron de forma recuperable. Archivar no libera espacio ni elimina archivos.'}

def restore(store,kind,identifier):
    if kind not in ('conversation','attachment'):raise ValueError('Tipo no permitido.')
    table='conversations' if kind=='conversation' else 'attachments'
    with store._conn() as db:
        cursor=db.execute('UPDATE '+table+' SET archived=0 WHERE id=? AND archived=1',(identifier,))
        if not cursor.rowcount:raise ValueError('Elemento archivado no encontrado.')
    return {'ok':True}
