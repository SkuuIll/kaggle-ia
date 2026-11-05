import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import base64,unittest
from unittest.mock import Mock
from vision_helper import analyze_visual,VISION_MODEL,VISION_DIGEST
class VisionHelperTests(unittest.TestCase):
 def response(self,data):
  r=Mock();r.json.return_value=data;return r
 def test_model_is_sequentially_unloaded_and_digest_checked(self):
  client=Mock();client.get.return_value=self.response({'models':[{'name':VISION_MODEL,'digest':VISION_DIGEST}]})
  client.post.side_effect=[self.response({}),self.response({'message':{'content':'Una imagen roja'}}),self.response({})]
  result=analyze_visual('coder',['data:image/jpeg;base64,'+base64.b64encode(b'fixture').decode()],'Describí',client)
  self.assertEqual(result['text'],'Una imagen roja');self.assertEqual(client.post.call_args_list[0].kwargs['json']['model'],'coder')
  self.assertEqual(client.post.call_args_list[-1].kwargs['json'],{'model':VISION_MODEL,'keep_alive':0})
 def test_changed_digest_never_generates_visual_answer(self):
  client=Mock();client.get.return_value=self.response({'models':[{'name':VISION_MODEL,'digest':'sha256:'+'0'*64}]})
  client.post.return_value=self.response({})
  with self.assertRaises(ValueError):analyze_visual('coder',['data:image/png;base64,eA=='],'Describe',client)
  self.assertFalse(any('/api/chat' in c.args[0] for c in client.post.call_args_list))
 def test_invalid_input_does_not_unload_or_pull_models(self):
  client=Mock()
  with self.assertRaises(ValueError):analyze_visual('coder',['https://example.test/picture'],'Describe',client)
  client.post.assert_not_called()

class FrameOrderTests(unittest.TestCase):
 def test_frames_are_observed_independently_and_order_is_explicit(self):
  from vision_helper import observe_frames
  post=Mock();post.side_effect=[VisionHelperTests().response({'text':'red'}),VisionHelperTests().response({'text':'blue'})]
  result=observe_frames(17860,['first-image','second-image'],'Describe',post)
  self.assertEqual([c.kwargs['json']['images'] for c in post.call_args_list],[['first-image'],['second-image']])
  self.assertLess(result.index('red'),result.index('blue'));self.assertIn('1',result);self.assertIn('2',result)

 def test_identical_frames_keep_positions_without_duplicate_inference(self):
  from vision_helper import observe_frames
  post=Mock();post.return_value=VisionHelperTests().response({'text':'red'})
  text=observe_frames(17860,['same','same'],'Describe',post)
  self.assertEqual(post.call_count,1);self.assertIn('fotograma 1',text);self.assertIn('fotograma 2',text)
