import tempfile  # for mkdtemp
import shutil
import sys
import os
import stat
import time


import pycp
from pycp.main import main as pycp_main
from pycp.util import pprint_transfer

import pytest


def test_mv_file_file(test_dir):
    "a_file -> a_file.back"
    a_file = os.path.join(test_dir, "a_file")
    a_file_back = os.path.join(test_dir, "a_file.back")

    sys.argv = ["pymv", a_file, a_file_back]
    pycp_main()
    assert os.path.exists(a_file_back)
    assert not os.path.exists(a_file)


def test_mv_dir_dir_1(test_dir):
    "a_dir -> b_dir (b_dir does not exist)"
    a_dir = os.path.join(test_dir, "a_dir")
    b_dir = os.path.join(test_dir, "b_dir")
    sys.argv = ["pymv", a_dir, b_dir]
    pycp_main()
    c_file = os.path.join(b_dir, "c_file")
    d_file = os.path.join(b_dir, "c_file")
    assert os.path.exists(c_file)
    assert os.path.exists(d_file)
    assert not os.path.exists(a_dir)


def test_mv_dir_dir_2(test_dir):
    "a_dir -> b_dir (b_dir exists)"
    a_dir = os.path.join(test_dir, "a_dir")
    b_dir = os.path.join(test_dir, "b_dir")
    os.mkdir(b_dir)
    sys.argv = ["pymv", a_dir, b_dir]
    pycp_main()
    c_file = os.path.join(b_dir, "a_dir", "c_file")
    d_file = os.path.join(b_dir, "a_dir", "c_file")
    assert os.path.exists(c_file)
    assert os.path.exists(d_file)
    assert not os.path.exists(a_dir)
