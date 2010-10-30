"""The mutli progressbar
contains several lines.

It has a single update(*args, **kwargs)
function.

"""
import sys
import time
from array import array
import signal
import termios
from fcntl import ioctl

def cursor_up(fd, nb_lines):
    """Move the cursor up by nb_lines"""
    fd.write("\033[%dA" % nb_lines)


class Widget():
    """A Widget has a single update()
    method that returns a string

    """
    def __init__(self, line):
        self.line = line
        self.parent = line.parent
        self.fill = False

    def update(self):
        raise NotImplementedError()

    def _curval(self):
       return self.line.curval()

    def _maxval(self):
       return self.line.maxval()

    def fraction(self):
        """Must return a float between 0 and 1
        using self.parent

        """
        curval = self._curval()
        maxval = self._maxval()
        if maxval == 0:
            return 0
        if curval == 0:
            return 0
        if curval == maxval:
            return 1
        res = float(curval) / maxval
        assert res > 0
        assert res < 1
        return res

class FillWidget(Widget):
    """A FillWidget MUST fill the width given
    has parameter of the update() method
    """
    def __init__(self, line):
        self.line = line
        self.parent = line.parent
        self.fill = True

    def update(self, width):
        raise NotImplementedError()

class BarWidget(FillWidget):
    """A Bar widget fills the line"""
    def __init__(self, line):
        FillWidget.__init__(self, line)

    def update(self, width):
        fraction = self.fraction()
        cwidth = width - 2
        marked_width = int(fraction * cwidth)
        m = "#"
        res = ("[" + (m*marked_width).ljust(cwidth) + "]")
        return res


class PercentWidget(Widget):
    def update(self):
        fraction = self.fraction()
        return "%3d%%" % int(fraction * 100)

class ETAWidget(Widget):
    def __init__(self, line):
        Widget.__init__(self, line)

    def update(self):
        elapsed = self._elapsed()
        fraction = self.fraction()
        if fraction == 0:
            return "ETA  : --:--:--"
        if fraction == 1:
            return "Time : " + self.format_time(elapsed)
        eta = elapsed / fraction - elapsed
        return "ETA  : " + self.format_time(eta)

    def format_time(self, seconds):
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    def _elapsed(self):
        """Must return the elapsed time, in seconds"""
        return self.line.elapsed()

class Line():
    """A Line is a list of Widgets

    """
    def __init__(self, parent):
        self.parent = parent
        self.widgets = list()

    def set_widgets(self, widgets):
        self.widgets = widgets
        self.fill_indexes = list()
        for i, widget in enumerate(self.widgets):
            if isinstance(widget, str):
                continue
            if widget.fill:
                self.fill_indexes.append(i)

    def curval(self):
        raise NotImplementedError()

    def maxval(self):
        raise NotImplementedError()

    def elapsed(self):
        raise NotImplementedError()

    def update(self):
        res = []
        currwidth = 0
        for i, widget in enumerate(self.widgets):
            if isinstance(widget, str):
                res.append(widget)
                currwidth += len(widget)
                continue
            if widget.fill:
                # Handle this widget later, because we don't
                # know the available width yet
                # But keep filling full_res with the widget
                # value, so that the indexes are consistent,
                # and that we can access the widget later
                res.append(widget)
            else:
                widget_res = widget.update()
                currwidth += len(widget_res)
                res.append(widget_res)
        for fill_index in self.fill_indexes:
            fill_widget = res[fill_index]
            term_width = self.parent.term_width
            # Each fill_widget should fill the same width:
            # (why not?)
            width = (term_width - currwidth) / len(self.fill_indexes)
            widget_res = fill_widget.update(int(width))
            res[fill_index] = widget_res
        return "".join(res)


class MultiProgressBar():
    def __init__(self, fd=sys.stderr):
        self.fd = fd
        self.lines = list()
        self.nb_lines = 0
        self.term_width = 80
        signal.signal(signal.SIGWINCH, self.handle_resize)
        # Call handle_resize once so that self.term_width is
        # correct.
        self.handle_resize(None, None)
        self.started = False

    def start(self):
        self.fd.write("\n" * self.nb_lines)
        self.started = True

    def handle_resize(self, _signum, _frame):
        h,w=array('h', ioctl(self.fd, termios.TIOCGWINSZ, '\0'*8))[:2]
        self.term_width = w

    def set_lines(self, lines):
        self.lines = lines
        self.nb_lines = len(lines)

    def update(self, params):
        if not self.started:
            self.start()
        self._update(params)
        for line in self.lines:
            line.update()

        self.display()

    def _update(self, params):
        raise NotImplementedError()

    def display(self):
        if self.fd is None:
            return
        cursor_up(self.fd, self.nb_lines)
        for line in self.lines:
            self.fd.write("\r" + line.update() + "\n")
        self.fd.flush()
