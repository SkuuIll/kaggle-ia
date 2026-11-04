import json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import chat_media
class ASRConfigurationTests(unittest.TestCase):
 def test_empty_model_directory_is_not_advertised_as_ready(self):
  with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'IA_ASR_MODEL_DIR':folder}):
   self.assertIsNone(chat_media._asr_dir())
 def test_asr_never_requests_gpu_or_remote_model(self):
  self.assertIn("device='cpu'",chat_media.ASR_SCRIPT)
  self.assertIn('local_files_only=True',chat_media.ASR_SCRIPT)
  self.assertIn('cpu_threads=2',chat_media.ASR_SCRIPT)
 def test_local_asr_transcribes_real_synthetic_speech(self):
  if not chat_media.capabilities()['audio_transcription'] or not shutil.which('ffmpeg'):self.skipTest('Modelo ASR local o FFmpeg no configurados en este entorno')
  filters=subprocess.run([shutil.which('ffmpeg'),'-hide_banner','-filters'],capture_output=True,text=True,timeout=10)
  if 'flite' not in filters.stdout:self.skipTest('FFmpeg sin filtro flite para fixture de voz')
  with tempfile.TemporaryDirectory(prefix='asr-speech-smoke-') as folder:
   audio=Path(folder)/'speech.wav'
   subprocess.run([shutil.which('ffmpeg'),'-nostdin','-v','error','-f','lavfi','-i',"flite=text='This is a speech transcription test. The model is working correctly.':voice=slt",'-ar','16000','-y',str(audio)],check=True,timeout=20,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   result=chat_media.prepare_media(audio,'audio')
   self.assertTrue(result['text'].strip());self.assertIn('test',result['text'].lower())
   self.assertIn('CPU',result['notice'])
