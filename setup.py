from distutils.core import setup
import os
import sys
import pycp
import subprocess


ON_WINDOWS = False

if sys.platform.startswith("win"):
    ON_WINDOWS = True

if not ON_WINDOWS:
    scripts    = ["bin/pycp", "bin/pymv"]
else:
    scripts    = [r"bin\pycp.bat", r"bin\pymv.bat"]

setup(name='pycp',
      version          = pycp.__version__,
      description      = 'cp with a progressbar',
      long_description = pycp.__doc__,
      author           = pycp.__author__,
      author_email     = pycp.__author_email__,
      url              = 'http://github.com/yannicklm/pycp',
      packages         = ['pycp'],
      license          ='COPYING',
      scripts          = scripts,
      classifiers      = [
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2 :: Only",
        "Topic :: System :: Shells",
      ],

     )
