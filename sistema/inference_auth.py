"""Scoped bearer credentials for HTTPS inference; no browser sessions accepted."""
import hashlib,hmac,json
from pathlib import Path

def allowed(header,account,path):
    if not header.startswith('Bearer ') or len(header)>512:return False
    try:expected=json.loads(Path(path).read_text(encoding='utf8')).get(str(account),'')
    except (OSError,ValueError):return False
    return bool(expected) and hmac.compare_digest(hashlib.sha256(header[7:].encode()).hexdigest(),expected)
