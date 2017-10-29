import abc
import itertools
import shutil
import time
import sys

import attr
import ui

import pycp.util


def cursor_up(nb_lines):
    """Move the cursor up by nb_lines"""
    sys.stdout.write("\033[%dA" % nb_lines)
    sys.stdout.flush()


def get_fraction(current_value, max_value):
    if max_value == 0 and current_value == 0:
        return 1
    if max_value == 0:
        return 0
    if current_value == 0:
        return 0
    if current_value == max_value:
        return 1
    return float(current_value) / max_value


class Component(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def render(self, props):
        pass


class FixedWidthComponent(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def render(self, props, width):
        pass


class Counter(Component):
    def render(self, props):
        index = props["index"]
        count = props["count"]
        num_digits = len(str(count))
        counter_format = "[%{}d/%d]".format(num_digits)
        return [counter_format % (index, count)]


class Percent(Component):
    def render(self, props):
        current_value = props["current_value"]
        max_value = props["max_value"]
        fraction = get_fraction(current_value, max_value)
        return ["%3d%%" % int(fraction * 100)]


class Bar(FixedWidthComponent):
    def render(self, props, width):
        current_value = props["current_value"]
        max_value = props["max_value"]

        marker = "#"
        fraction = get_fraction(current_value, max_value)
        cwidth = width - 2
        marked_width = int(fraction * cwidth)
        res = (marker * marked_width).ljust(cwidth)
        return ["[%s]" % res]


class Speed(Component):
    def render(self, props):
        elapsed = props["elapsed"]
        current_value = props["current_value"]
        if elapsed < 2e-6:
            bits_per_second = 0.0
        else:
            bits_per_second = float(current_value) / elapsed
        speed = bits_per_second

        units = ['B', 'K', 'M', 'G', 'T', 'P']
        unit = None
        for unit in units:
            if speed < 1000:
                break
            speed /= 1000
        speed_format = "%.2f %s"

        return [speed_format % (speed, unit + "/s")]


class ETA(Component):
    @classmethod
    def get_eta(cls, fraction, elapsed):
        if fraction == 0:
            return "ETA  : --:--:--"
        if fraction == 1:
            return "Time : " + cls.format_time(elapsed)
        eta = elapsed / fraction - elapsed
        return cls.format_time(eta)

    @staticmethod
    def format_time(seconds):
        """Simple way of formating time """
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    def render(self, props):
        elapsed = props["elapsed"]
        current_value = props["current_value"]
        max_value = props["max_value"]
        fraction = get_fraction(current_value, max_value)
        eta = self.get_eta(fraction, elapsed)
        return [eta]


class Filename(Component):
    def render(self, props):
        filename = props["filename"]
        return [pycp.util.shorten_path(filename, 40)]


@attr.s
class FixedTuple:
    index = attr.ib()
    component = attr.ib()


def tokens_length(tokens):
    _, without_color = ui.process_tokens(tokens, end="", sep="")
    return len(without_color)


class Line():
    def __init__(self):
        self.components = list()
        self.fixed = None

    def set_components(self, components):
        self.components = components
        fixed = list()
        for (i, component) in enumerate(components):
            if isinstance(component, FixedWidthComponent):
                fixed.append(FixedTuple(i, component))
        assert len(fixed) == 1, "Expecting exactly one fixed width component"
        self.fixed = fixed[0]

    def render(self, **kwargs):
        accumulator = [None] * len(self.components)
        term_width = shutil.get_terminal_size().columns
        current_width = 0
        for i, component in enumerate(self.components):
            if i == self.fixed.index:
                continue
            elif isinstance(component, Component):
                tokens = component.render(kwargs)
                accumulator[i] = tokens
                current_width += tokens_length(tokens)
            elif isinstance(component, ui.Color):
                accumulator[i] = [component]
            else:
                accumulator[i] = [component]
                current_width += len(component)

        fixed_width = term_width - current_width
        accumulator[self.fixed.index] = self.fixed.component.render(kwargs, fixed_width)

        return list(itertools.chain.from_iterable(accumulator))


# pylint: disable=too-many-instance-attributes
class OneFileIndicator():
    def __init__(self, num_files):
        self.num_files = num_files
        self.index = 0
        self.done = 0
        self.size = 0
        self.start_time = 0
        percent = Percent()
        bar = Bar()
        speed = Speed()
        eta = ETA()
        self.line = Line()
        self.line.set_components([
            ui.blue, percent, ui.reset, " ",
            ui.lightgray, bar, ui.reset, " - ",
            ui.standout, speed, ui.reset, " | ",
            ui.brown, eta, ui.reset
        ])

    def on_new_file(self, src, dest, size):
        self.done = 0
        self.size = size
        self.index += 1
        self.start_time = time.time()
        tokens = list()
        counter = Counter()
        counter_tokens = counter.render({
            "index": self.index,
            "count": self.num_files,
        })
        colored_transfer = pycp.util.pprint_transfer(src, dest)
        tokens = [ui.blue] + counter_tokens + [" "] + colored_transfer
        ui.info(*tokens, end="\n", sep="")
        tokens = self.line.render(
            current_value=0,
            elapsed=0,
            max_value=size)
        ui.info(*tokens, end="\r", sep="")

    # pylint: disable=no-self-use
    def stop(self):
        ui.info("")

    def on_file_transfer(self, value):
        elapsed = time.time() - self.start_time
        self.done += value
        tokens = self.line.render(
            index=self.index,
            count=self.num_files,
            current_value=self.done,
            elapsed=elapsed,
            max_value=self.size)
        ui.info(*tokens, end="\r", sep="")

    # pylint: disable=no-self-use
    def on_file_done(self):
        ui.info("")


# # pylint: disable=too-many-instance-attributes
class GlobalIndicator:
    def __init__(self, num_files, total_size):
        self.num_files = num_files
        self.total_size = total_size
        self.total_done = 0
        self.total_start = 0
        self.total_elapsed = 0

        self.index = 0
        self.count = 0
        self.file_done = 0
        self.file_size = 0
        self.file_start = 0
        self.file_elapsed = 0
        self.file_src = None

        self.first_line = self.build_first_line()
        self.second_line = self.build_second_line()

    @staticmethod
    def build_first_line():
        res = Line()
        counter = Counter()
        percent = Percent()
        bar = Bar()
        eta = ETA()
        res.set_components([
            ui.green, counter, ui.reset, " ",
            ui.blue, percent, ui.reset, " - ",
            ui.lightgray, bar, ui.reset, " - ",
            ui.brown, eta, ui.reset,
        ])
        return res

    @staticmethod
    def build_second_line():
        res = Line()
        percent = Percent()
        bar = Bar()
        eta = ETA()
        speed = Speed()
        filename = Filename()
        res.set_components([
            ui.blue, percent, ui.reset, " ",
            ui.bold, filename, ui.reset, " ",
            ui.lightgray, bar, ui.reset, " - ",
            ui.standout, speed, ui.reset, " | ",
            ui.brown, eta, ui.reset,
        ])
        return res

    def start(self):
        self.total_start = time.time()
        tokens = self.first_line.render(
            index=self.index,
            count=self.num_files,
            current_value=0,
            elapsed=0,
            max_value=self.total_size)
        ui.info(*tokens, end="\n", sep="")

    def _render_first_line(self):
        total_elapsed = time.time() - self.total_start
        tokens = self.first_line.render(
            index=self.index,
            count=self.num_files,
            current_value=self.total_done,
            elapsed=total_elapsed,
            max_value=self.total_size)
        cursor_up(2)
        ui.info("\r", *tokens, end="\n", sep="")

    def _render_second_line(self):
        file_elapsed = time.time() - self.file_start
        tokens = self.second_line.render(
            current_value=self.file_done,
            max_value=self.file_size,
            elapsed=file_elapsed,
            filename=self.file_src,
        )
        ui.info("\r", *tokens, end="\n", sep="")

    def on_new_file(self, src, unused_dest, size):
        self.index += 1
        self._render_first_line()

        self.file_done = 0
        self.file_size = size
        self.file_start = time.time()
        self.file_src = src
        self._render_second_line()

    def on_file_transfer(self, value):
        self.total_done += value
        self._render_first_line()

        self.file_done += value
        self._render_second_line()

    def on_file_done(self):
        pass

    def stop(self):
        pass
