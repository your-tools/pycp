pycp: cp and mv with a progressbar
==================================

.. image:: https://travis-ci.org/dmerejkowsky/pycp.svg?branch=master
  :target: https://travis-ci.org/dmerejkowsky/pycp
.. image:: http://img.shields.io/pypi/v/pycp.png
  :target: https://pypi.python.org/pypi/pycp
.. image:: https://img.shields.io/github/license/dmerejkowsky/pycp.svg
  :target: https://github.com/dmerejkowsky/pycp/blob/master/LICENSE


What it looks like:

.. image:: https://dmerej.info/pub/pycp-colors.png
  :target: https://github.com/dmerejkowsky/pycp


See ``pycp --help`` for detailed usage.

Development happens on `github <https://github.com/dmerejkowsky/pycp>`_


Installation
------------

``pycp`` works both for any version greater than Python 3.4, and is installable with
``pip``.


For ``Archlinux,`` a ``PKGBUILD`` is also available on ``AUR``


Notes
-----

* Implementation heavily inspired by the wonderful library ``progressbar`` by Nilton Volpato.

* If you are looking for a ncurses-based solution, vcp maybe the right choice
  for you http://www.freebsdsoftware.org/sysutils/vcp.html

* If you are looking for a more general solution to display progress bars when
  performing command-line operations, see clpbar: http://clpbar.sourceforge.net/
