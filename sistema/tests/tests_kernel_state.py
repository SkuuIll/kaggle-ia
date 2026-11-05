import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import unittest,requests
from types import SimpleNamespace
from unittest.mock import Mock
from coding_control import state
def not_found():
    response=requests.Response();response.status_code=404
    return requests.HTTPError('not found',response=response)
class KernelStateTests(unittest.TestCase):
    def test_404_is_not_absence_when_owned_listing_has_target(self):
        api=Mock();api.kernels_status.side_effect=not_found()
        api.kernels_list.return_value=[SimpleNamespace(ref='me/model')]
        with self.assertRaises(requests.HTTPError):state(api,'me/model')
    def test_listing_checks_later_pages_before_declaring_missing(self):
        api=Mock();api.kernels_status.side_effect=ValueError('kernels.get denied')
        api.kernels_list.side_effect=[[SimpleNamespace(ref='me/'+str(i)) for i in range(100)],[SimpleNamespace(ref='me/model')]]
        with self.assertRaises(ValueError):state(api,'me/model')
        self.assertEqual(api.kernels_list.call_count,2)
    def test_confirmed_complete_listing_can_report_missing(self):
        api=Mock();api.kernels_status.side_effect=not_found();api.kernels_list.return_value=[]
        self.assertEqual(state(api,'me/model'),'MISSING')
if __name__=='__main__':unittest.main()
