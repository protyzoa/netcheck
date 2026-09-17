# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for NetCheck."""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect dnspython data files
datas = [
    # i18n JSON files
    ('netcheck/i18n/*.json', 'netcheck/i18n'),
]

# Collect all dnspython submodules (needed for DNS resolution)
hidden_imports = collect_submodules('dns') + [
    'psutil',
    'PyQt6',
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
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
    name='NetCheck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Add .ico path here if you have an icon
)

