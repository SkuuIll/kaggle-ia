"""Private integrated chat store, media extractor, and streaming runner."""
import base64,codecs,io,json,math,mimetypes,os,re,sqlite3,struct,threading,time,uuid,zipfile,zlib
from contextlib import contextmanager
from pathlib import Path
import xml.etree.ElementTree as ET
import requests
from chat_context import pack_context

MAX_FILE_BYTES=15*1024*1024
MAX_TOTAL_BYTES=30*1024*1024
MAX_FILES_PER_MESSAGE=8
MAX_PIXELS=16_000_000
MAX_TEXT=60_000

TEXT_EXTENSIONS=frozenset('.txt .md .csv .tsv .json .jsonl .yaml .yml .toml .ini .cfg .log .py .js .jsx .ts .tsx .html .css .scss .sql .sh .ps1 .bat .c .cpp .h .hpp .cs .java .kt .rs .go .rb .php .xml .svg .tex .rst .srt .vtt .env.example'.split())
IMAGE_EXTENSIONS={'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.gif':'image/gif'}
VIDEO_EXTENSIONS={'.mp4':'video/mp4','.webm':'video/webm','.mov':'video/quicktime','.mkv':'video/x-matroska','.avi':'video/x-msvideo'}
AUDIO_EXTENSIONS={'.mp3':'audio/mpeg','.wav':'audio/wav','.ogg':'audio/ogg','.m4a':'audio/mp4','.flac':'audio/flac'}
OFFICE_EXTENSIONS={'.docx','.xlsx','.pptx','.odt'}

def safe_filename(name):
    cleaned=re.sub(r'[^\w.\- ()áéíóúÁÉÍÓÚñÑ]','_',Path(name or 'archivo').name).strip(' .')
    return (cleaned or 'archivo')[:120]

def _image_dimensions(raw,suffix):
    if raw.startswith(b'\x89PNG\r\n\x1a\n') and len(raw)>=24:
        w,h=struct.unpack('>II',raw[16:24])
        return 'PNG','image/png',w,h
    if raw.startswith((b'GIF87a',b'GIF89a')) and len(raw)>=10:
        w,h=struct.unpack('<HH',raw[6:10])
        return 'GIF','image/gif',w,h
    if raw.startswith(b'RIFF') and raw[8:12]==b'WEBP' and len(raw)>=30:
        chunk=raw[12:16]
        if chunk==b'VP8 ' and len(raw)>=30:
            w,h=struct.unpack('<HH',raw[26:30])
            return 'WEBP','image/webp',w&0x3fff,h&0x3fff
        if chunk==b'VP8L' and len(raw)>=25:
            b0,b1,b2,b3=raw[21:25]
            w=1+(((b1&0x3f)<<8)|b0);h=1+(((b3&0x0f)<<10)|(b2<<2)|((b1&0xc0)>>6))
            return 'WEBP','image/webp',w,h
        if chunk==b'VP8X' and len(raw)>=30:
            w=1+int.from_bytes(raw[24:27],'little');h=1+int.from_bytes(raw[27:30],'little')
            return 'WEBP','image/webp',w,h
    if raw.startswith(b'\xff\xd8'):
        idx=2;n=len(raw)
        while idx+9<n:
            if raw[idx]!=0xff:idx+=1;continue
            marker=raw[idx+1]
            while marker==0xff and idx+2<n:idx+=1;marker=raw[idx+1]
            if marker in (0xd8,0xd9) or 0xd0<=marker<=0xd7:idx+=2;continue
            if idx+4>n:break
            length=struct.unpack('>H',raw[idx+2:idx+4])[0]
            if length<2 or idx+2+length>n:break
            if marker in (0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf) and idx+9<=n:
                h,w=struct.unpack('>HH',raw[idx+5:idx+9])
                return 'JPEG','image/jpeg',w,h
            idx+=2+length
    raise ValueError('Formato de imagen no válido o dañado. Usá PNG, JPEG, WebP o GIF.')

def _mp4_duration(raw):
    idx=0;n=len(raw)
    while idx+8<=n:
        size,box=struct.unpack('>I4s',raw[idx:idx+8])
        if size<8:break
        if box==b'moov':
            sub=idx+8;end=min(n,idx+size)
            while sub+8<=end:
                ssize,sbox=struct.unpack('>I4s',raw[sub:sub+8])
                if ssize<8:break
                if sbox==b'mvhd' and sub+28<=end:
                    version=raw[sub+8]
                    if version==0 and sub+28<=end:
                        scale,dur=struct.unpack('>II',raw[sub+20:sub+28])
                        if scale:return round(dur/scale,2)
                    elif version==1 and sub+36<=end:
                        scale,dur=struct.unpack('>IQ',raw[sub+28:sub+36])
                        if scale:return round(dur/scale,2)
                sub+=ssize
        idx+=size
    return None

def _extract_office_xml(path,suffix):
    texts=[]
    with zipfile.ZipFile(path) as z:
        entries=z.infolist()
        if len(entries)>2000 or sum(entry.file_size for entry in entries)>32*1024*1024:
            raise ValueError('El documento comprimido supera el límite de extracción.')
        names=z.namelist()
        targets=[]
        if suffix=='.docx':targets=[n for n in names if n=='word/document.xml']
        elif suffix=='.pptx':targets=sorted(n for n in names if n.startswith('ppt/slides/slide') and n.endswith('.xml'))
        elif suffix=='.xlsx':targets=[n for n in names if n=='xl/sharedStrings.xml' or n.startswith('xl/worksheets/sheet')]
        elif suffix=='.odt':targets=[n for n in names if n=='content.xml']
        for target in targets[:50]:
            if z.getinfo(target).file_size>4*1024*1024:raise ValueError('Una sección del documento supera el límite de extracción.')
            root=ET.fromstring(z.read(target))
            chunk=' '.join(t.strip() for t in root.itertext() if t and t.strip())
            if chunk:texts.append(chunk)
    return '\n\n'.join(texts)[:MAX_TEXT]

def _extract_pdf_text(path):
    try:
        from pypdf import PdfReader
        reader=PdfReader(str(path))
        if reader.is_encrypted:raise ValueError('El PDF está protegido con contraseña.')
        out=[]
        for page in reader.pages[:80]:
            txt=page.extract_text() or ''
            if txt.strip():out.append(txt.strip())
            if sum(len(x) for x in out)>=MAX_TEXT:break
        return '\n\n'.join(out)[:MAX_TEXT]
    except ImportError:
        pass
    raw=Path(path).read_bytes()
    if not raw.startswith(b'%PDF'):raise ValueError('Archivo PDF inválido.')
    chunks=[]
    for match in re.finditer(rb'stream\r?\n(.*?)\r?\nendstream',raw,re.DOTALL):
        stream=match.group(1)
        for candidate in (stream,):
            try:stream=zlib.decompress(candidate)
            except Exception:pass
        for token in re.findall(rb'\(([^()\\]*(?:\\.[^()\\]*)*)\)\s*Tj',stream):
            cleaned=re.sub(rb'\\([()\\])',rb'\1',token).decode('latin1',errors='ignore').strip()
            if cleaned:chunks.append(cleaned)
        for array in re.findall(rb'\[(.*?)\]\s*TJ',stream,re.DOTALL):
            parts=[re.sub(rb'\\([()\\])',rb'\1',p).decode('latin1',errors='ignore') for p in re.findall(rb'\(([^()\\]*(?:\\.[^()\\]*)*)\)',array)]
            joined=''.join(parts).strip()
            if joined:chunks.append(joined)
        if sum(len(x) for x in chunks)>=MAX_TEXT:break
    return ' '.join(chunks)[:MAX_TEXT]

def extract_attachment(path,mime,name):
    path=Path(path).resolve()
    size=path.stat().st_size if path.is_file() else 0
    if not path.is_file() or size<=0 or size>MAX_FILE_BYTES:
        raise ValueError('El archivo está vacío o supera el límite de 15 MB por adjunto.')
    suffix=Path(name).suffix.lower()
    mime=(mime or '').split(';',1)[0].strip().lower() or mimetypes.guess_type(name)[0] or 'application/octet-stream'
    if suffix in IMAGE_EXTENSIONS or (mime in IMAGE_EXTENSIONS.values() and suffix!='.svg'):
        raw=path.read_bytes()
        fmt,real_mime,w,h=_image_dimensions(raw,suffix)
        if w*h>MAX_PIXELS:raise ValueError('La imagen supera el límite de 16 megapíxeles.')
        b64='data:'+real_mime+';base64,'+base64.b64encode(raw).decode('ascii')
        return {'kind':'image','mime':real_mime,'text':'','image_url':b64,
                'summary':f'Imagen {fmt} ({w}×{h} px, {max(1,size//1024)} KB)'}
    if suffix in VIDEO_EXTENSIONS or mime.startswith('video/'):
        raw=path.read_bytes()[:512*1024]
        dur=_mp4_duration(raw) if suffix in ('.mp4','.mov') or 'mp4' in mime else None
        real_mime=VIDEO_EXTENSIONS.get(suffix,mime if mime.startswith('video/') else 'video/mp4')
        dur_txt=f', duración {dur}s' if dur else ''
        return {'kind':'video','mime':real_mime,'text':'','image_url':None,
                'summary':f'Video adjunto ({Path(name).suffix.upper().lstrip(".") or "VIDEO"}, {max(1,size//1024)} KB{dur_txt}). Reproducible y descargable en el chat.'}
    if suffix in AUDIO_EXTENSIONS or mime.startswith('audio/'):
        real_mime=AUDIO_EXTENSIONS.get(suffix,mime if mime.startswith('audio/') else 'audio/mpeg')
        return {'kind':'audio','mime':real_mime,'text':'','image_url':None,
                'summary':f'Audio adjunto ({Path(name).suffix.upper().lstrip(".") or "AUDIO"}, {max(1,size//1024)} KB). Reproducible y descargable en el chat.'}
    if suffix=='.pdf' or mime=='application/pdf':
        text=_extract_pdf_text(path)
        note=f'Documento PDF ({len(text)} caracteres extraídos).' if text else 'PDF adjunto (sin capa de texto extraíble; disponible para descarga).'
        return {'kind':'document','mime':'application/pdf','text':text,'image_url':None,'summary':note}
    if suffix in OFFICE_EXTENSIONS:
        try:text=_extract_office_xml(path,suffix)
        except Exception as exc:raise ValueError('No se pudo leer el documento Office adjunto.') from exc
        return {'kind':'document','mime':mime,'text':text,'image_url':None,
                'summary':f'Documento {suffix.upper().lstrip(".")} ({len(text)} caracteres extraídos).'}
    if suffix in TEXT_EXTENSIONS or mime.startswith('text/') or mime in ('application/json','application/xml','application/javascript'):
        raw=path.read_bytes()[:MAX_TEXT*4+4]
        try:text=codecs.getincrementaldecoder('utf-8-sig')('strict').decode(raw,final=len(raw)<=MAX_TEXT*4)
        except UnicodeDecodeError:
            text=raw.decode('latin1',errors='replace')
        if '\x00' in text[:4096]:raise ValueError('El archivo parece binario y no puede leerse como texto.')
        text=text[:MAX_TEXT]
        return {'kind':'code' if suffix in {'.py','.js','.ts','.tsx','.jsx','.html','.css','.sql','.sh','.ps1','.c','.cpp','.h','.java','.kt','.rs','.go','.json','.yaml','.yml'} else 'document',
                'mime':'text/plain' if mime=='application/octet-stream' else mime,
                'text':text,'image_url':None,'summary':f'Texto/código extraído ({len(text)} caracteres).'}
    return {'kind':'file','mime':mime,'text':'','image_url':None,
            'summary':f'Archivo binario adjunto ({max(1,size//1024)} KB). Disponible para descarga.'}

class ChatStore:
    def __init__(self,base_dir):
        self.base=Path(base_dir).resolve()
        self.private=self.base/'.private';self.private.mkdir(parents=True,exist_ok=True)
        self.files_dir=self.private/'chat-files';self.files_dir.mkdir(parents=True,exist_ok=True)
        self.db_path=self.private/'chat.sqlite'
        self.lock=threading.Lock()
        self.requests={}
        self.upload_lock=threading.Lock()
        self.send_lock=threading.Lock()
        with self._conn() as db:
            db.execute('CREATE TABLE IF NOT EXISTS conversations (id TEXT PRIMARY KEY, title TEXT NOT NULL, account TEXT NOT NULL, system_prompt TEXT NOT NULL DEFAULT "", created_at REAL NOT NULL, updated_at REAL NOT NULL, archived INTEGER NOT NULL DEFAULT 0)')
            db.execute('CREATE TABLE IF NOT EXISTS messages (id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, status TEXT NOT NULL DEFAULT "done", created_at REAL NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS attachments (id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, message_id TEXT, name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL, kind TEXT NOT NULL, summary TEXT NOT NULL, extracted_text TEXT NOT NULL DEFAULT "", image_url TEXT, disk_name TEXT NOT NULL, created_at REAL NOT NULL)')
            if 'archived' not in {r[1] for r in db.execute('PRAGMA table_info(attachments)')}:db.execute('ALTER TABLE attachments ADD COLUMN archived INTEGER NOT NULL DEFAULT 0')
            db.execute('CREATE TABLE IF NOT EXISTS chat_requests (id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, message_id TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, updated_at REAL NOT NULL)')
            stale=list(db.execute("SELECT id,message_id,payload FROM chat_requests WHERE status='running'"))
            for row in stale:
                state=json.loads(row['payload']);state['status']='interrupted';state['error']='El panel se reinició. Se conserva la respuesta parcial; podés enviar un nuevo mensaje.'
                db.execute('UPDATE chat_requests SET status=?,payload=?,updated_at=? WHERE id=?',('interrupted',json.dumps(state,ensure_ascii=False),time.time(),row['id']))
                db.execute("UPDATE messages SET status='interrupted' WHERE id=?",(row['message_id'],))
            db.execute("UPDATE messages SET status='interrupted' WHERE status='running'")
            db.execute('CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, created_at)')
            db.execute('CREATE INDEX IF NOT EXISTS idx_attachments_conv ON attachments(conversation_id)')

    @contextmanager
    def _conn(self):
        conn=sqlite3.connect(self.db_path,timeout=10)
        conn.row_factory=sqlite3.Row
        try:
            with conn:yield conn
        finally:conn.close()

    def limits(self):
        return {'file_bytes':MAX_FILE_BYTES,'total_bytes':MAX_TOTAL_BYTES,'files_per_message':MAX_FILES_PER_MESSAGE}

    def list_conversations(self):
        with self._conn() as db:
            rows=db.execute('SELECT c.id, c.title, c.account, c.system_prompt, c.created_at, c.updated_at, (SELECT COUNT(*) FROM messages m WHERE m.conversation_id=c.id) AS message_count FROM conversations c WHERE c.archived=0 ORDER BY c.updated_at DESC LIMIT 100').fetchall()
        return [dict(r) for r in rows]

    def create_conversation(self,account,title='',system_prompt=''):
        from chat_storage import check_capacity
        check_capacity(self,32768)
        now=time.time();cid=uuid.uuid4().hex[:16]
        clean_title=(title or '').strip()[:80] or 'Nueva conversación'
        clean_prompt=(system_prompt or '').strip()[:8000]
        with self._conn() as db:
            db.execute('INSERT INTO conversations(id,title,account,system_prompt,created_at,updated_at,archived) VALUES(?,?,?,?,?,?,0)',(cid,clean_title,account,clean_prompt,now,now))
        return {'id':cid,'title':clean_title,'account':account,'system_prompt':clean_prompt,'created_at':now,'updated_at':now,'message_count':0}

    def get_conversation(self,cid):
        with self._conn() as db:
            conv=db.execute('SELECT id,title,account,system_prompt,created_at,updated_at FROM conversations WHERE id=? AND archived=0',(cid,)).fetchone()
            if not conv:raise ValueError('Conversación no encontrada.')
            msgs=db.execute('SELECT id,role,content,status,created_at FROM messages WHERE conversation_id=? ORDER BY created_at ASC',(cid,)).fetchall()
            atts=db.execute('SELECT id,message_id,name,mime,size,kind,summary,created_at FROM attachments WHERE conversation_id=? ORDER BY created_at ASC',(cid,)).fetchall()
            measurements={
                row['message_id']:{'tps':row['tps'],'tokens':row['tokens'],'elapsed':row['elapsed']}
                for row in db.execute("""
                    SELECT message_id, json_extract(payload,'$.tps') AS tps,
                           json_extract(payload,'$.tokens') AS tokens,
                           json_extract(payload,'$.elapsed') AS elapsed
                    FROM chat_requests WHERE conversation_id=? AND status='done'
                    AND json_extract(payload,'$.measurement_kind')='request'
                """,(cid,))
            }
        by_msg={}
        for a in atts:
            if a['message_id']:by_msg.setdefault(a['message_id'],[]).append(dict(a))
        messages=[]
        for m in msgs:
            item=dict(m);item['attachments']=by_msg.get(m['id'],[])
            if m['id'] in measurements:item['measurement']=measurements[m['id']]
            messages.append(item)
        with self._conn() as db:latest=db.execute('SELECT payload FROM chat_requests WHERE conversation_id=? ORDER BY updated_at DESC LIMIT 1',(cid,)).fetchone()
        pending=[dict(a) for a in atts if a['message_id'] is None and not self._attachment_archived(a['id'])]
        return {'conversation':dict(conv),'messages':messages,'pending_attachments':pending,'latest_request':json.loads(latest['payload']) if latest else None}

    def _attachment_archived(self,identifier):
        with self._conn() as db:return bool(db.execute('SELECT archived FROM attachments WHERE id=?',(identifier,)).fetchone()[0])

    def update_conversation(self,cid,title=None,system_prompt=None,account=None):
        from chat_storage import check_capacity
        check_capacity(self,32768)
        with self._conn() as db:
            conv=db.execute('SELECT id,title,account,system_prompt FROM conversations WHERE id=? AND archived=0',(cid,)).fetchone()
            if not conv:raise ValueError('Conversación no encontrada.')
            new_title=conv['title'] if title is None else (str(title).strip()[:80] or conv['title'])
            new_prompt=conv['system_prompt'] if system_prompt is None else str(system_prompt).strip()[:8000]
            new_account=conv['account'] if account is None else str(account).strip()
            now=time.time()
            db.execute('UPDATE conversations SET title=?, system_prompt=?, account=?, updated_at=? WHERE id=?',(new_title,new_prompt,new_account,now,cid))
        return {'id':cid,'title':new_title,'system_prompt':new_prompt,'account':new_account,'updated_at':now}

    def archive_conversation(self,cid):
        with self._conn() as db:
            cur=db.execute('UPDATE conversations SET archived=1, updated_at=? WHERE id=? AND archived=0',(time.time(),cid))
            if cur.rowcount==0:raise ValueError('Conversación no encontrada.')
        return {'ok':True}

    def upload_attachment(self,cid,name,mime,b64_data):
        from chat_storage import check_upload
        if not isinstance(b64_data,str) or len(b64_data)>((MAX_FILE_BYTES+2)//3)*4:raise ValueError('Adjunto demasiado grande o inválido.')
        with self.upload_lock:
            check_upload(self,len(b64_data)*3//4)
            return self._upload_attachment(cid,name,mime,b64_data)

    def _upload_attachment(self,cid,name,mime,b64_data):
        with self._conn() as db:
            conv=db.execute('SELECT id FROM conversations WHERE id=? AND archived=0',(cid,)).fetchone()
            if not conv:raise ValueError('Creá o seleccioná una conversación válida antes de subir archivos.')
        if not isinstance(b64_data,str) or not b64_data:raise ValueError('Archivo vacío.')
        raw=base64.b64decode(b64_data,validate=True)
        if len(raw)>MAX_FILE_BYTES:raise ValueError('El archivo supera el límite de 15 MB.')
        clean_name=safe_filename(name)
        att_id=uuid.uuid4().hex[:16]
        disk_name=att_id+'-'+clean_name
        disk_path=(self.files_dir/disk_name).resolve()
        if not disk_path.is_relative_to(self.files_dir):raise ValueError('Ruta de archivo inválida.')
        disk_path.write_bytes(raw)
        try:os.chmod(disk_path,0o600)
        except OSError:pass
        try:
            info=extract_attachment(disk_path,mime,clean_name)
            if info['kind'] in ('video','audio'):
                from chat_media import prepare_media,capabilities
                can_process=capabilities()['video_frames'] if info['kind']=='video' else capabilities()['audio_transcription']
                media=prepare_media(disk_path,info['kind']) if can_process else {'image_urls':[],'text':'','notice':'Archivo guardado y descargable. El procesamiento multimedia no está configurado en este servidor; no se interpretó su contenido.'}
                info['summary']=media['notice'];info['text']=media['text']
                info['image_url']=json.dumps(media['image_urls']) if media['image_urls'] else None
        except Exception:
            disk_path.unlink(missing_ok=True)
            raise
        now=time.time()
        with self._conn() as db:
            db.execute('INSERT INTO attachments(id,conversation_id,message_id,name,mime,size,kind,summary,extracted_text,image_url,disk_name,created_at) VALUES(?,?,NULL,?,?,?,?,?,?,?,?,?)',
                       (att_id,cid,clean_name,info['mime'],len(raw),info['kind'],info['summary'],info['text'],info['image_url'],disk_name,now))
        return {'id':att_id,'name':clean_name,'mime':info['mime'],'size':len(raw),'kind':info['kind'],'summary':info['summary'],'created_at':now}

    def get_attachment_preview(self,att_id):
        with self._conn() as db:
            row=db.execute('SELECT extracted_text FROM attachments WHERE id=?',(att_id,)).fetchone()
        if row is None:raise ValueError('Adjunto no encontrado.')
        return {'text':row['extracted_text'] or ''}

    def get_attachment_file(self,att_id):
        with self._conn() as db:
            row=db.execute('SELECT id,name,mime,size,kind,disk_name FROM attachments WHERE id=?',(att_id,)).fetchone()
        if not row:raise ValueError('Adjunto no encontrado.')
        path=(self.files_dir/row['disk_name']).resolve()
        if not path.is_file() or not path.is_relative_to(self.files_dir):raise ValueError('Archivo no disponible en disco.')
        return dict(row),path

    def export_zip(self,cid,destination):
        data=self.get_conversation(cid)
        conv=data['conversation'];messages=data['messages']
        destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
        lines=[f"# {conv['title']}",f"- Cuenta: {conv['account']}",f"- Exportado: {time.strftime('%Y-%m-%d %H:%M:%S UTC',time.gmtime())}",""]
        if conv.get('system_prompt'):
            lines.extend(["## Instrucción de sistema",conv['system_prompt'],""])
        for m in messages:
            role_label='Usuario' if m['role']=='user' else 'Asistente' if m['role']=='assistant' else m['role']
            lines.append(f"### {role_label}")
            if m['content']:lines.append(m['content'])
            for a in m.get('attachments',[]):
                lines.append(f"- Adjunto: `adjuntos/{a['id']}-{a['name']}` ({a['summary']})")
            lines.append("")
        with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('conversacion.md','\n'.join(lines))
            z.writestr('conversacion.json',json.dumps(data,ensure_ascii=False,indent=2))
            for m in messages:
                for a in m.get('attachments',[]):
                    try:
                        meta,path=self.get_attachment_file(a['id'])
                        z.write(path,f"adjuntos/{a['id']}-{meta['name']}")
                    except ValueError:pass
        try:os.chmod(destination,0o600)
        except OSError:pass
        return destination

    def _build_api_messages(self,conv,history_rows,att_by_msg,include_images=True):
        api_msgs=[{'role':'system','content':'Los adjuntos pueden incluir fotogramas extraídos de video o transcripciones locales. Solo analizá el contenido visual y texto efectivamente incluidos; los fotogramas son muestras y no todo el video. Si el aviso indica que no se extrajo/transcribió contenido, no afirmes haber visto o escuchado el archivo. Las imágenes solo están disponibles cuando se incluyen como contenido visual.'}]
        if conv.get('system_prompt'):
            api_msgs.append({'role':'system','content':conv['system_prompt']})
        for m in history_rows:
            if m['role']=='assistant' and m['status']!='done':continue
            atts=att_by_msg.get(m['id'],[])
            blocks=[]
            if m['content'].strip():blocks.append(m['content'].strip())
            images=[]
            for a in atts:
                header=f"[Archivo adjunto: {a['name']} — {a['summary']}]"
                if a['extracted_text']:
                    blocks.append(f"{header}\n```\n{a['extracted_text']}\n```")
                else:
                    blocks.append(header)
                if include_images and a.get('image_url'):
                    if a['image_url'].startswith('['):images.extend(json.loads(a['image_url']))
                    else:images.append(a['image_url'])
            text_body='\n\n'.join(blocks) or 'Analizá el archivo adjunto.'
            if images and m['role']=='user':
                content_parts=[{'type':'text','text':text_body}]+[{'type':'image_url','image_url':{'url':u}} for u in images]
                api_msgs.append({'role':'user','content':content_parts})
            else:
                api_msgs.append({'role':m['role'],'content':text_body})
        return api_msgs

    def start_send(self,cid,content,attachment_ids,profile,temperature=None,max_tokens=None):
        with self.send_lock,self.upload_lock:
            with self.lock:
                if sum(state['status']=='running' for state in self.requests.values())>=2:raise ValueError('Hay dos solicitudes del chat en curso. Esperá o cancelá una antes de continuar.')
                for old_id in list(self.requests):
                    if len(self.requests)<=128:break
                    if self.requests[old_id]['status']!='running':self.requests.pop(old_id)
            with self._conn() as db:
                if db.execute("SELECT 1 FROM messages WHERE conversation_id=? AND status='running' LIMIT 1",(cid,)).fetchone():raise ValueError('Esta conversación ya tiene una respuesta en curso. Esperá o cancelala.')
            return self._start_send(cid,content,attachment_ids,profile,temperature,max_tokens)

    def _start_send(self,cid,content,attachment_ids,profile,temperature=None,max_tokens=None):
        content=(content or '').strip()
        if len(content)>32000:raise ValueError('El mensaje supera el límite de 32.000 caracteres. Adjuntá el contenido como archivo.')
        temp_val=float(profile.get('temperature',0.2) if temperature is None else temperature)
        max_out=int(profile.get('output_tokens',4096) if max_tokens is None else max_tokens)
        if not math.isfinite(temp_val) or not 0<=temp_val<=2 or not 1<=max_out<=32768:raise ValueError('Temperatura o límite de salida fuera de rango.')
        reserved_bytes=max_out*64+len(content.encode('utf8'))*3+8192
        from chat_storage import check_capacity
        check_capacity(self,reserved_bytes)
        attachment_ids=list(attachment_ids or [])
        if not content and not attachment_ids:
            raise ValueError('Escribí un mensaje o adjuntá al menos un archivo.')
        if len(attachment_ids)>MAX_FILES_PER_MESSAGE:
            raise ValueError('Superaste el máximo de archivos por mensaje.')
        with self._conn() as db:
            conv=db.execute('SELECT id,title,account,system_prompt FROM conversations WHERE id=? AND archived=0',(cid,)).fetchone()
            if not conv:raise ValueError('Conversación no encontrada.')
            if len(set(attachment_ids))!=len(attachment_ids):raise ValueError('No repitas el mismo adjunto.')
            att_rows=[]
            for aid in attachment_ids:
                row=db.execute('SELECT * FROM attachments WHERE id=? AND conversation_id=?',(aid,cid)).fetchone()
                if not row:raise ValueError('Uno de los adjuntos no pertenece a esta conversación.')
                if row['message_id'] or row['archived']:raise ValueError('El adjunto ya fue enviado o está archivado; subilo de nuevo o restauralo.')
                att_rows.append(dict(row))
            if sum(a['size'] for a in att_rows)>MAX_TOTAL_BYTES:raise ValueError('Los adjuntos del mensaje superan 30 MB.')
            now=time.time()
            user_msg_id=uuid.uuid4().hex[:16]
            asst_msg_id=uuid.uuid4().hex[:16]
            new_title=conv['title']
            if conv['title']=='Nueva conversación' and content:
                new_title=re.sub(r'\s+',' ',content)[:56]
            db.execute('INSERT INTO messages(id,conversation_id,role,content,status,created_at) VALUES(?,?,?,?,"done",?)',(user_msg_id,cid,'user',content,now))
            for aid in attachment_ids:
                db.execute('UPDATE attachments SET message_id=? WHERE id=?',(user_msg_id,aid))
            db.execute('INSERT INTO messages(id,conversation_id,role,content,status,created_at) VALUES(?,?,"assistant","","running",?)',(asst_msg_id,cid,now+0.001))
            db.execute('UPDATE conversations SET title=?, updated_at=? WHERE id=?',(new_title,now,cid))
            history_rows=[dict(r) for r in db.execute('SELECT id,role,content,status FROM messages WHERE conversation_id=? AND id!=? ORDER BY created_at ASC',(cid,asst_msg_id)).fetchall()]
            all_atts=[dict(r) for r in db.execute('SELECT id,message_id,name,summary,extracted_text,image_url FROM attachments WHERE conversation_id=? AND message_id IS NOT NULL',(cid,)).fetchall()]
            att_by_msg={}
            for a in all_atts:att_by_msg.setdefault(a['message_id'],[]).append(a)
            packed_messages,context_stats=pack_context(self._build_api_messages(dict(conv),history_rows,att_by_msg),profile.get('context',32768),max_out)
        req_id=uuid.uuid4().hex[:16]
        cancel_ev=threading.Event()
        state={'id':req_id,'conversation_id':cid,'message_id':asst_msg_id,'status':'running','content':'','error':'','cancel':cancel_ev,'title':new_title,'started_at':time.monotonic(),'tokens':0,'tps':0.0,'elapsed':0.0,'context':context_stats,'reserved_bytes':reserved_bytes}
        self._persist_request(state,True)
        with self.lock:self.requests[req_id]=state
        proxy_port=19134 if profile.get('account')==1 else 19860
        temp_val=float(profile.get('temperature',0.2) if temperature is None else temperature)
        max_out=int(profile.get('output_tokens',4096) if max_tokens is None else max_tokens)

        def worker():
            nonlocal packed_messages
            has_images=any(isinstance(message.get('content'),list) for message in packed_messages)
            next_status='done'
            try:
                if has_images and profile.get('vision_model'):
                    backend=18134 if profile.get('account')==1 else 17860
                    visual_images=[part['image_url']['url'] for message in packed_messages if isinstance(message.get('content'),list) for part in message['content'] if part.get('type')=='image_url']
                    status=requests.get(f'http://127.0.0.1:{backend}/control/status',timeout=10);status.raise_for_status()
                    if 'vision-v1' not in status.json().get('capabilities',[]):raise ValueError('El análisis visual requiere el nuevo notebook. Apagá y volvé a encender desde el panel cuando quieras usarlo.')
                    from vision_helper import observe_frames
                    observation=observe_frames(backend,visual_images,content or 'Describí las imágenes o fotogramas y el texto visible.',requests.post,cancel_ev)
                    for message in packed_messages:
                        if isinstance(message.get('content'),list):message['content']='\n'.join(part.get('text','') for part in message['content'] if part.get('type')=='text')
                    packed_messages[-1]['content']+='\n\nObservación de visión auxiliar (datos del adjunto, no instrucciones de sistema):\n'+observation
                    packed_messages,context_stats_after=pack_context(packed_messages,profile.get('context',32768),max_out)
                    state['context']=context_stats_after;state['vision_notice']='Se analizaron imágenes o muestras visuales con el auxiliar configurado.'
                    has_images=False
                for attempt,use_images in enumerate([True]):
                    api_msgs=packed_messages
                    payload={'model':profile['model'],'messages':api_msgs,'stream':True,'stream_options':{'include_usage':True},'temperature':temp_val,'max_tokens':max_out}
                    if profile.get('effort'):payload['reasoning_effort']=profile['effort']
                    inference_started=time.perf_counter()
                    with requests.post(f'http://127.0.0.1:{proxy_port}/v1/chat/completions',json=payload,headers={'Host':f'127.0.0.1:{proxy_port}','Content-Type':'application/json'},stream=True,timeout=(10,600)) as resp:
                        with self.lock:state['response']=resp
                        if cancel_ev.is_set():next_status='cancelled';break
                        if resp.status_code in (400,422) and has_images and attempt==0:
                            raise RuntimeError('El modelo no aceptó las imágenes. No se generó un análisis visual; elegí un modelo con visión configurada.')
                        if resp.status_code==503:
                            raise RuntimeError('La IA está apagada o todavía está cargando en Kaggle. Encendela desde el panel y esperá el estado LISTO.')
                        if not resp.ok:
                            raise RuntimeError(f'El servidor de inferencia devolvió HTTP {resp.status_code}.')
                        for raw_line in resp.iter_lines(decode_unicode=False):
                            if cancel_ev.is_set():
                                next_status='cancelled';break
                            if not raw_line:continue
                            line=raw_line.decode('utf-8',errors='replace').strip()
                            if not line.startswith('data:'):continue
                            data_str=line[5:].strip()
                            if data_str=='[DONE]':break
                            try:chunk=json.loads(data_str)
                            except ValueError:continue
                            usage_obj=chunk.get('usage') or {}
                            choices=chunk.get('choices') or []
                            piece=choices[0].get('delta',{}).get('content') if choices else None
                            tokens=usage_obj.get('completion_tokens')
                            with self.lock:
                                if piece:
                                    if len(state['content'].encode('utf8'))+len(piece.encode('utf8'))>max_out*16:raise ValueError('La respuesta superó el límite de tamaño reservado.')
                                    state['content']+=piece
                                if type(tokens) is int and tokens>0:
                                    elapsed=time.perf_counter()-inference_started
                                    if elapsed>0:
                                        state.update(tokens=tokens,tps=round(tokens/elapsed,1),
                                                     elapsed=round(elapsed,3),measurement_kind='request')
                            self._persist_request(state)
                        break
            except Exception as exc:
                if cancel_ev.is_set():
                    next_status='cancelled'
                else:
                    next_status='error'
                    with self.lock:state['error']=str(exc)[:240]
            finally:
                if cancel_ev.is_set():next_status='cancelled'
                with self.lock:
                    state.pop('response',None)
                    final_content=state['content']
                    err_text=state['error']
                    if next_status=='done' and not final_content.strip():
                        next_status='error';err_text='El modelo terminó sin una respuesta visible. Aumentá los tokens de respuesta si se agotaron durante el razonamiento.';state['error']=err_text
                if next_status=='error' and not final_content:
                    final_content=err_text or 'No se pudo completar la respuesta.'
                with self._conn() as db:
                    db.execute('UPDATE messages SET content=?, status=? WHERE id=?',(final_content,next_status,asst_msg_id))
                    db.execute('UPDATE conversations SET updated_at=? WHERE id=?',(time.time(),cid))
                self._persist_request({**state,'status':next_status,'content':final_content},True)
                with self.lock:
                    state['status']=next_status;state['content']=final_content

        threading.Thread(target=worker,daemon=True).start()
        return {'request_id':req_id,'user_message_id':user_msg_id,'assistant_message_id':asst_msg_id,'title':new_title,'context':context_stats}

    def _persist_request(self,state,force=False):
        now=time.monotonic()
        if not force and now-state.get('_persisted_at',0)<1:return
        state['_persisted_at']=now
        fields=('id','conversation_id','message_id','status','content','error','title','tps','tokens','elapsed','measurement_kind','context','reserved_bytes')
        snapshot={key:state.get(key) for key in fields}
        with self._conn() as db:
            db.execute('INSERT OR REPLACE INTO chat_requests VALUES(?,?,?,?,?,?)',(state['id'],state['conversation_id'],state['message_id'],state['status'],json.dumps(snapshot,ensure_ascii=False),time.time()))
            db.execute('UPDATE messages SET content=?,status=? WHERE id=?',(state['content'],state['status'],state['message_id']))

    def get_request(self,req_id):
        with self.lock:
            state=self.requests.get(req_id)
            if state:return {key:state.get(key) for key in ('id','status','content','error','title','tps','tokens','elapsed','measurement_kind','context','reserved_bytes')}
        with self._conn() as db:row=db.execute('SELECT payload FROM chat_requests WHERE id=?',(req_id,)).fetchone()
        if not row:raise ValueError('Solicitud de generación no encontrada.')
        return json.loads(row['payload'])

    def cancel_request(self,req_id):
        with self.lock:
            state=self.requests.get(req_id)
            if not state:
                old=self.get_request_from_disk(req_id)
                if old['status']!='running':return {'ok':True,'status':old['status']}
                raise ValueError('Solicitud no disponible para cancelar.')
            state['cancel'].set();state['status']='cancelled'
            response=state.get('response')
        self._persist_request(state,True)
        if response:threading.Thread(target=response.close,daemon=True).start()
        return {'ok':True,'status':'cancelled','notice':'Cancelado en el panel y cierre de conexión solicitado. Esto no apaga la sesión de Kaggle.'}

    def get_request_from_disk(self,req_id):
        with self._conn() as db:row=db.execute('SELECT payload FROM chat_requests WHERE id=?',(req_id,)).fetchone()
        if not row:raise ValueError('Solicitud no encontrada.')
        return json.loads(row['payload'])
