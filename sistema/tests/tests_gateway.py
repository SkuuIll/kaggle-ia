import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import ast,io,unittest
from pathlib import Path
from unittest.mock import Mock

class GatewayExtensionTests(unittest.TestCase):
 def test_extension_is_explicit_limited_and_renews_idle(self):
  tree=ast.parse(((Path(__file__).parent.parent/'core'/'remote_gateway.py' if (Path(__file__).parent.parent/'core'/'remote_gateway.py').exists() else Path(__file__).parent/'remote_gateway.py')).read_text(encoding='utf8'))
  # Exclude only the production socket and background thread startup.
  tree.body=tree.body[:-2];namespace={};exec(compile(tree,'gateway-test','exec'),namespace)
  handler=object.__new__(namespace['Gateway']);handler.path='/control/extend';handler.wfile=io.BytesIO()
  handler.send_response=Mock();handler.send_error=Mock();handler.end_headers=Mock()
  namespace['last_activity']=0
  for _ in range(4):handler.do_POST()
  self.assertEqual(namespace['session_extension'],120);self.assertGreater(namespace['last_activity'],0)
  handler.do_POST();handler.send_error.assert_called_once_with(409)
  self.assertEqual(handler.send_response.call_count,4)
