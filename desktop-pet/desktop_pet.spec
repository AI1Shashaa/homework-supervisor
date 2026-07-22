# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 规格：生成可双击运行的 DesktopPet.exe"""

from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "assets" / "cat.png"), "assets"),
        (str(root / "assets" / "cat_body.png"), "assets"),
        (str(root / "assets" / "cat_head.png"), "assets"),
        (str(root / "assets" / "cat_tail.png"), "assets"),
        (str(root / "assets" / "layers.json"), "assets"),
        (str(root / "assets" / "icon.png"), "assets"),
    ],
    hiddenimports=[],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="DesktopPet",
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
    icon=str(root / "assets" / "icon.png"),
)
