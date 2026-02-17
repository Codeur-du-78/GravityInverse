# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('cube.png', '.'), ('Boutton.png', '.'), ('button.png', '.'), ('Bühnenbild1.png', '.'), ('530448__mellau__whoosh-short-5.wav', '.'), ('614105__kierham__weird-short-impact.wav', '.'), ('523547__lilmati__retro-underwater-coin.wav', '.'), ('spike A.png', '.'), ('spike B.png', '.'), ('spike C.png', '.'), ('spike D.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='GravityInver',
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
