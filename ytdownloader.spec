# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# yt_dlp·customtkinter는 동적 로딩이 많아 전체 수집
_datas = []
_binaries = []
_hiddenimports = []
for _pkg in ("yt_dlp", "customtkinter"):
    d, b, h = collect_all(_pkg)
    _datas += d
    _binaries += b
    _hiddenimports += h

a = Analysis(
    ["ytdownloader.py"],
    pathex=[],
    binaries=_binaries,
    datas=_datas,
    hiddenimports=_hiddenimports,
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
    name="ytdownloader",
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
