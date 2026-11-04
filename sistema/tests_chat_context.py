import unittest
from chat_context import pack_context,cost
class ContextTests(unittest.TestCase):
 def test_budget_keeps_latest_and_never_changes_history(self):
  original=[{'role':'system','content':'Reglas' }]+[{'role':'user' if i%2==0 else 'assistant','content':str(i)+'x'*1400} for i in range(30)]
  result,stats=pack_context(original,8192,1024)
  self.assertEqual(result[-1],original[-1]);self.assertGreater(stats['omitted_messages'],0)
  self.assertLessEqual(sum(cost(m) for m in result),stats['budget']);self.assertEqual(len(original),31)
 def test_oversized_latest_is_rejected_without_truncation(self):
  with self.assertRaises(ValueError):pack_context([{'role':'user','content':'x'*9000}],8192,1024)
 def test_multilingual_text_cost_is_conservative(self):
  self.assertGreater(cost({'content':'你好😀'}),len('你好😀'))
