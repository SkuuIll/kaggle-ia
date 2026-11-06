"""Bootstrap the pinned Heretic text server inside the private Kaggle notebook."""

import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request


def start_exl3(config, log):
    root = Path('/kaggle/temp/ia-exl3')
    root.mkdir(parents=True, exist_ok=True)
    python = sys.executable
    env = {**os.environ, 'CUDA_VISIBLE_DEVICES': '0,1', 'NCCL_P2P_DISABLE': '1',
           'HF_HUB_DOWNLOAD_TIMEOUT': '120', 'PIP_DISABLE_PIP_VERSION_CHECK': '1'}

    def run(*args, **kwargs):
        subprocess.run(args, env=env, check=True, **kwargs)

    run(python, '-m', 'pip', 'install', '--no-cache-dir', '--index-url',
        'https://download.pytorch.org/whl/cu128', 'torch==2.11.0+cu128')
    abi = f'cp{sys.version_info.major}{sys.version_info.minor}'
    wheel = f'exllamav3-1.6.6+cu128.torch2.11.0-{abi}-{abi}-linux_x86_64.whl'
    url = 'https://github.com/turboderp-org/exllamav3/releases/download/v1.6.6/'
    urllib.request.urlretrieve(url + wheel.replace('+', '%2B'), root / wheel)
    tabby = root / 'tabby'
    run('git', 'clone', '--quiet', 'https://github.com/theroyallab/tabbyAPI.git', str(tabby))
    run('git', '-C', str(tabby), 'checkout', '--quiet', '8f92fac5d9307bf1e09668c3715b32ff46ad0333')
    run(python, '-m', 'pip', 'install', '--no-cache-dir', str(root / wheel), str(tabby))
    report_phase('download')
    models = root / 'models'
    download = (
        'from huggingface_hub import snapshot_download; import sys; '
        'snapshot_download(sys.argv[1], revision=sys.argv[2], local_dir=sys.argv[3], '
        'allow_patterns=["*.json","*.safetensors","*.jinja","*.txt","*.model"])'
    )
    for repo, revision, name in (
        ('Honkware/Qwen3.8-27B-heretic-ara-exl3-4.0bpw', '1d09f16a35dc3c23b9634741bf61e6c746fcce21', config['model']),
        ('r0b0tlab/Qwen3.8-27B-DFlash2-EXL3-4.00bpw', '265b5240592907d2d55ff0dc4d5f66569692604d', 'dflash2'),
    ):
        run(python, '-c', download, repo, revision, str(models / name))
    context = config['context']
    options = {
        'network': {'host': '127.0.0.1', 'port': 11434, 'disable_auth': True, 'allowed_origins': []},
        'model': {'model_dir': str(models), 'model_name': config['model'], 'backend': 'exllamav3',
                  'max_seq_len': context, 'cache_size': context, 'cache_mode': 'Q4',
                  'tensor_parallel': True, 'tensor_parallel_backend': 'nccl',
                  'chunk_size': 1024, 'max_batch_size': 1, 'use_dummy_models': True,
                  'dummy_model_names': [config['model']]},
        'draft_model': {'draft_model_dir': str(models), 'draft_model_name': 'dflash2',
                        'draft_cache_mode': 'Q4', 'draft_num_tokens': 7},
    }
    settings_file = root / 'tabby-config.yml'
    settings_file.write_text(json.dumps(options), encoding='utf-8')
    report_phase('register')
    return subprocess.Popen([python, 'start.py', '--config', str(settings_file)],
                            cwd=tabby, env=env, stdout=log, stderr=log)
