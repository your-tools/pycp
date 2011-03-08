"""This module contains two kinds of ProgressBars.

FilePbar  : one progressbar for each file
GlobalPbar : one progressbar for the whole transfer

"""

import sys
import time
from pycp.pbar import Line, ProgressBar
from pycp.pbar import Widget, FillWidget, BarWidget, ETAWidget, PercentWidget, FileTransferSpeed

from pycp.util import pprint_transfer, shorten_path

class OneFileProgressLine(Line):
    """A progress line for just one file"""
    def __init__(self, parent):
        Line.__init__(self, parent)
        percent = PercentWidget(self)
        file_bar = BarWidget(self)
        file_eta = ETAWidget(self)
        file_speed = FileTransferSpeed(self)
        self.set_widgets([percent,
                         " " ,
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

class FilePbar(ProgressBar):
    """A file progress bar is initialized with
    a src, a dest, and a size

    """
    def __init__(self, src, dest, size):
        self.src = src
        self.dest = dest
        self.file_done = 0
        self.file_size = size
        self.start_time = 0
        self.file_elapsed = 0
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

    def _update(self, xferd):
        """Implement ProgressBar._update """
        self.file_done += xferd
        self.file_elapsed = time.time() - self.start_time

class DoneNumber(Widget):
    """Print '3 on 42' """
    def __init__(self, line):
        Widget.__init__(self, line)

    def update(self):
        """Overwrite Widget.update """
        done = self.parent.num_files_done
        total  = self.parent.num_files
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
                         " " ,
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
                         " - " ,
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

    def _update(self, xferd):
        """Implement ProgressBar._update """
        self.file_done  += xferd
        self.total_done += xferd
        self.file_elapsed  = time.time() - self.file_start_time
        self.total_elapsed = time.time() - self.start_time

    def new_file(self, src, size):
        """Called when a new file is being transferred"""
        self.file_name = src
        self.file_done = 0
        self.file_size = size
        self.num_files_done += 1
        self.file_start_time = time.time()
