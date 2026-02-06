# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Hidden imports for all required modules
hidden_imports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'fastapi.responses',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'pydantic',
    'pydantic.fields',
    'pydantic.networks',
    'httpx',
    'multipart',
    'faster_whisper',
    'ctranslate2',
    'tokenizers',
    'cv2',
    'mediapipe',
    'PIL',
    'PIL.Image',
    'numpy',
    'yt_dlp',
    'yt_dlp.extractor',
    'yt_dlp.downloader',
    'boto3',
    'botocore',
    'botocore.exceptions',
    'sqlite3',
    'json',
    'pathlib',
    'threading',
    'concurrent.futures',
    'subprocess',
]

datas = [
    ('.env.example', '.'),
    ('services', 'services'),
]

binaries = []

for pkg in [
    'faster_whisper',
    'ctranslate2',
    'tokenizers',
    'mediapipe',
    'cv2',
    'numpy',
    'yt_dlp',
    'boto3',
    'botocore',
]:
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hidden_imports += pkg_hidden

a = Analysis(
    ['run_backend.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'test_*',
        'tests',
        '__pycache__',
        'torch',
        'torchvision',
        'torchaudio',
    ],
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
    name='antariks-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='antariks-backend',
)
