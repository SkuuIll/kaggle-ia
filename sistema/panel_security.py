import hmac,os
from urllib.parse import urlsplit

def panel_host(host,port):
    origin=os.environ.get('IA_PUBLIC_ORIGIN','')
    return local_host(host,port) or bool(origin and host==urlsplit(origin).netloc)
def local_host(host,port):return host in {f'127.0.0.1:{port}',f'localhost:{port}'}
def mutation_allowed(headers,token,port):
    allowed={'',f'http://127.0.0.1:{port}',f'http://localhost:{port}'}
    if os.environ.get('IA_PUBLIC_ORIGIN'):allowed.add(os.environ['IA_PUBLIC_ORIGIN'])
    return panel_host(headers.get('Host',''),port) and headers.get('Origin','') in allowed and hmac.compare_digest(headers.get('X-IA-Token',''),token)


def login_return_target(value):
    import re
    from urllib.parse import urlsplit,parse_qs
    if not isinstance(value,str) or len(value)>2048 or any(ord(c)<32 for c in value):return '/'
    try:parsed=urlsplit(value)
    except ValueError:return '/'
    if parsed.scheme or parsed.netloc:return '/'
    if parsed.path=='/' and not parsed.query and parsed.fragment in ('','dashboard','chat','cuentas','modelos','plantillas','actividad','configuracion'):
        return '/'+('#'+parsed.fragment if parsed.fragment else '')
    if re.fullmatch(r'/api/chat/attachment/[a-f0-9]{16,32}',parsed.path):
        return parsed.path+('?inline=1' if parse_qs(parsed.query).get('inline')==['1'] else '')
    if re.fullmatch(r'/api/download/[a-f0-9]{32}',parsed.path):return parsed.path
    return '/'


def file_login_redirect(path,headers,method):
    from urllib.parse import quote
    if method!='GET' or not (headers.get('Sec-Fetch-Dest')=='document' or 'text/html' in headers.get('Accept','')):return None
    target=login_return_target(path)
    if not target.startswith(('/api/chat/attachment/','/api/download/')):return None
    return '/login?expired=1&next='+quote(target,safe='')


def attachment_headers(name,mime,inline=False):
    import re,unicodedata
    from urllib.parse import quote
    name=str(name).replace('\r','').replace('\n','')[:180] or 'archivo'
    fallback=unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode()
    fallback=re.sub(r'[^A-Za-z0-9._ -]','_',fallback) or 'archivo'
    mime=str(mime).split(';',1)[0].strip().lower()
    if not re.fullmatch(r'[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+',mime):mime='application/octet-stream'
    allowed={'image/png','image/jpeg','image/webp','image/gif','video/mp4','video/webm','video/quicktime','video/x-matroska','video/x-msvideo','audio/mpeg','audio/wav','audio/ogg','audio/mp4','audio/flac','application/pdf','text/plain'}
    mode='inline' if inline and mime in allowed else 'attachment'
    return mime,mode+'; filename="'+fallback+'"; filename*=UTF-8\'\''+quote(name,safe='')
