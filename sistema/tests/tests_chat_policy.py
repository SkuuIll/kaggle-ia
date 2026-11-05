import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import base64,json,tempfile,time,unittest
from pathlib import Path
from chat_engine import ChatStore
from chat_storage import save_policy,check_upload,storage_status,archive_stale,archived_items,restore
class ChatPolicyTests(unittest.TestCase):
 def test_restart_marks_partial_request_interrupted_and_keeps_content(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=ChatStore(tmp);conv=store.create_conversation('rapido')
   with store._conn() as db:db.execute("INSERT INTO messages VALUES('msg',?,'assistant','parcial','running',?)",(conv['id'],time.time()))
   state={'id':'req','conversation_id':conv['id'],'message_id':'msg','status':'running','content':'parcial','error':'','title':'test','tokens':1,'tps':1,'elapsed':1}
   store._persist_request(state,True);reopened=ChatStore(tmp)
   self.assertEqual(reopened.get_request('req')['status'],'interrupted')
   self.assertEqual(reopened.get_conversation(conv['id'])['messages'][0]['content'],'parcial')
 def test_quota_refuses_before_write_and_retention_is_recoverable(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=ChatStore(tmp);conv=store.create_conversation('rapido');save_policy(store,64,1)
   with self.assertRaises(ValueError):check_upload(store,30*1024*1024)
   att=store.upload_attachment(conv['id'],'file.txt','text/plain',base64.b64encode(b'hello').decode())
   with store._conn() as db:db.execute('UPDATE attachments SET created_at=0 WHERE id=?',(att['id'],))
   self.assertEqual(archive_stale(store)['archived_attachments'],1)
   self.assertTrue(store.get_attachment_file(att['id'])[1].exists())
   restore(store,'attachment',att['id']);self.assertEqual(archived_items(store)['attachments'],[])
   store.archive_conversation(conv['id']);restore(store,'conversation',conv['id'])
   self.assertEqual(store.get_conversation(conv['id'])['conversation']['id'],conv['id'])

 def test_generation_admission_reserves_output_before_writing_messages(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as tmp:
   store=ChatStore(tmp);conv=store.create_conversation('rapido')
   with patch('chat_storage.check_capacity',side_effect=ValueError('Cuota llena')):
    with self.assertRaises(ValueError):store.start_send(conv['id'],'Hola',[],{'account':1,'model':'test','context':32768})
   self.assertEqual(store.get_conversation(conv['id'])['messages'],[])
 def test_restored_upload_is_returned_to_pending_list(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=ChatStore(tmp);conv=store.create_conversation('rapido')
   att=store.upload_attachment(conv['id'],'pending.txt','text/plain',base64.b64encode(b'texto').decode())
   with store._conn() as db:db.execute('UPDATE attachments SET archived=1 WHERE id=?',(att['id'],))
   self.assertEqual(store.get_conversation(conv['id'])['pending_attachments'],[])
   restore(store,'attachment',att['id'])
   self.assertEqual(store.get_conversation(conv['id'])['pending_attachments'][0]['id'],att['id'])
