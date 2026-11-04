"""Official quota conversion and counters only: never save conversation bodies."""
import json,sqlite3,time
from datetime import timezone
from contextlib import contextmanager
from pathlib import Path

def quota_values(response):
    quota=response.gpu_quota
    if quota is None:return None
    def seconds(value):return value.total_seconds() if value is not None else None
    used=seconds(quota.time_used);reserved=seconds(quota.time_reserved);allowed=seconds(quota.total_time_allowed)
    return {'used_seconds':used,'reserved_seconds':reserved,'allowed_seconds':allowed,
            'available_seconds':max(0,allowed-used-reserved) if None not in (allowed,used,reserved) else None,
            'refresh':(response.quota_refresh_time.replace(tzinfo=timezone.utc) if response.quota_refresh_time.tzinfo is None else response.quota_refresh_time).isoformat() if response.quota_refresh_time else None,'source':'Kaggle'}

class UsageParser:
    def __init__(self):self.buffer=b'';self.body=bytearray();self.value=None
    def feed(self,chunk):
        if len(self.body)<8*1024*1024:self.body.extend(chunk)
        self.buffer+=chunk
        while b'\n' in self.buffer:
            line,self.buffer=self.buffer.split(b'\n',1)
            if line.startswith((b'data: ',b'{')):
                try:self._object(json.loads(line[6:] if line.startswith(b'data: ') else line))
                except (ValueError,TypeError):pass
        if len(self.buffer)>8*1024*1024:self.buffer=b''
    def _object(self,data):
        if not isinstance(data,dict):return
        if isinstance(data.get('response'),dict):self._object(data['response'])
        usage=data.get('usage')
        if isinstance(usage,dict) and 'prompt_tokens' in usage and 'completion_tokens' in usage:
            self.value=(int(usage['prompt_tokens']),int(usage['completion_tokens']))
        elif isinstance(usage,dict) and 'input_tokens' in usage and 'output_tokens' in usage:
            self.value=(int(usage['input_tokens']),int(usage['output_tokens']))
        elif 'prompt_eval_count' in data and 'eval_count' in data:
            self.value=(int(data['prompt_eval_count']),int(data['eval_count']))
    def finish(self):
        if self.value is None:
            try:self._object(json.loads(self.body))
            except (ValueError,TypeError):pass
        return self.value

class UsageStore:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:db.execute('CREATE TABLE IF NOT EXISTS requests (id INTEGER PRIMARY KEY, timestamp REAL, account INTEGER, model TEXT, input_tokens INTEGER, output_tokens INTEGER, status INTEGER, duration REAL)')
        with self.connect() as db:db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, timestamp REAL, action TEXT, profile TEXT, status TEXT)')
        with self.connect() as db:
            if 'identity' not in {r[1] for r in db.execute('PRAGMA table_info(requests)')}:db.execute('ALTER TABLE requests ADD COLUMN identity TEXT')
            if 'detail' not in {r[1] for r in db.execute('PRAGMA table_info(events)')}:db.execute("ALTER TABLE events ADD COLUMN detail TEXT NOT NULL DEFAULT ''")
            db.execute('CREATE TABLE IF NOT EXISTS connections (account INTEGER PRIMARY KEY, identity TEXT NOT NULL)')
    @contextmanager
    def connect(self):
        connection=sqlite3.connect(self.path,timeout=10)
        try:
            with connection:yield connection
        finally:connection.close()
    def bind_identity(self,account,identity):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO connections(account,identity) VALUES(?,?)',(account,identity))
            # Legacy records are attributed once on migration, never to later replacement accounts.
            db.execute('UPDATE requests SET identity=? WHERE account=? AND identity IS NULL',(identity,account))
    def identity(self,account):
        with self.connect() as db:row=db.execute('SELECT identity FROM connections WHERE account=?',(account,)).fetchone()
        return row[0] if row else None
    def record(self,account,model,input_tokens,output_tokens,status,duration,identity=None):
        identity=identity if identity is not None else self.identity(account)
        with self.connect() as db:db.execute('INSERT INTO requests(timestamp,account,model,input_tokens,output_tokens,status,duration,identity) VALUES(?,?,?,?,?,?,?,?)',(time.time(),account,str(model)[:160],input_tokens,output_tokens,status,duration,identity))
    def totals(self,account,identity=None):
        clause=' AND identity=?' if identity is not None else '';args=(account,identity) if identity is not None else (account,)
        with self.connect() as db:
            row=db.execute('SELECT COUNT(*),COALESCE(SUM(input_tokens),0),COALESCE(SUM(output_tokens),0),SUM(CASE WHEN input_tokens IS NULL THEN 1 ELSE 0 END),AVG(duration),SUM(CASE WHEN status>=400 THEN 1 ELSE 0 END) FROM requests WHERE account=?'+clause,args).fetchone()
        return {'requests':row[0],'input_tokens':row[1],'output_tokens':row[2],'unknown_requests':row[3] or 0,'average_duration':row[4],'failed_requests':row[5] or 0}
    def daily(self,account,identity=None):
        clause=' AND identity=?' if identity is not None else '';args=(account,identity) if identity is not None else (account,)
        with self.connect() as db:
            rows=db.execute("SELECT strftime('%Y-%m-%d',timestamp,'unixepoch'),COUNT(*),COALESCE(SUM(input_tokens),0),COALESCE(SUM(output_tokens),0) FROM requests WHERE account=?"+clause+" AND timestamp>=CAST(strftime('%s','now','start of day','-6 days') AS REAL) GROUP BY 1 ORDER BY 1",args).fetchall()
        return [dict(zip(('day','requests','input_tokens','output_tokens'),row)) for row in rows]
    def event(self,action,profile,status,detail=""):
        with self.connect() as db:db.execute('INSERT INTO events(timestamp,action,profile,status,detail) VALUES(?,?,?,?,?)',(time.time(),str(action)[:40],str(profile or '')[:40],str(status)[:16],str(detail)[:240]))
    def events(self):
        with self.connect() as db:rows=db.execute('SELECT id,timestamp,action,profile,status,detail FROM events ORDER BY id DESC LIMIT 40').fetchall()
        return [dict(zip(('id','timestamp','action','profile','status','detail'),row)) for row in rows]
