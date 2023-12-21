from dataclasses import dataclass
import abc
import os
import shutil
import sys
import time
import typing


class Progress:
    def __init__(self) -> None:
        self.total_done = 0
        self.total_size = 0
        self.total_elapsed = 0.0

        self.index = 0
        self.count = 0
        self.src = ""
        self.dest = ""
        self.file_done = 0
        self.file_size = 0
        self.file_start = 0.0
        self.file_elapsed = 0.0


def cursor_up(nb_lines: int) -> None:
    """Move the cursor up by nb_lines"""
    sys.stdout.write("\033[%dA" % nb_lines)
    sys.stdout.flush()


def get_fraction(current_value: int, max_value: int) -> float:
    if max_value == 0 and current_value == 0:
        return 1
    if max_value == 0:
        return 0
    if current_value == 0:
        return 0
    if current_value == max_value:
        return 1
    return float(current_value) / max_value


def human_readable(size: int) -> str:
    """Build a nice human readable string from a size given in
    bytes

    """
    if size < 1024**2:
        hreadable = float(size) / 1024.0
        return "%.0fK" % hreadable
    elif size < (1024**3):
        hreadable = float(size) / (1024**2)
        return "%.1fM" % round(hreadable, 1)
    else:
        hreadable = float(size) / (1024.0**3)
        return "%.2fG" % round(hreadable, 2)


def shorten_path(path: str, length: int) -> str:
    """Shorten a path so that it is never longer
    that the given length

    """
    if len(path) < length:
        return path
    if os.path.sep not in path:
        return shorten_string(path, length)

    short_base = ""
    if path.startswith(os.path.sep):
        short_base = os.path.sep
        path = path[1:]
    parts = path.split(os.path.sep)
    short_base += os.path.sep.join([p[0] for p in parts[:-1]])
    if len(short_base) > length:
        short_base = ""

    # Shorten the last part:
    short_name = parts[-1]
    last_length = length - len(short_base)
    if short_base:
        last_length = last_length - 1
    short_name = shorten_string(short_name, last_length)
    return os.path.join(short_base, short_name)


def shorten_string(input_string: str, length: int) -> str:
    """Shorten a string in a nice way:

    >>> shorten_string("foobar", 5)
    'fo...'
    """
    if len(input_string) < length:
        return input_string
    if length > 3:
        return input_string[: length - 3] + "..."
    if length == 3:
        return input_string[0] + ".."
    if length == 2:
        return input_string[0] + "."
    if length == 1:
        return input_string[0]
    return ""


def describe_transfer(src: str, dest: str) -> typing.Tuple[str, str, str, str]:
    """Returns pfx, src_mid, dest_mid, sfx, the 4 components
    required to build the "foo/{bar => baz}/qux" string

    """
    # Note: directly borrowed from git's diff.c file.
    len_src = len(src)
    len_dest = len(dest)

    # Find common prefix
    pfx_length = 0
    i = 0
    j = 0
    while i < len_src and j < len_dest and src[i] == dest[j]:
        if src[i] == os.path.sep:
            pfx_length = i + 1
        i += 1
        j += 1

    # Find common suffix
    sfx_length = 0
    i = len_src - 1
    j = len_dest - 1
    while i > 0 and j > 0 and src[i] == dest[j]:
        if src[i] == os.path.sep:
            sfx_length = len_src - i
        i -= 1
        j -= 1

    src_midlen = len_src - pfx_length - sfx_length
    dest_midlen = len_dest - pfx_length - sfx_length

    pfx = src[:pfx_length]
    sfx = dest[len_dest - sfx_length :]
    src_mid = src[pfx_length : pfx_length + src_midlen]
    dest_mid = dest[pfx_length : pfx_length + dest_midlen]

    if pfx == os.path.sep:
        # The common prefix is / ,
        # avoid print /{etc => tmp}/foo, and
        # print {/etc => /tmp}/foo
        pfx = ""
        src_mid = os.path.sep + src_mid
        dest_mid = os.path.sep + dest_mid

    return pfx, src_mid, dest_mid, sfx


Props = typing.Dict[str, typing.Any]
SizedString = typing.Tuple[int, str]


class Component(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def render(self, props: Props) -> SizedString:
        """Should return a tuple with a length and a string"""


class AnsiEscapeSequence(Component):
    seq = "\0"

    def render(self, props: Props) -> SizedString:
        return 0, self.seq


class Blue(AnsiEscapeSequence):
    seq = "\x1b[34;1m"


class Bold(AnsiEscapeSequence):
    seq = "\x1b[1m"


class Brown(AnsiEscapeSequence):
    seq = "\x1b[33m"


class Green(AnsiEscapeSequence):
    seq = "\x1b[32;1m"


class LightGray(AnsiEscapeSequence):
    seq = "\x1b[37m"


class Reset(AnsiEscapeSequence):
    seq = "\x1b[0m"


class Standout(AnsiEscapeSequence):
    seq = "\x1b[3m"


class Yellow(AnsiEscapeSequence):
    seq = "\x1b[33;1m"


class Text(Component):
    def __init__(self, text: str) -> None:
        self.text = text

    def render(self, props: Props) -> SizedString:
        return len(self.text), self.text


class Space(Text):
    def __init__(self) -> None:
        super().__init__(" ")


class Dash(Text):
    def __init__(self) -> None:
        super().__init__(" - ")


class Pipe(Text):
    def __init__(self) -> None:
        super().__init__(" | ")


class DynamicText(Component, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_text(self, props: Props) -> str:
        pass

    def render(self, props: Props) -> SizedString:
        text = self.get_text(props)
        return len(text), text


# TODO: fix name
class FixedWidthComponent(Component, metaclass=abc.ABCMeta):
    def render(self, props: Props) -> SizedString:
        width = props["width"]
        text = self.render_props_for_width(props, width)
        return len(text), text

    @abc.abstractmethod
    def render_props_for_width(self, props: Props, width: int) -> str:
        pass


class TransferText(FixedWidthComponent):
    def render_props_for_width(self, props: Props, width: int) -> str:
        src = props["src"]
        dest = props["dest"]
        pfx, src_mid, dest_mid, sfx = describe_transfer(src, dest)
        if not pfx and not sfx:
            components = [
                Bold(),
                Text(src),
                Reset(),
                Blue(),
                Text(" => "),
                Reset(),
                Bold(),
                Text(dest),
            ]
        else:
            components = [
                Bold(),
                Text(pfx),
                Reset(),
                LightGray(),
                Text("{%s => %s}" % (src_mid, dest_mid)),
                Reset(),
                Bold(),
                Text(sfx),
            ]
        return "".join(x.render({})[1] for x in components)


class Counter(DynamicText):
    def get_text(self, props: Props) -> str:
        index = props["index"]
        count = props["count"]
        num_digits = len(str(count))
        counter_format = "[%{}d/%d]".format(num_digits)
        return counter_format % (index, count)


class Percent(DynamicText):
    def get_text(self, props: Props) -> str:
        current_value = props["current_value"]
        max_value = props["max_value"]
        fraction = get_fraction(current_value, max_value)
        return "%3d%%" % int(fraction * 100)


class Bar(FixedWidthComponent):
    def render_props_for_width(self, props: Props, width: int) -> str:
        current_value = props["current_value"]
        max_value = props["max_value"]

        marker = "#"
        fraction = get_fraction(current_value, max_value)
        cwidth = width - 2
        marked_width = int(fraction * cwidth)
        res = (marker * marked_width).ljust(cwidth)
        return "[%s]" % res


class Speed(DynamicText):
    def get_text(self, props: Props) -> str:
        elapsed = props["elapsed"]
        current_value = props["current_value"]
        if elapsed < 2e-6:
            bits_per_second = 0.0
        else:
            bits_per_second = float(current_value) / elapsed
        speed = bits_per_second

        units = ["B", "K", "M", "G", "T", "P"]
        unit = None
        for unit in units:
            if speed < 1000:
                break
            speed /= 1000
        speed_format = "%.2f %s"
        return speed_format % (speed, unit + "/s")


class ETA(DynamicText):
    @classmethod
    def get_eta(cls, fraction: float, elapsed: int) -> str:
        if fraction == 0:
            return "ETA  : --:--:--"
        if fraction == 1:
            return "Time : " + cls.format_time(elapsed)
        eta = elapsed / fraction - elapsed
        return cls.format_time(eta)

    @staticmethod
    def format_time(seconds: float) -> str:
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    def get_text(self, props: Props) -> str:
        elapsed = props["elapsed"]
        current_value = props["current_value"]
        max_value = props["max_value"]
        fraction = get_fraction(current_value, max_value)
        eta = self.get_eta(fraction, elapsed)
        return eta


class Filename(DynamicText):
    def get_text(self, props: Props) -> str:
        filename = props["filename"]
        return shorten_path(filename, 40)


@dataclass
class FixedTuple:
    index: int
    component: Component


class Line:
    def __init__(self, components: typing.List[Component]) -> None:
        self.components = components
        fixed = list()
        for i, component in enumerate(components):
            if isinstance(component, FixedWidthComponent):
                fixed.append(FixedTuple(i, component))
        assert len(fixed) == 1, "Expecting exactly one fixed width component"
        self.fixed = fixed[0]

    def render(self, **kwargs: typing.Any) -> str:
        accumulator = [""] * len(self.components)
        term_width = shutil.get_terminal_size().columns
        current_width = 0
        for i, component in enumerate(self.components):
            if i == self.fixed.index:
                continue
            length, string = component.render(kwargs)
            accumulator[i] = string
            current_width += length

        fixed_width = term_width - current_width
        kwargs["width"] = fixed_width
        accumulator[self.fixed.index] = self.fixed.component.render(kwargs)[1]

        return "".join(accumulator)


class ProgressIndicator:
    def __init__(self) -> None:
        pass

    def on_new_file(self, progress: Progress) -> None:
        pass

    def on_file_done(self) -> None:
        pass

    def on_progress(self, progress: Progress) -> None:
        pass

    def on_start(self) -> None:
        pass

    def on_finish(self) -> None:
        pass


class OneFileIndicator(ProgressIndicator):
    def __init__(self) -> None:
        super().__init__()
        self.first_line = Line([Blue(), Counter(), TransferText(), Reset()])
        self.second_line = Line(
            [
                Blue(),
                Percent(),
                Reset(),
                Space(),
                LightGray(),
                Bar(),
                Reset(),
                Dash(),
                Standout(),
                Speed(),
                Reset(),
                Pipe(),
                Yellow(),
                ETA(),
                Reset(),
            ]
        )

    def on_new_file(self, progress: Progress) -> None:
        out1 = self.first_line.render(
            index=progress.index,
            count=progress.count,
            src=progress.src,
            dest=progress.dest,
        )
        print(out1)
        out2 = self.second_line.render(
            current_value=0, elapsed=0, max_value=progress.file_size
        )
        print(out2, end="\r")

    def on_progress(self, progress: Progress) -> None:
        out = self.second_line.render(
            index=progress.index,
            count=progress.count,
            current_value=progress.file_done,
            elapsed=progress.file_elapsed,
            max_value=progress.file_size,
        )
        print(out, end="\r")

    def on_file_done(self) -> None:
        print()


class GlobalIndicator(ProgressIndicator):
    def __init__(self) -> None:
        super().__init__()
        self.first_line = self.build_first_line()
        self.second_line = self.build_second_line()

    def on_start(self) -> None:
        print()

    @staticmethod
    def build_first_line() -> Line:
        return Line(
            [
                Green(),
                Counter(),
                Reset(),
                Space(),
                Blue(),
                Percent(),
                Reset(),
                Dash(),
                LightGray(),
                Bar(),
                Reset(),
                Dash(),
                Yellow(),
                ETA(),
                Reset(),
            ]
        )

    @staticmethod
    def build_second_line() -> Line:
        return Line(
            [
                Blue(),
                Percent(),
                Reset(),
                Space(),
                Bold(),
                Filename(),
                Reset(),
                Space(),
                LightGray(),
                Bar(),
                Reset(),
                Dash(),
                Standout(),
                Speed(),
                Reset(),
                Pipe(),
                Yellow(),
                ETA(),
                Reset(),
            ]
        )

    def _render_first_line(self, progress: Progress) -> None:
        out = self.first_line.render(
            index=progress.index,
            count=progress.count,
            current_value=progress.total_done,
            elapsed=progress.total_elapsed,
            max_value=progress.total_size,
        )
        cursor_up(2)
        print("\r", out, sep="")

    def _render_second_line(self, progress: Progress) -> None:
        out = self.second_line.render(
            current_value=progress.file_done,
            max_value=progress.file_size,
            elapsed=progress.file_elapsed,
            filename=progress.src,
        )
        print("\r", out, sep="")

    def on_progress(self, progress: Progress) -> None:
        self._render_first_line(progress)
        self._render_second_line(progress)
