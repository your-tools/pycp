PYCP: cp and mv with a progressbar
==================================

.. image:: https://travis-ci.org/yannicklm/pycp.svg?branch=master
  :target: https://travis-ci.org/yannicklm/pycp
.. image:: http://img.shields.io/pypi/v/pycp.png
  :target: https://pypi.python.org/pypi/pycp

DESCRIPTION
-----------

``pycp`` / ``pymv`` are meant to be used from the command line.

``pycp.pbar`` was heavily based on the wonderful library ``progressbar`` by Nilton Volpato.

See man page for detail usage

Screenshot::

  $ pycp -g ~/test/tbbt/ /tmp
   29% -  45.11 M/s - [#########                        ] - 2 on 4 ETA  : 00:00:11
   19% /home/yannick/test/tbbt/t2.avi [#####                     ] ETA  : 00:00:01



INSTALLATION
------------

``pycp`` works both for Python2.7 and Python3, and is installable with
``pip``.


For ``Archlinux,`` a ``PKGBUILD`` is also available on ``AUR``


BUGS
----

See `github bug tracker <https://github.com/yannicklm/pycp/issues>`_

CHANGELOG
----------

See `here <https://raw.githubusercontent.com/yannicklm/pycp/master/Changelog.rst>`_


SEE ALSO
--------

* If you are looking for a ncurses-based solution, vcp maybe the right choice
  for you http://www.freebsdsoftware.org/sysutils/vcp.html


* If you are looking for a more general solution to display progress bars when
  performing command-line operations, see clpbar: http://clpbar.sourceforge.net/
