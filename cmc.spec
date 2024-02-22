# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['com_mate_converter\\__main__.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('com_mate_converter\\css\\cmc.css', 'com_mate_converter\\css\\'),
        ('com_mate_converter\\locale\\zh_CN\\LC_MESSAGES\\com-mate-converter.mo', 'com_mate_converter\\locale\\zh_CN\\LC_MESSAGES\\'),
        ('cmc.ico', '.')
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
    a.datas,
    [],
    name='cmc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version.txt',
    icon='cmc.ico',
)
