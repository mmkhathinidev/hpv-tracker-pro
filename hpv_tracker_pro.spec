# -*- mode: python ; coding: utf-8 -*-
# Build mode: onedir (portable folder) — significantly faster startup than onefile
# because no temporary extraction is needed on launch.
# To build: pyinstaller hpv_tracker_pro.spec

block_cipher = None

a = Analysis(
    ['hpv_tracker_pro.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icons', 'icons'),
    ],
    hiddenimports=[
        'reportlab.lib.pagesizes',
        'reportlab.lib.colors',
        'reportlab.lib.units',
        'reportlab.platypus',
        'reportlab.lib.styles',
        'reportlab.lib.enums',
        'reportlab.pdfgen.canvas',
        'docx',
        'docx.shared',
        'docx.enum.text',
        'docx.enum.table',
        'docx.oxml',
        'docx.oxml.ns',
        'docx.oxml.shared',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
    ],
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
    [],                         # No binaries/datas here in onedir mode
    exclude_binaries=True,      # Required for onedir: binaries go into COLLECT
    name='HPV_Tracker_Pro',
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
    icon=None,
)

# COLLECT bundles the exe + all dependencies into a single portable folder
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HPV_Tracker_Pro',    # Output folder: dist/HPV_Tracker_Pro/
)