# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Tournoi LJTT — produces a single self-contained Windows .exe."""
from pathlib import Path

SPEC_DIR = Path(SPECPATH)

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(SPEC_DIR)],
    binaries=[],
    datas=[
        # Bundle the assets folder (logo.png lives here once you drop it in)
        ('src/assets', 'src/assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude PyQt6 modules we don't need to slim the binary
        'PyQt6.QtNetwork',
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtMultimedia',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtSql',
        'PyQt6.QtTest',
        'PyQt6.QtDBus',
        'PyQt6.QtBluetooth',
        'PyQt6.QtPositioning',
        'PyQt6.QtSensors',
        'PyQt6.QtSerialPort',
        'PyQt6.QtNfc',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Use the logo as icon if it exists (must be .ico on Windows)
_icon_path = SPEC_DIR / 'src' / 'assets' / 'icon.ico'
icon = str(_icon_path) if _icon_path.exists() else None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TournoiLJTT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # no console window (windowed app)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)
