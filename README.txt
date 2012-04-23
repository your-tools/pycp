PYCP: cp and mv with a progressbar
==================================

DESCRIPTION
-----------

pycp / pymv are meant to be used from the command line.

pycp.pbar was heavily based on the wonderful library progressbar by Nilton Volpato.

See man page for detail usage

Screenshot:

  $ pycp -g ~/test/tbbt/ /tmp
   29% -  45.11 M/s - [#########                        ] - 2 on 4 ETA  : 00:00:11
   19% /home/yannick/test/tbbt/t2.avi [#####                     ] ETA  : 00:00:01



INSTALLATION
------------

Simplest way is with just


  easy_install pycp


Pycp is also packaged for the following distributions:

Ubuntu: http://launchpad.net/~yannick-lm/+archive/ppa

ArchLinux : a PKGBUILD is available on AUR


BUGS
----

None known ... yet.
Please report if you find one

SEE ALSO
--------

* If you are looking for a ncurses-based solution, vcp maybe the right choice
  for you http://www.freebsdsoftware.org/sysutils/vcp.html


* If you are looking for a more general solution to display progressbars when
  performing command-line operations, see clpbar: http://clpbar.sourceforge.net/


