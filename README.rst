pycp: cp and mv with a progressbar
==================================

.. image:: http://img.shields.io/pypi/v/pycp.png
  :target: https://pypi.python.org/pypi/pycp


What it looks like:

.. image:: https://raw.githubusercontent.com/your-tools/pycp/master/scrot/pycp.png
  :target: https://github.com/your-tools/pycp


See ``pycp --help`` for detailed usage.

Development happens on `github <https://github.com/your-tools/pycp>`_


Installation
------------

``pycp`` works both for any version greater than Python 3.4, and is installable with
``pip``.


For ``Archlinux,`` a ``PKGBUILD`` is also available on ``AUR``


Notes
-----

* Implementation heavily inspired by the wonderful library ``progressbar`` by Nilton Volpato.

* I also maintain a similar tool written in rust called `rusync <https://github.com/your-tools/rusync>`_. It has a different set of features (so you may want to stick with pycpy), but is much faster.

* If you are looking for a ncurses-based solution, vcp maybe the right choice
  for you http://www.freebsdsoftware.org/sysutils/vcp.html

* If you are looking for a more general solution to display progress bars when
  performing command-line operations, see clpbar: http://clpbar.sourceforge.net/
