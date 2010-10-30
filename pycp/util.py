"""Various useful functions"""

import os

def debug(message):
    """Print debug mesages when env. var PYCP_DEBUG is set."""
    if os.environ.get("PYCP_DEBUG"):
        print message

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

    pprint_transfer("/path/to/foo", "/path/to/bar")
    >>> /path/to/{foo => bar}
    """
    len_src = len(src)
    len_dest = len(dest)

    # Find common prefix
    pfx_length = 0
    i = 0
    j = 0
    while (i < len_src and j < len_dest and src[i] == dest[j]):
        if src[i] == os.path.sep:
            pfx_length = i + 1
        i += 1
        j += 1

    # Find common suffix
    sfx_length = 0
    i  = len_src - 1
    j = len_dest - 1
    while (i > 0 and j > 0 and src[i] == dest[j]):
        if src[i] == os.path.sep:
            sfx_length = len_src - i
        i -= 1
        j -= 1

    src_midlen  = len_src  - pfx_length - sfx_length
    dest_midlen = len_dest - pfx_length - sfx_length

    pfx   = src[:pfx_length]
    sfx   = dest[len_dest - sfx_length:]
    src_mid  = src [pfx_length:pfx_length + src_midlen ]
    dest_mid = dest[pfx_length:pfx_length + dest_midlen]

    if pfx == os.path.sep:
        # The common prefix is / ,
        # avoid print /{etc => tmp}/foo, and
        # print {/etc => /tmp}/foo
        pfx = ""
        src_mid  = os.path.sep + src_mid
        dest_mid = os.path.sep + dest_mid

    if not pfx and not sfx:
        return "%s => %s" % (src, dest)

    res = "%s{%s => %s}%s" % (pfx, src_mid, dest_mid, sfx)
    return res
