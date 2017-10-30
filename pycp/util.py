"""Various useful functions"""

import os

import ui


def debug(message):
    """Print debug mesages when env. var PYCP_DEBUG is set."""
    if os.environ.get("PYCP_DEBUG"):
        print(message)


def human_readable(size):
    """Build a nice human readable string from a size given in
    bytes

    """
    if size < 1024**2:
        hreadable = float(size)/1024.0
        return "%.0fK" % hreadable
    elif size < (1024**3):
        hreadable = float(size)/(1024**2)
        return "%.1fM" % round(hreadable, 1)
    else:
        hreadable = float(size)/(1024.0**3)
        return "%.2fG" % round(hreadable, 2)


def pprint_transfer(src, dest):
    """
    Directly borrowed from git's diff.c file.

    >>> pprint_transfer("/path/to/foo", "/path/to/bar")
    '/path/to/{foo => bar}'
    """
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
    sfx = dest[len_dest - sfx_length:]
    src_mid = src[pfx_length:pfx_length + src_midlen]
    dest_mid = dest[pfx_length:pfx_length + dest_midlen]

    if pfx == os.path.sep:
        # The common prefix is / ,
        # avoid print /{etc => tmp}/foo, and
        # print {/etc => /tmp}/foo
        pfx = ""
        src_mid = os.path.sep + src_mid
        dest_mid = os.path.sep + dest_mid

    if not pfx and not sfx:
        return [
            ui.bold, src, ui.reset,
            ui.blue, " => ", ui.reset,
            ui.bold, dest
        ]

    return [
        ui.bold, pfx, ui.reset,
        ui.lightgray, "{", src_mid, " => ", dest_mid, "}", ui.reset,
        ui.bold, sfx
    ]


def shorten_path(path, length):
    """Shorten a path so that it is never longer
    that the given length

    >>> shorten_path("bazinga", 6)
    'baz...'
    >>> shorten_path("foo/bar/baz", 12)
    'foo/bar/baz'
    >>> shorten_path("foo/bar/baz", 10)
    'f/b/baz'
    >>> shorten_path("/foo/bar/baz", 11)
    '/f/b/baz'
    >>> shorten_path("foo/bar/bazinga", 10)
    'f/b/baz...'
    >>> shorten_path("foo/bar/baz/spam/eggs", 6)
    'eggs'
    >>> shorten_path("foo/bar/baz/spam/elephant", 4)
    'e...'
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


def shorten_string(input_string, length):
    """Shorten a string in a nice way:

    >>> shorten_string("foobar", 5)
    'fo...'
    >>> shorten_string("foobar", 3)
    'f..'
    >>> shorten_string("foobar", 2)
    'f.'
    >>> shorten_string("foobar", 1)
    'f'
    """
    if len(input_string) < length:
        return input_string
    if length > 3:
        return input_string[:length-3] + "..."
    if length == 3:
        return input_string[0] + ".."
    if length == 2:
        return input_string[0] + "."
    if length == 1:
        return input_string[0]
    return ""


if __name__ == "__main__":
    import doctest
    doctest.testmod()
