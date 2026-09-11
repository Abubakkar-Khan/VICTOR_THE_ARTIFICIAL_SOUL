# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

project_root = os.path.abspath(os.curdir)

datas = [
    (os.path.join(project_root, 'victor', 'web'), os.path.join('victor', 'web')),
    (os.path.join(project_root, 'victor', 'sprite'), os.path.join('victor', 'sprite')),
    (os.path.join(project_root, 'config'), 'config'),
]

hiddenimports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespans',
    'uvicorn.lifespans.on',
    'fastapi',
    'fastapi.staticfiles',
    'starlette',
    'starlette.routing',
    'starlette.staticfiles',
    'starlette.middleware',
    'starlette.middleware.cors',
    'starlette.responses',
    'pydantic',
    'pydantic_core',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'duckduckgo_search',
    'bs4',
    'yaml',
    'urllib.request',
    'tkinter',
    'webview',
    'webview.platforms.winforms',
    'webview.platforms.edgechromium',
    'sounddevice',
    'speech_recognition',
    'scipy',
    'scipy.io',
    'scipy.io.wavfile',
    'clr',
    'pythonnet',
]

a = Analysis(
    ['victor/launcher.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Victor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'victor', 'sprite', 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Victor',
)
