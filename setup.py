from setuptools import setup
import os
import sys
import pycp


setup(name='pycp',
      version="7.3",
      description='cp and mv with a progressbar',
      author=" Dimitr Merejkowsky",
      url='http://github.com/dmerejkowsky/pycp',
      packages=['pycp'],
      license='COPYING',
      entry_points={
          "console_scripts": [
              "pycp = pycp.main:main",
              "pymv = pycp.main:main",
            ]
      },
      classifiers=[
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Shells",
      ],
      )
