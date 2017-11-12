8.0.6
-----

* Fix packaging issue: ``pycp`` wheels are no longer universal.

8.0.5
-----

* Fix crash in ``pycp -g``. Reported by @z1lt0id

8.0.4
-----

* Partial revert of 8.0.3: ``pycp`` is now still fast even with just one CPU


8.0.3
-----

* Performance improvements (see #20). We are now faster than v7 :)
  Note that ``pycp`` will be still be slow if only one CPU is available.

8.0.2
-----

* Packaging fixes

8.0.1
----

* Fix calling ``--version`` is some corner cases.

8.0
---

* New feature: colors by default.

  I'd like to thank @schvabodka-man for giving me the opportunity to
  refactor code that was more than 7 years old :)

* Breaking change: remove ``--all`` see `#19 <https://github.com/dmerejkowsky/pycp/issues/19>`_
  for details.
* Drop Windows support
* Drop Python2 support
* Massive refactoring
* Stricter CI

7.3
---
* Try to preserve user and group when used with ``-p,--preserve``
* Optimization : read source file size only once
* Fix crash when file size increases while it's being copied

7.2.2
-----
* Include test/test_dir/ in source package. This
  makes it possible for pycp packages to run the tests

7.2.1
-----
* Fix README. (version bump required for updating
  pypi page)

7.2
---
* Bring back Python2.7 compatibily. Why not ?
* Display a file count even when not using ``-g``

7.1
---
* Fix classifiers

7.0
---
* port to Python3
* switch to setuptools for the packaging

6.1
---
* improve symlink support

6.0
---
* massive refactoring
* pycp no longer depends on progressbar
* add pycp -g option to display a global progress bar on
  several lines

5.0
---
* massive refactoring
* pycp no longer uses threading code.
  copying small files should now be painless
  (no more time.sleep)
* pycp learned --all and --preserve options
* change license from GPL to BSD

4.3.3
-----
* pycp no longer hangs when copy fails.
* error code is non zero when serious problems occurs.

4.3.2
-----

Bug fixes concerning small and empty files

4.3.1
-----
Bug fix: ``pymv a_dir b_dir`` left an empty ``a_dir`` behind

4.3
----
Nicer print of what is being transfered::

  /path/to/{foo => bar}/a/b

instead of::

  /path/to/foo/a/b -> /path/to/bar/a/b

4.2
---
Pycp now is available on Pypi:
http://pypi.python.org/pypi/pycp/

4.1
---
You can now use --safe to never overwrite files.

4.0.2
-----
Lots of bug fixes, introducing automatic tests

4.0.1
------
Fix bug for Python2.5: threading module still has
only camelCase functions.

4.0
----
Now using ``shutil`` and ``thread`` modules instead of ``subprocess``.
(Replacing ``supbrocess.popen("/bin/cp")`` by calling a thread
running ``shutil.copy``)
Bonus: pycp might become cross-platform

3.2
----
Switch from ``getopt`` to ``OptionParser`` (much better)

3.1
---
* Now using ``/bin/cp`` instead of ``cp`` (thanks, Chris Gilles)

* No more ``-o`` option. Files are now overwritten by default.
  Pass a ``-i,--interactive``  option if you want to be asked
  for confirmation before overwritting files

* Mimic ``cp`` behaviour. (thanks, ctaf)

3.0
---
Little trick to have a ``pymv``

2.2
---
* Skips existing files instead of canceling whole operation
* Implementing ``-o,--overwrite`` option.

2.1
---
Able to copy multiple files::

  pycp bar foo /path/to/baz

2.0
----
Now able to copy recursively files!

1.3
----
Add an ETA and file speed estimation

1.2
---
* Fix possible division by zero
* Fix possible race condition

1.1
---
Add a proper license

1.0
---
Initial commit
