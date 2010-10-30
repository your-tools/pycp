import sys
import time
from pycp.multipbar import Line, MultiProgressBar
from pycp.multipbar import Widget, BarWidget, ETAWidget, PercentWidget

from pycp.util import pprint_transfer

class OneFileProgressLine(Line):
    def __init__(self, parent):
        Line.__init__(self, parent)
        percent = PercentWidget(self)
        file_bar = BarWidget(self)
        file_eta = ETAWidget(self)
        self.set_widgets([percent,
                         " " ,
                         file_bar,
                         " ",
                         file_eta])
    def curval(self):
        return self.parent.file_done

    def maxval(self):
        return self.parent.file_size

    def elapsed(self):
        return self.parent.file_elapsed

class FilePbar(MultiProgressBar):
    """A file progress bar is initialized with
    a src, a dest, and a size

    """
    def __init__(self, src, dest, size):
        self.src = src
        self.dest = dest
        self.file_done = 0
        self.file_size = size
        MultiProgressBar.__init__(self, fd=sys.stderr)
        file_progress_line = OneFileProgressLine(self)
        self.set_lines([file_progress_line])

    def start(self):
        to_print = pprint_transfer(self.src, self.dest)
        self.fd.write(to_print + "\n")
        self.start_time = time.time()
        MultiProgressBar.start(self)

    def _update(self, xferd):
        self.file_done += xferd
        self.file_elapsed = time.time() - self.start_time

class DoneNumber(Widget):
    def __init__(self, line):
        Widget.__init__(self, line)

    def update(self):
        done = self.parent.num_files_done
        max  = self.parent.num_files
        return "%d on %d" % (done, max)

class FileName(Widget):
    def __init__(self, line):
        Widget.__init__(self, line)

    def update(self):
        return self.parent.file_name

class FileProgressLine(Line):
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
        return self.parent.file_done

    def maxval(self):
        return self.parent.file_size

    def elapsed(self):
        return self.parent.file_elapsed

class TotalLine(Line):
    def __init__(self, parent):
        Line.__init__(self, parent)
        done_number = DoneNumber(self)
        total_percent = PercentWidget(self)
        total_bar = BarWidget(self)
        total_eta = ETAWidget(self)
        self.set_widgets([total_percent,
                         " " ,
                         done_number,
                         " ",
                         total_bar,
                         " ",
                         total_eta])

    def curval(self):
        return self.parent.total_done

    def maxval(self):
        return self.parent.total_size

    def elapsed(self):
        return self.parent.total_elapsed


class GlobalPbar(MultiProgressBar):
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
        MultiProgressBar.__init__(self, fd=sys.stderr)
        file_progress_line = FileProgressLine(self)
        total_line = TotalLine(self)
        self.set_lines([total_line, file_progress_line])

    def start(self):
        self.start_time = time.time()
        MultiProgressBar.start(self)

    def _update(self, xferd):
        self.file_done  += xferd
        self.total_done += xferd
        self.file_elapsed  = time.time() - self.file_start_time
        self.total_elapsed = time.time() - self.start_time

    def new_file(self, src, size):
        self.file_name = src
        self.file_done = 0
        self.file_size = size
        self.num_files_done += 1
        self.file_start_time = time.time()
