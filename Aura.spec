from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

datas = []
binaries = []
hiddenimports = [
    'aura.body.clipboard',
    'aura.body.desktop',
    'aura.body.filesystem',
    'aura.body.process',
    'aura.body.web',
    'aura.body.apps',
    'aura.body.sysinfo',
    'aura.body.notify',
    'aura.body.schedule',
    'aura.body.workflow',
    'aura.body.vision',
    'aura.body.voice',
    'aura.body.knowledge',
    'aura.body.delegate',
    'aura.body.memory_tools',
    'aura.body.trigger_tools',
    'aura.body.hardware',
    'aura.body.audit',
    'aura.body.confirm',
    'aura.mcp',
    'aura.mcp.client',
    'aura.mcp.server',
    'aura.mcp.config',
    'aura.brain.rag',
    'aura.brain.long_memory',
    'aura.brain.triggers',
    'aura.brain.graph',
    'aura.brain.kernel',
    'aura.brain.researcher',
    'aura.brain.creator',
    'aura.brain.router',
    'aura.brain.llm',
    'aura.brain.context',
    'aura.brain.memory',
    'aura.brain.scheduler',
    'aura.brain.workflows',
    'aura.server.app',
    'aura.server.routes',
    'aura.server.settings_routes',
    'aura.server.upload',
    'aura.server.webhook_routes',
    'aura.plugins',
    'aura.config',
    'aura.commands',
    'aura.models',
    'aura.security',
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
    'starlette',
    'httptools',
    'websockets',
    'pydantic',
    'langchain_core',
    'langchain_openai',
    'langgraph',
    'httpx',
    'psutil',
    'pyperclip',
    'GPUtil',
    'yaml',
    'rich',
    'python_multipart',
    'python_multipart.multipart',
]

# Collect all data, binaries and hiddenimports for main libraries
for pkg in ['uvicorn', 'fastapi', 'starlette', 'python_multipart', 'langchain_core', 'langchain_openai', 'langgraph', 'pydantic', 'httpx', 'rich']:
    tmp_ret = collect_all(pkg)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]
    hiddenimports += collect_submodules(pkg)

# Explicitly include metadata for python-multipart as FastAPI checks for it
datas += copy_metadata('python-multipart')

# Explicitly collect aura submodules
hiddenimports += collect_submodules('aura')


a = Analysis(
    ['aura\\__main__.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy.testing'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='aura-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
