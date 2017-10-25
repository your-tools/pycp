import re
import textwrap

import pycp
from pycp.progress import FilePbar


def test_file_pbar():
    pycp.options.chomp = False

    file_pbar = FilePbar("src/foo", "dest/foo", 42, 1, 3)
    file_pbar.update(20)
