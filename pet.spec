# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置：把 sakuyi_pet.py + assets5 打成单个 exe
# 用法：pyinstaller pet.spec  （产物在 dist/ 目录）

a = Analysis(['sakuyi_pet.py'],
             pathex=[],
             binaries=[],
             datas=[('assets5', 'assets5')],   # 把素材文件夹打进 exe
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
          name='sakuyi_pet',
          debug=False,
          strip=False,
          upx=False,
          console=False,        # 双击运行不弹黑色控制台窗口
          icon=None)            # 有 .ico 图标的话填在这里
