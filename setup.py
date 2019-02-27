from setuptools import setup
import os
import sys
import pycp


setup(name='pycp',
      version="8.0.7",
      description='cp and mv with a progressbar',
      author="Dimitri Merejkowsky",
      author_email="d.merej@gmail.com",
      url='http://github.com/dmerejkowsky/pycp',
      packages=['pycp'],
      license='COPYING',
      install_requires=[
          "attrs",
      ],
      extras_require={
          "dev": [
              "path.py",
              "pycodestyle",
              "pyflakes",
              "pylint",
              "mccabe",
              "pytest",
              "pytest-mock",
              "bumpversion",
              "twine",
              "wheel",
          ]
      },
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
