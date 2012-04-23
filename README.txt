PYCP: cp and mv with a progressbar
==================================

DESCRIPTION
-----------

pycp / pymv are meant to be used from the command line.

pycp.pbar was heavily based on the wonderful library progressbar by Nilton Volpato.

See man page for detail usage

Screenshot:

::

  $ pycp -g ~/test/tbbt/ /tmp
   29% -  45.11 M/s - [#########                        ] - 2 on 4 ETA  : 00:00:11
   19% /home/yannick/test/tbbt/t2.avi [#####                     ] ETA  : 00:00:01



INSTALLATION
------------

  easy_install pycp

is probably the easiest way.


There are also other ways to install pycp:
* Linux:

Ubuntu: there are also pycp packages on this PPA:
http://launchpad.net/~yannick-lm/+archive/ppa

ArchLinux : a PKGBUILD is available on AUR:
http://aur.archlinux.org/packages.php?ID=29319


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


