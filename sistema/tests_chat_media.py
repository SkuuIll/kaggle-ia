import json,tempfile,unittest,shutil,subprocess
from pathlib import Path
from unittest.mock import patch
import chat_media

class MediaPreparationTests(unittest.TestCase):
 def test_rejects_urls_and_oversized_files_before_any_subprocess(self):
  with patch('chat_media._run') as run:
   with self.assertRaises(ValueError):chat_media.prepare_media('https://example.test/video.mp4','video')
   run.assert_not_called()
 def test_frames_are_real_local_outputs_and_temporary_files_are_removed(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'clip.mp4';path.write_bytes(b'video')
   commands=[]
   def execute(command,timeout=30):
    commands.append(command)
    if 'ffprobe' in command[0]:return json.dumps({'format':{'duration':'20'},'streams':[{'codec_type':'video','width':640,'height':360}]}).encode()
    Path(command[-1]).write_bytes(b'\xff\xd8JPEG');return b''
   with patch('chat_media.shutil.which',side_effect=lambda n:n),patch('chat_media._run',side_effect=execute):result=chat_media.prepare_media(path,'video')
   self.assertEqual(len(result['image_urls']),4);self.assertIn('No se transcribió',result['notice'])
   self.assertEqual(list(Path(folder).iterdir()),[path])
   self.assertTrue(all('file,pipe' in c for c in commands));self.assertTrue(all('mov' in c for c in commands))
 def test_rejects_long_or_invalid_duration_before_frame_decode(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'clip.mp4';path.write_bytes(b'video')
   for duration in ['181','nan','inf','0']:
    with patch('chat_media.shutil.which',return_value='ffprobe'),patch('chat_media._run',return_value=json.dumps({'format':{'duration':duration}}).encode()):
     with self.assertRaises(ValueError):chat_media.prepare_media(path,'video')
 def test_audio_without_local_model_does_not_invent_transcription(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'clip.wav';path.write_bytes(b'audio')
   with patch('chat_media._probe',return_value=({},3)),patch('chat_media.capabilities',return_value={'audio_transcription':False}),patch('chat_media._run') as run:
    result=chat_media.prepare_media(path,'audio');self.assertEqual(result['text'],'');self.assertIn('sin interpretar',result['notice']);run.assert_not_called()

class RealMediaSmokeTests(unittest.TestCase):
 @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg/ffprobe no instalados')
 def test_extracts_four_real_jpegs_from_synthetic_cpu_video(self):
  with tempfile.TemporaryDirectory(prefix='ia-media-smoke-') as folder:
   path=Path(folder)/'synthetic.mp4'
   subprocess.run([shutil.which('ffmpeg'),'-nostdin','-v','error','-f','lavfi','-i','color=c=red:s=320x240:r=4:d=4','-c:v','mpeg4','-pix_fmt','yuv420p','-y',str(path)],check=True,timeout=20,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   result=chat_media.prepare_media(path,'video')
   self.assertEqual(len(result['image_urls']),4)
   self.assertTrue(all(url.startswith('data:image/jpeg;base64,/9j/') for url in result['image_urls']))
   self.assertEqual(list(Path(folder).iterdir()),[path])

if __name__=='__main__':unittest.main()
