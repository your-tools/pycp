#!/usr/bin/env python

from distutils.core import setup
import os
import sys
import pycp
import subprocess


ON_WINDOWS = False

if sys.platform.startswith("win"):
    ON_WINDOWS = True

def gen_man_pages():
    """Simply call help2man bin/pycp """
    man_pages = {}
    for f in ["pycp", "pymv"]:
        try:
            bin = os.path.join("bin", f)
            p = subprocess.Popen("help2man -N %s" %  bin,
                stdout=subprocess.PIPE,
                env = {"PYTHONPATH" : "."},
                shell = True)
            out = p.communicate()[0]
            man_pages[f] = out
        except OSError, e:
            print "help2man failed. Error was", e
            return

    if not os.path.exists("doc"):
        os.mkdir("doc")

    for f in ["pycp", "pymv"]:
        man = os.path.join("doc", f + ".1")
        f_desc = open(man, "w")
        f_desc.write(man_pages[f])
        f_desc.close()
    return man_pages

if not ON_WINDOWS:
    scripts    = ["bin/pycp", "bin/pymv"]
    man_pages = gen_man_pages()
    if man_pages:
        data_files = [("/usr/share/man/man1", ["doc/pycp.1","doc/pymv.1"])]
    else:
        data_files = []

else:
    scripts    = [r"bin\pycp.bat", r"bin\pymv.bat"]
    data_files = []



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
      data_files       = data_files,
      classifiers      = [
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2 :: Only",
        "Topic :: System :: Shells",
      ],

     )
