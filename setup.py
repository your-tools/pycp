from setuptools import setup
import os
import sys
import pycp


setup(name='pycp',
      version          = pycp.__version__,
      description      = 'cp and mv with a progressbar',
      author           = pycp.__author__,
      author_email     = pycp.__author_email__,
      url              = 'http://github.com/yannicklm/pycp',
      packages         = ['pycp'],
      license          ='COPYING',
      entry_points     = {
          "console_scripts" : [
              "pycp  = pycp.main:main",
              "pymv  = pycp.main:main",
            ]
      },
      classifiers      = [
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Shells",
      ],

     )
