#!/usr/bin/env python

from distutils.core import setup
import pycp

setup(name='pycp',
      version= pycp.__version__,
      description='cp with a progressbar',
      long_description = pycp.__doc__,
      requires=['progressbar'],
      author=pycp.__author__,
      author_email=pycp.__author_email__,
      url='http://gitorious.org/projects/pycp',
      py_modules=['pycp'],
      license='GPL', 
      platforms=['Linux'],
      scripts = ["pycp"]
     )
