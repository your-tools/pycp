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
import pycp

def cursor_up(file_desc, nb_lines):
    """Move the cursor up by nb_lines"""
    file_desc.write("\033[%dA" % nb_lines)


class Widget():
    """A Widget has a single update()
    method that returns a string

    """
    def __init__(self, line):
        self.line = line
        self.parent = line.parent
        self.fill = False

    def update(self):
        """Called by line.update"""
        raise NotImplementedError()

    def curval(self):
        """Returns the current value.
        By default, calls line.curval()

        """
        return self.line.curval()

    def maxval(self):
        """Returns the maximum value.
        By default, calls line.maxval()

        """
        return self.line.maxval()

    def fraction(self):
        """Must return a float between 0 and 1
        using self.parent

        """
        curval = self.curval()
        maxval = self.maxval()
        if maxval == 0 and curval == 0:
            return 1
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
        Widget.__init__(self, line)
        self.fill = True

    def update(self, width):
        """Return a string of size width using self.parent

        """
        raise NotImplementedError()

class BarWidget(FillWidget):
    """A Bar widget fills the line"""
    def __init__(self, line):
        FillWidget.__init__(self, line)

    def update(self, width):
        """Create a progress bar of size width, looking like
        [#####   ]

        or if I like candy
        [--Co  o ]
        """
        fraction = self.fraction()
        cwidth = width - 2
        marked_width = int(fraction * cwidth)

        if pycp.options.chomp:
            marker = "-"
            if marked_width == cwidth:
                res = marker * marked_width
            else:
                if marked_width % 2:
                    pacman = "\033[1;33mc\033[m"
                else:
                    pacman = "\033[1;33mC\033[m"
                pac_dots = (" o " * (1 + cwidth // 3))[marked_width + 1:cwidth]
                markers = marker * marked_width
                res = markers + pacman + "\033[0;37m" + pac_dots + "\033[m"
        else:
            marker = "#"
            res = (marker * marked_width).ljust(cwidth)
        return "[%s]" % res

class FileTransferSpeed(Widget):
    "Widget for showing the transfer speed (useful for file transfers)."
    def __init__(self, line):
        self.fmt = '%6.2f %s'
        self.units = ['B','K','M','G','T','P']
        Widget.__init__(self, line)

    def update(self):
        """Implement Widget.update """
        elapsed = self.line.elapsed()
        curval = self.line.curval()
        if elapsed < 2e-6:#== 0:
            bps = 0.0
        else:
            bps = float(curval) / elapsed
        spd = bps
        for u in self.units:
            if spd < 1000:
                break
            spd /= 1000
        return self.fmt % (spd, u+'/s')

class PercentWidget(Widget):
    """A widget for percentages """
    def update(self):
        """By default, simply use self.fraction """
        fraction = self.fraction()
        return "%3d%%" % int(fraction * 100)

class ETAWidget(Widget):
    """A widget to display Estimated Time of Arrival at first,
    and then total time spent when finish.

    """
    def __init__(self, line):
        Widget.__init__(self, line)

    def update(self):
        """Implement Widget.update """
        elapsed = self.elapsed()
        fraction = self.fraction()
        if fraction == 0:
            return "ETA  : --:--:--"
        if fraction == 1:
            return "Time : " + self.format_time(elapsed)
        eta = elapsed / fraction - elapsed
        return "ETA  : " + self.format_time(eta)

    @staticmethod
    def format_time(seconds):
        """Simple way of formating time """
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    def elapsed(self):
        """Must return the elapsed time, in seconds.
        By default, call self.line.elapsed.
        """
        return self.line.elapsed()

class Line():
    """A Line is a list of Widgets

    """
    def __init__(self, parent):
        self.parent = parent
        self.widgets = list()

    def set_widgets(self, widgets):
        """Set the widgets of the lines"""
        self.widgets = widgets
        self.fill_indexes = list()
        for i, widget in enumerate(self.widgets):
            if isinstance(widget, str):
                continue
            if widget.fill:
                self.fill_indexes.append(i)

    def curval(self):
        """The current value of the line.

        To be implemented using self.parent.
        """
        raise NotImplementedError()

    def maxval(self):
        """The maximum value of the line.

        To be implemented using self.parent.
        """
        raise NotImplementedError()

    def elapsed(self):
        """The elapsed time of the line.

        To be implemented using self.parent.
        """
        raise NotImplementedError()

    def update(self):
        """Call widget.update() for each widget in self.widget,
        dealing with FillWidgets

        """
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


class ProgressBar():
    """A ProgressBar is simply a list of Lines

    """
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
        """Called at the first update() if not already called before.

        To be overloaded like this:
        class MyPbar
           ...

           def start(self):
               self.start_time = ....

               ProgressBar.start(self)

        """
        self.fd.write("\n" * self.nb_lines)
        self.started = True
        self.update(0)

    def handle_resize(self, _signum, _frame):
        """When the term is resized, a siganl is send.
        Catch it and update self.term_width

        """
        height_, width =array('h', ioctl(self.fd, termios.TIOCGWINSZ, '\0'*8))[:2]
        self.term_width = width

    def set_lines(self, lines):
        """Set the lines of the ProgressBar """
        self.lines = lines
        self.nb_lines = len(lines)

    def update(self, params):
        """Make sure the ProgressBar is started, then call _update,
        (which should set a few attributes.)

        Then call update() for each line in self.lines.
        The lines should be able to use self.parent to acess the
        attibute of the PogressBar set during self._update

        """
        if not self.started:
            self.start()
        self._update(params)
        self.display()

    def _update(self, params):
        """Set the attributes used by line.update()

        """
        raise NotImplementedError()

    def display(self):
        """Display the lines, taking care of always moving
        the cursor up before printing new lines

        """
        if self.fd is None:
            return
        cursor_up(self.fd, self.nb_lines)
        for line in self.lines:
            self.fd.write("\r" + line.update() + "\n")
        self.fd.flush()
