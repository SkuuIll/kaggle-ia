"""Pinned CUDA runtime for the qualified ThinkingCap profile."""

import os
from pathlib import Path
import subprocess


def start_llama(config, model_path, log):
    root = Path('/kaggle/temp/ia-llama')
    root.mkdir(parents=True, exist_ok=True)
    tag = 'b12170'
    for prefix in ('llama', 'cudart-llama'):
        name = f'{prefix}-{tag}-bin-ubuntu-cuda-12.8-x64.tar.gz'
        archive = root / name
        subprocess.run(['curl', '-fLsS', '--retry', '4', '-o', str(archive),
                        f'https://github.com/ggml-org/llama.cpp/releases/download/{tag}/{name}'], check=True)
        subprocess.run(['tar', '-xzf', str(archive), '-C', str(root)], check=True)
        archive.unlink()
    binary = next(root.rglob('llama-server'))
    libraries = sorted({str(path.parent) for path in root.rglob('*.so*')})
    if os.environ.get('LD_LIBRARY_PATH'):
        libraries.append(os.environ['LD_LIBRARY_PATH'])
    return subprocess.Popen(
        [str(binary), '-m', str(model_path), '--alias', config['model'], '-c', str(config['context']),
         '-np', '1', '-ngl', '999', '-sm', 'layer', '-fa', 'on', '-ctk', 'q8_0', '-ctv', 'q8_0',
         '-b', '2048', '-ub', '512', '--jinja', '--host', '127.0.0.1', '--port', '11434',
         '--no-context-shift', '--sse-ping-interval', '15'],
        env={**os.environ, 'LD_LIBRARY_PATH': ':'.join(libraries)}, stdout=log, stderr=log,
    )
