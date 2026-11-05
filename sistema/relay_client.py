"""Compatibility forwarder for sistema.pool.relay_client"""
import sys, runpy
from pathlib import Path

_BASE = Path(__file__).resolve().parent
_SUBDIRS = ['core', 'chat', 'pool', 'accounts', 'clients', 'templates', 'web', 'tests']
for _sub in _SUBDIRS:
    _p = str(_BASE / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

_target = _BASE / 'pool' / 'relay_client.py'

if __name__ == '__main__':
    runpy.run_path(str(_target), run_name='__main__')
else:
    from pool.relay_client import *
    from pool import relay_client as _mod
    for _k in dir(_mod):
        if not _k.startswith('__'):
            globals()[_k] = getattr(_mod, _k)
