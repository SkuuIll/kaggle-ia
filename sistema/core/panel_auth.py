"""Password verification for the HTTPS dashboard; credentials never enter logs."""
import base64,hashlib,hmac,json,os,re,secrets,tempfile,time,threading
from pathlib import Path

def password_record(username,password):
    if not username or ':' in username or not 16<=len(password)<=256:raise ValueError('Usuario requerido y contrasena de 16 a 256 caracteres.')
    salt=secrets.token_bytes(16)
    digest=hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1,dklen=32)
    return {'username':username,'salt':salt.hex(),'digest':digest.hex()}

class PasswordGate:
    def __init__(self,path):
        self.path=Path(path);self.record=json.loads(self.path.read_text(encoding='utf8'));self.failures={};self.lock=threading.Lock()
        self.users_path=self.path.with_name('panel-users.json')
        self.users=json.loads(self.users_path.read_text(encoding='utf8')) if self.users_path.exists() else {}
    @staticmethod
    def _save(path,record):
        fd,name=tempfile.mkstemp(prefix=path.name+'.',suffix='.pending',dir=path.parent)
        temp=Path(name)
        try:
            with os.fdopen(fd,'w',encoding='utf8') as stream:json.dump(record,stream)
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)
    def role(self,username):
        if username==self.record['username']:return 'owner'
        if username in self.users:return 'observer'
        return None
    def list_users(self):
        return sorted(self.users)
    def create_user(self,username,password):
        if not isinstance(username,str) or not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{2,31}',username):
            raise ValueError('Usá de 3 a 32 letras minúsculas, números, puntos, guiones o guiones bajos.')
        if self.role(username) or username.casefold()==self.record['username'].casefold():
            raise ValueError('Ese usuario ya existe.')
        if len(self.users)>=25:raise ValueError('Se alcanzó el límite de 25 usuarios invitados.')
        if not isinstance(password,str) or not 16<=len(password)<=256:
            raise ValueError('Usá una contraseña de 16 a 256 caracteres.')
        users={**self.users,username:password_record(username,password)}
        self._save(self.users_path,users);self.users=users
    def remove_user(self,username):
        if not isinstance(username,str) or username not in self.users or self.role(username)!='observer':
            raise ValueError('Usuario invitado no encontrado.')
        users={key:value for key,value in self.users.items() if key!=username}
        self._save(self.users_path,users);self.users=users
    def check(self,username,password,source='local'):
        if not isinstance(username,str) or not isinstance(password,str) or ':' in username or len(username)>128 or len(password)>256:return False
        try:header='Basic '+base64.b64encode((username+':'+password).encode()).decode()
        except UnicodeError:return False
        return self.verify(header,source)
    def change_password(self,username,current,new,source='local'):
        if not self.check(username,current,source):return False
        if not isinstance(new,str) or not 16<=len(new)<=256:raise ValueError('Usa entre 16 y 256 caracteres.')
        record=password_record(username,new)
        if self.role(username)=='owner':
            self._save(self.path,record);self.record=record
        else:
            users={**self.users,username:record}
            self._save(self.users_path,users);self.users=users
        return True
    def verify(self,header,source='local'):
        with self.lock:
            now=time.monotonic()
            self.failures={ip:[t for t in times if now-t<60] for ip,times in self.failures.items() if times and now-times[-1]<60}
            if len(self.failures.get(source,[]))>=20:return False
        try:
            if not header.startswith('Basic ') or len(header)>2048:return False
            user,password=base64.b64decode(header[6:],validate=True).decode().split(':',1)
            record=self.record if user==self.record['username'] else self.users.get(user,self.record)
            digest=hashlib.scrypt(password.encode(),salt=bytes.fromhex(record['salt']),n=16384,r=8,p=1,dklen=32)
            valid=hmac.compare_digest(user.encode(),record['username'].encode()) & hmac.compare_digest(digest.hex(),record['digest'])
        except (ValueError,UnicodeError):valid=False
        if not valid:
            with self.lock:
                if len(self.failures)>1024:self.failures.pop(next(iter(self.failures)))
                self.failures.setdefault(source,[]).append(time.monotonic())
        return bool(valid)

class Sessions:
    """Opaque server-side sessions. Restart, logout or password reset revoke access."""
    lifetime=8*60*60
    cookie_name='__Host-ia_session'
    def __init__(self,clock=time.monotonic):self.clock=clock;self.items={};self.lock=threading.Lock()
    def create(self,username):
        with self.lock:
            now=self.clock();self.items={k:v for k,v in self.items.items() if v['expires']>now}
            if len(self.items)>=100:self.items.pop(next(iter(self.items)))
            token=secrets.token_urlsafe(32)
            self.items[token]={'username':username,'csrf':secrets.token_urlsafe(32),'expires':now+self.lifetime}
            return token
    def get(self,token):
        with self.lock:
            value=self.items.get(token)
            if value and value['expires']>self.clock():return dict(value)
            self.items.pop(token,None);return None
    def revoke(self,token):
        with self.lock:self.items.pop(token,None)
    def revoke_user(self,username):
        with self.lock:self.items={k:v for k,v in self.items.items() if v['username']!=username}
    def clear(self):
        with self.lock:self.items.clear()
    def cookie(self,token):
        return f'{self.cookie_name}={token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age={self.lifetime if token else 0}'
