import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _d in [_ROOT, _ROOT / 'core', _ROOT / 'chat', _ROOT / 'pool', _ROOT / 'accounts', _ROOT / 'clients', _ROOT / 'templates']:
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import shutil,subprocess,tempfile,unittest,zipfile,json
from pathlib import Path
from portability import export_program,export_private,import_private
from lifecycle import stop_reason

class PortabilityTests(unittest.TestCase):
    def test_program_excludes_credentials_generated_notebooks_and_caches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'app';root.mkdir();(root/'sistema').mkdir()
            for name in ['MENU_IA.bat','README.md','sistema/panel.html','sistema/coding_control.py','sistema/kaggle(1).json','sistema/kernel2/coder_server.ipynb','sistema/.private/kaggle_relay','sistema/.venv/secret.txt']:
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('private' if '.private' in name or '.json' in name else 'data')
            out=Path(tmp)/'program.zip';export_program(root,out)
            with zipfile.ZipFile(out) as z:
                self.assertIn('MENU_IA.bat',z.namelist());self.assertIn('sistema/coding_control.py',z.namelist())
                self.assertIn('sistema/panel.html',z.namelist())
                self.assertFalse(any('kaggle(' in n or '.private' in n or '.venv' in n or '.ipynb' in n for n in z.namelist()))

    def test_modular_publication_cli_exports_from_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'README.md').write_text('project readme')
            for name in ('publicar_codigo.py','templates/publicar_codigo.py','core/portability.py'):
                target=root/'sistema'/name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(_ROOT/name,target)
            result=subprocess.run([sys.executable,str(root/'sistema/publicar_codigo.py')],cwd=root,
                                  capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            with zipfile.ZipFile(root/'exportaciones/kaggle-ia-publico.zip') as archive:
                self.assertIn('README.md',archive.namelist())
                self.assertIn('sistema/templates/publicar_codigo.py',archive.namelist())

    def test_private_connection_roundtrip_does_not_include_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'source';(root/'sistema/.private').mkdir(parents=True)
            (root/'sistema/kaggle(2).json').write_text(json.dumps({'username':'sample','key':'not-real'}))
            (root/'sistema/.private/kaggle_relay').write_text('test-private-key')
            (root/'sistema/.private/known_hosts').write_text('test-host')
            (root/'sistema/.private/log.txt').write_text('omit')
            out=Path(tmp)/'private.zip';export_private(root,out)
            dest=Path(tmp)/'dest';import_private(dest,out)
            self.assertEqual((dest/'sistema/.private/kaggle_relay').read_text(),'test-private-key')
            self.assertFalse((dest/'sistema/.private/log.txt').exists())

    def test_import_rejects_unexpected_or_traversal_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive=Path(tmp)/'bad.zip';dest=Path(tmp)/'dest'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('sistema/.private/known_hosts','ok');z.writestr('../escape.txt','bad')
            with self.assertRaises(ValueError):import_private(dest,archive)
            self.assertFalse((dest/'sistema/.private/known_hosts').exists())

class LifecycleTests(unittest.TestCase):
    def test_idle_does_not_interrupt_active_generation(self):
        self.assertIsNone(stop_reason(0,0,1,901,15,120))
        self.assertEqual(stop_reason(0,0,0,901,15,120),'inactividad')
    def test_absolute_limit_stops_even_busy(self):
        self.assertEqual(stop_reason(0,7200,1,7201,15,120),'limite de sesion')

if __name__=='__main__':unittest.main()
