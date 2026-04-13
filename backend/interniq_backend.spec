# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for InternIQ backend
# Run: pyinstaller backend/interniq_backend.spec

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Collect all submodules for key packages
uvicorn_datas, uvicorn_binaries, uvicorn_hiddenimports = collect_all('uvicorn')
fastapi_datas, fastapi_binaries, fastapi_hiddenimports = collect_all('fastapi')
sqlalchemy_datas, sqlalchemy_binaries, sqlalchemy_hiddenimports = collect_all('sqlalchemy')

all_datas = uvicorn_datas + fastapi_datas + sqlalchemy_datas
all_binaries = uvicorn_binaries + fastapi_binaries + sqlalchemy_binaries
all_hiddenimports = (
    uvicorn_hiddenimports +
    fastapi_hiddenimports +
    sqlalchemy_hiddenimports +
    collect_submodules('pydantic') +
    collect_submodules('starlette') +
    collect_submodules('email_validator') +
    [
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
        'uvicorn.main',
        'anyio',
        'anyio._backends._asyncio',
        'anyio._backends._trio',
        'pydantic',
        'pydantic.v1',
        'pydantic.v1.networks',
        'requests',
        'aiofiles',
        'multipart',
        'dotenv',
        'dotenv.main',
        'python_dotenv',
        'apscheduler',
        'apscheduler.triggers.interval',
        'apscheduler.triggers.cron',
        'apscheduler.executors.pool',
        'apscheduler.jobstores.sqlalchemy',
        'httpx',
        'multiprocessing',
    ]
)

a = Analysis(
    ['app/main.py'],
    pathex=['..'],
    binaries=all_binaries,
    datas=all_datas + [
        ('../backend/models', 'backend/models'),
        ('../backend/api', 'backend/api'),
        ('../backend/services', 'backend/services'),
        ('../backend/scrapers', 'backend/scrapers'),
        ('../backend/__init__.py', 'backend/'),
        ('../backend/main.py', 'backend/'),
        ('../backend/config.py', 'backend/'),
        ('../backend/scheduler.py', 'backend/'),
    ],
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Exclude heavy optional/unused packages to keep the binary small
    excludes=['tkinter', 'matplotlib', 'PIL', 'cv2', 'numpy', 'pandas',
              'playwright', 'motor', 'ollama', 'anthropic', 'openai',
              'psycopg2', 'psycopg2_binary'],
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
    name='interniq-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window = cleaner native feel
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
    name='interniq-backend',
)
