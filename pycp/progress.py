"""This module contains two kinds of ProgressBars.

FilePbar  : one progressbar for each file
GlobalPbar : one progressbar for the whole transfer

"""

from array import array
from fcntl import ioctl
import abc
import os
import signal
import sys
import termios
import time

from pycp.util import pprint_transfer, shorten_path


def cursor_up(file_desc, nb_lines):
    """Move the cursor up by nb_lines"""
    file_desc.write("\033[%dA" % nb_lines)


class Widget(metaclass=abc.ABCMeta):
    """A Widget has a single update()
    method that returns a string

    """
    def __init__(self, line):
        self.line = line
        self.parent = line.parent
        self.fill = False

    @abc.abstractmethod
    def update(self, *args, **kwargs):
        """Called by line.update"""

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
        if res >= 1:
            res = 1
        return res


class FillWidget(Widget, metaclass=abc.ABCMeta):
    """A FillWidget MUST fill the width given
    as parameter of the update() method
    """
    def __init__(self, line):
        Widget.__init__(self, line)
        self.fill = True

    # pylint: disable=arguments-differ
    @abc.abstractmethod
    def update(self, width):
        """Return a string of size width using self.parent

        """


class DoneNumber(Widget):
    """Print '3 on 42' """
    def __init__(self, line):
        Widget.__init__(self, line)

    # pylint: disable=arguments-differ
    def update(self):
        """Overwrite Widget.update """
        done = self.parent.num_files_done
        total = self.parent.num_files
        return "%d on %d" % (done, total)


class FileName(FillWidget):
    """Print the name of the file being transferred. """
    def __init__(self, line):
        FillWidget.__init__(self, line)

    def update(self, width):
        """Overwrite Widget.update """
        short_path = shorten_path(self.parent.file_name, width)
        to_fill = width - len(short_path)
        res = short_path + ' ' * to_fill
        return res


class Line(metaclass=abc.ABCMeta):
    """A Line is a list of Widgets

    """
    def __init__(self, parent):
        self.parent = parent
        self.widgets = list()
        self.fill_indexes = list()

    def set_widgets(self, widgets):
        """Set the widgets of the lines"""
        self.widgets = widgets
        for i, widget in enumerate(self.widgets):
            if isinstance(widget, str):
                continue
            if widget.fill:
                self.fill_indexes.append(i)

    @abc.abstractmethod
    def curval(self):
        """The current value of the line.

        To be implemented using self.parent.
        """

    @abc.abstractmethod
    def maxval(self):
        """The maximum value of the line.

        To be implemented using self.parent.
        """

    @abc.abstractmethod
    def elapsed(self):
        """The elapsed time of the line.

        To be implemented using self.parent.
        """

    def update(self):
        """Call widget.update() for each widget in self.widget,
        dealing with FillWidgets

        """
        res = []
        currwidth = 0
        for widget in self.widgets:
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


class ProgressBar(metaclass=abc.ABCMeta):
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
        try:
            ioctl_out = ioctl(self.fd, termios.TIOCGWINSZ, '\0'*8)
            unused_height, width = array('h', ioctl_out)[:2]
            self.term_width = width
        # self.fd may not be a terminal
        except OSError:
            self.term_width = 80

    def set_lines(self, lines):
        """Set the lines of the ProgressBar """
        self.lines = lines
        self.nb_lines = len(lines)

    def update(self, params):
        """Make sure the ProgressBar is started, then call _update,
        (which should set a few attributes.)

        Then call update() for each line in self.lines.
        The lines should be able to use self.parent to acess the
        attibute of the ProgressBar set during self._update

        """
        if not self.started:
            self.start()
        self._update(params)
        self.display()

    @abc.abstractmethod
    def _update(self, *args):
        """Set the attributes used by line.update()

        """

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


class OneFileProgressLine(Line):
    """A progress line for just one file"""
    def __init__(self, parent):
        Line.__init__(self, parent)
        file_count = FileCountWidget(self,
                                     parent.file_index,
                                     parent.num_files)
        percent = PercentWidget(self)
        file_bar = BarWidget(self)
        file_eta = ETAWidget(self)
        file_speed = FileTransferSpeed(self)
        self.set_widgets([file_count,
                          " ",
                          percent,
                          " ",
                          file_bar,
                          " - ",
                          file_speed,
                          " | ",
                          file_eta])

    def curval(self):
        """Implements Line.curval"""
        return self.parent.file_done

    def maxval(self):
        """Implements Line.maxval"""
        return self.parent.file_size

    def elapsed(self):
        """Implements Line.elapsed"""
        return self.parent.file_elapsed


# pylint: disable=too-many-instance-attributes
class FilePbar(ProgressBar):
    """A file progress bar is initialized with
    a src, a dest, and a size

    """
    # pylint: disable=too-many-arguments
    def __init__(self, src, dest, size, file_index, num_files):
        self.src = src
        self.dest = dest
        self.file_done = 0
        self.file_size = size
        self.start_time = 0
        self.file_elapsed = 0
        self.num_files = num_files
        self.file_index = file_index
        ProgressBar.__init__(self, fd=sys.stderr)
        file_progress_line = OneFileProgressLine(self)
        self.set_lines([file_progress_line])

    def start(self):
        """Print what is going to be transferred,
        initialized self.start_time

        """
        to_print = pprint_transfer(self.src, self.dest)
        self.fd.write(to_print + "\n")
        self.start_time = time.time()
        ProgressBar.start(self)

    # pylint: disable=arguments-differ
    def _update(self, xferd):
        """Implement ProgressBar._update """
        self.file_done += xferd
        if self.file_done > self.file_size:
            # can happen if file grew since the time we computed
            # its size
            self.file_done = self.file_size
        self.file_elapsed = time.time() - self.start_time


class FileProgressLine(Line):
    """A progress line for one file"""
    def __init__(self, parent):
        Line.__init__(self, parent)
        percent = PercentWidget(self)
        file_bar = BarWidget(self)
        file_name = FileName(self)
        file_eta = ETAWidget(self)
        self.set_widgets([percent,
                          " ",
                          file_name,
                          " ",
                          file_bar,
                          " ",
                          file_eta])

    def curval(self):
        """Implement Line.curval"""
        return self.parent.file_done

    def maxval(self):
        """Implement Line.maxval"""
        return self.parent.file_size

    def elapsed(self):
        """Implement Line.elapsed"""
        return self.parent.file_elapsed


class TotalLine(Line):
    """A progress line for the whole transfer """
    def __init__(self, parent):
        Line.__init__(self, parent)
        done_number = DoneNumber(self)
        total_percent = PercentWidget(self)
        total_bar = BarWidget(self)
        total_eta = ETAWidget(self)
        speed = FileTransferSpeed(self)
        self.set_widgets([total_percent,
                          " - ",
                          speed,
                          " - ",
                          total_bar,
                          " - ",
                          done_number,
                          " ",
                          total_eta])

    def curval(self):
        """Implement Line.curval"""
        return self.parent.total_done

    def maxval(self):
        """Implement Line.maxval"""
        return self.parent.total_size

    def elapsed(self):
        """Implement Line.elapsed"""
        return self.parent.total_elapsed


# pylint: disable=too-many-instance-attributes
class GlobalPbar(ProgressBar):
    """The Global progressbar.
    First line is a TotalLine, the second is a FileProgressLine

    """
    def __init__(self, num_files, total_size):
        self.num_files = num_files
        self.num_files_done = 0
        self.file_done = 0
        self.file_size = 0
        self.file_name = ""
        self.file_elapsed = 0
        self.file_start_time = 0
        self.total_size = total_size
        self.total_done = 0
        self.total_elapsed = 0
        self.start_time = 0
        ProgressBar.__init__(self, fd=sys.stderr)
        file_progress_line = FileProgressLine(self)
        total_line = TotalLine(self)
        self.set_lines([total_line, file_progress_line])

    def start(self):
        """Overwrite ProgressBar.start """
        self.start_time = time.time()
        ProgressBar.start(self)

    # pylint: disable=arguments-differ
    def _update(self, xferd):
        """Implement ProgressBar._update """
        self.file_done += xferd
        self.total_done += xferd
        self.file_elapsed = time.time() - self.file_start_time
        self.total_elapsed = time.time() - self.start_time

    def new_file(self, src, size):
        """Called when a new file is being transferred"""
        self.file_name = src
        self.file_done = 0
        self.file_size = size
        self.num_files_done += 1
        self.file_start_time = time.time()


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

        if os.environ.get("PYCP_PACMAN"):
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
        self.units = ['B', 'K', 'M', 'G', 'T', 'P']
        Widget.__init__(self, line)

    # pylint: disable=arguments-differ
    def update(self):
        """Implement Widget.update """
        elapsed = self.line.elapsed()
        curval = self.line.curval()
        if elapsed < 2e-6:
            bps = 0.0
        else:
            bps = float(curval) / elapsed
        spd = bps
        unit = None
        for unit in self.units:
            if spd < 1000:
                break
            spd /= 1000
        return self.fmt % (spd, unit+'/s')


class PercentWidget(Widget):
    """A widget for percentages """
    # pylint: disable=arguments-differ
    def update(self):
        """By default, simply use self.fraction """
        fraction = self.fraction()
        return "%3d%%" % int(fraction * 100)


class FileCountWidget(Widget):
    """ Return something like [ 4/ 10] """
    def __init__(self, line, file_index, num_files):
        Widget.__init__(self, line)
        self.file_index = file_index
        self.num_files = num_files

    # pylint: disable=arguments-differ
    def update(self):
        num_digits = len(str(self.num_files))
        counter_format = "[%{}d/%d]".format(num_digits)
        counter_str = counter_format % (self.file_index, self.num_files)
        return counter_str


class ETAWidget(Widget):
    """A widget to display Estimated Time of Arrival at first,
    and then total time spent when finish.

    """
    def __init__(self, line):
        Widget.__init__(self, line)

    # pylint: disable=arguments-differ
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
