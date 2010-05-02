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
            p = subprocess.Popen(["help2man", "-N", bin], stdout=subprocess.PIPE)
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

if not ON_WINDOWS:
    gen_man_pages()
    data_files = [ ("/usr/share/man/man1", ["doc/pycp.1","doc/pymv.1"]) ],
    scripts    = ["bin/pycp", "bin/pymv"],

else:
    data_files = []
    scripts    = ["bin/pycp.bat", "bin/pymv.bat"],



setup(name='pycp',
      version          = pycp.__version__,
      description      = 'cp with a progressbar',
      long_description = pycp.__doc__,
      requires         = ['progressbar'],
      author           = pycp.__author__,
      author_email     = pycp.__author_email__,
      url              = 'http://sd-5791.dedibox.fr/prog/pycp.txt',
      py_modules       = ['pycp'],
      license          =' GPL',
      scripts          = scripts,
      data_files       = data_files,
     )
