import sys
import os


from pycp.main import main as pycp_main


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


def test_hidden(test_dir):
    a_dir = os.path.join(test_dir, "a_dir")
    dest = os.path.join(test_dir, "dest")
    os.mkdir(dest)
    sys.argv = ["pymv", a_dir, dest]
    pycp_main()
    hidden_copy = os.path.join(dest, "a_dir", ".hidden")
    assert os.path.exists(hidden_copy)
