# TODO

* fix pylint: disable stuff
* reduce cyclomatic complexity
* pycp/transfer.py: use polymorphism instead of 'if' statements to
  use global or one line progress indicators
* restore candy !
* factorize code for displaying just progress of just on file
  (global pbar second line is exactly the OneFileIndicator line, with an additional Filename widget
* get rid of start() ?
* turn state into a class ?
* fix bug when *reducing* term size ?
* throttle screen refresh (increasing buffer size won't do the trick)
* async I/O
