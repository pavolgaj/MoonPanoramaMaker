# -*- mode: python -*-

block_cipher = None


a = Analysis(['moon_panorama_maker.py'],
             pathex=['/home/rolf/Pycharm-Projects/MoonPanoramaMaker/Source'],
             binaries=[],
             datas=[( 'landmark_pictures', 'landmark_pictures' ),
                    ( '../InstallForge/plugins', 'plugins' ),
                    ( '../Documentation/MoonPanoramaMaker_User-Guide.pdf', '.' ),
                    ( '../Documentation/Illustrations/MoonPanoramaMaker.jpg', '.' )
                    ],
             hiddenimports=['sklearn.neighbors.typedefs',
                            'sklearn.tree',
                            'sklearn.tree._utils',
                            'sklearn.neighbors.quad_tree',
                            'scipy._lib.messagestream',
                            ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='MoonPanoramaMaker',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='MoonPanoramaMaker')
