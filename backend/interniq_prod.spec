# -*- mode: python ; coding: utf-8 -*-
# InternIQ Production PyInstaller Spec
# Single-file build — produces one portable interniq-backend.exe
#
# Run from project root:
#   pyinstaller backend\interniq_prod.spec --distpath backend\dist --workpath backend\build_tmp --noconfirm
#
# Output: backend\dist\interniq-backend.exe  (single file, ~25-40 MB)

import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

block_cipher = None

# ── Collect all submodules for framework packages ────────────────────────────
uvicorn_datas,   uvicorn_bins,   uvicorn_hidden   = collect_all('uvicorn')
fastapi_datas,   fastapi_bins,   fastapi_hidden   = collect_all('fastapi')
sqlalchemy_datas, sql_bins,      sql_hidden       = collect_all('sqlalchemy')
starlette_datas, star_bins,      star_hidden      = collect_all('starlette')
pydantic_datas,  pyd_bins,       pyd_hidden       = collect_all('pydantic')
anyio_datas,     anyio_bins,     anyio_hidden     = collect_all('anyio')

all_datas    = uvicorn_datas + fastapi_datas + sqlalchemy_datas + starlette_datas + pydantic_datas + anyio_datas
all_binaries = uvicorn_bins  + fastapi_bins  + sql_bins         + star_bins       + pyd_bins       + anyio_bins
all_hidden   = (
    uvicorn_hidden + fastapi_hidden + sql_hidden + star_hidden + pyd_hidden + anyio_hidden +
    collect_submodules('apscheduler') +
    collect_submodules('httpx') +
    collect_submodules('httpcore') +
    [
        # Uvicorn internals
        'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.main',
        # AnyIO backends
        'anyio._backends._asyncio', 'anyio._backends._trio',
        # python-dotenv
        'dotenv', 'dotenv.main',
        # APScheduler
        'apscheduler', 'apscheduler.triggers.interval', 'apscheduler.triggers.cron',
        'apscheduler.executors.pool', 'apscheduler.jobstores.sqlalchemy',
        # HTTP
        'httpx', 'httpcore', 'h11',
        # HTML parsing
        'bs4', 'soupsieve',
        # Other
        'requests', 'multiprocessing', 'asyncio',
        'pydantic', 'pydantic.v1',
        'email_validator',
    ]
)

a = Analysis(
    # app/main.py is the PyInstaller entry point (formerly backend_entry.py at project root)
    ['app/main.py'],
    # pathex '..' = project root, so 'from backend.config import Config' resolves
    pathex=['..'],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Rust-compiled packages — not needed
        'watchfiles', 'uvloop', 'httptools',
        # Heavy data-science packages — not needed
        'tkinter', 'matplotlib', 'PIL', 'cv2', 'numpy', 'pandas',
        'scipy', 'tensorflow', 'torch',
        # Unused DB drivers
        'psycopg2', 'psycopg2_binary', 'asyncpg', 'motor',
        # Unused AI/LLM packages
        'ollama', 'anthropic', 'openai',
        # Unused GUI
        'wx', 'PyQt5', 'PyQt6',
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── Single-file EXE ───────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='interniq-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,          # Extract to system temp on each run
    console=True,                 # Keep console for logging/debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
