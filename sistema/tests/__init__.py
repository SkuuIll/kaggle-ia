import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent
_SUBDIRS = ['core', 'chat', 'pool', 'accounts', 'clients', 'templates', 'web', 'tests']
for _sub in _SUBDIRS:
    _p = str(_BASE / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))
