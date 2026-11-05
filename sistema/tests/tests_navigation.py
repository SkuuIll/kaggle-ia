import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import unittest
from panel_security import login_return_target,file_login_redirect

class NavigationTests(unittest.TestCase):
 def test_attachment_login_returns_to_exact_safe_attachment(self):
  target='/api/chat/attachment/'+'a'*16+'?inline=1'
  self.assertEqual(login_return_target(target),target)
  self.assertIn('next=%2Fapi%2Fchat%2Fattachment%2F',file_login_redirect(target,{'Accept':'text/html'},'GET'))
 def test_api_requests_still_receive_unauthorized_instead_of_html(self):
  target='/api/chat/attachment/'+'a'*16
  self.assertIsNone(file_login_redirect(target,{'Accept':'application/json'},'GET'))
  self.assertIsNone(file_login_redirect('/api/state',{'Accept':'text/html'},'GET'))
  self.assertIsNone(file_login_redirect(target,{'Accept':'text/html'},'POST'))
 def test_foreign_destinations_control_characters_and_traversal_are_rejected(self):
  for target in ['//evil.example/a','https://evil.example/a','javascript:alert(1)','//[malformed-host','/\\evil.example','/api/chat/attachment/../../other','/\nLocation:other',None,7]:
   self.assertEqual(login_return_target(target),'/')
 def test_chat_navigation_and_private_download_are_allowed(self):
  self.assertEqual(login_return_target('/#chat'),'/#chat')
  path='/api/download/'+'b'*32
  self.assertEqual(login_return_target(path),path)
 def test_attachment_query_is_canonical_and_cannot_redirect(self):
  path='/api/chat/attachment/'+'a'*16
  self.assertEqual(login_return_target(path+'?inline=1&next=https://evil.example#fragment'),path+'?inline=1')

 def test_download_headers_support_unicode_names(self):
  from panel_security import attachment_headers
  mime,disposition=attachment_headers('informe_日本.pdf','application/pdf',True)
  self.assertEqual(mime,'application/pdf');self.assertTrue(disposition.startswith('inline;'))
  self.assertIn("filename*=UTF-8''",disposition);disposition.encode('ascii')
 def test_active_formats_are_downloaded_and_mime_header_is_sanitized(self):
  from panel_security import attachment_headers
  self.assertTrue(attachment_headers('picture.svg','image/svg+xml',True)[1].startswith('attachment;'))
  mime,disposition=attachment_headers('line\r\nname.txt','text/plain\r\nInjected: value',True)
  self.assertEqual(mime,'application/octet-stream');self.assertNotIn('\r',disposition);self.assertNotIn('\n',disposition)
