import os
import re
import shutil
import stat
import sys
import tempfile
import time


from pycp.main import main as pycp_main
from conftest import mock_term_size, strip_ansi_colors

import pytest


@pytest.fixture()
def test_dir():
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    cur_test = os.path.join(cur_dir, "test_dir")
    temp_dir = tempfile.mkdtemp("pycp-test")
    test_dir = os.path.join(temp_dir, "test_dir")
    shutil.copytree(cur_test, test_dir)
    yield test_dir
    if os.environ.get("DEBUG"):
        print("not removing", test_dir)
    else:
        shutil.rmtree(test_dir)


def test_zero():
    sys.argv = ["pycp"]
    with pytest.raises(SystemExit):
        pycp_main()


def test_cp_self_1(test_dir):
    "a_file -> a_file"
    a_file = os.path.join(test_dir, "a_file")
    sys.argv = ["pycp", a_file, a_file]
    with pytest.raises(SystemExit):
        pycp_main()


def test_cp_self_2(test_dir):
    "a_file -> ."
    a_file = os.path.join(test_dir, "a_file")
    sys.argv = ["pycp", a_file, test_dir]
    with pytest.raises(SystemExit):
        pycp_main()


def test_cp_file_file(test_dir):
    "a_file -> a_file.back"
    # cp a_file a_file.back
    a_file = os.path.join(test_dir, "a_file")
    a_file_back = os.path.join(test_dir, "a_file.back")

    sys.argv = ["pycp", a_file, a_file_back]
    pycp_main()
    assert os.path.exists(a_file_back)


def test_cp_symlink(test_dir):
    # note: since shutil.copytree does not handle
    # symlinks the way we would like to, create
    # link now
    a_link = os.path.join(test_dir, "a_link")
    a_target = os.path.join(test_dir, "a_target")
    with open(a_target, "w") as fp:
        fp.write("a_target\n")
    os.symlink("a_target", a_link)
    b_link = os.path.join(test_dir, "b_link")
    sys.argv = ["pycp", a_link, b_link]
    pycp_main()
    assert os.path.islink(b_link)
    b_target = os.readlink(b_link)
    assert b_target == "a_target"


def test_cp_keep_rel_symlink(test_dir):
    a_link = os.path.join(test_dir, "a_link")
    a_target = os.path.join(test_dir, "a_target")
    with open(a_target, "w") as fp:
        fp.write("a_target\n")
    os.symlink("a_target", a_link)
    b_dir = os.path.join(test_dir, "b_dir")
    os.mkdir(b_dir)
    b_link = os.path.join(b_dir, "b_link")
    sys.argv = ["pycp", a_link, b_link]
    pycp_main()
    assert os.path.islink(b_link)
    b_target = os.readlink(b_link)
    assert b_target == "a_target"


def test_cp_exe_file(test_dir):
    "copied file should still be executable"
    exe_file = os.path.join(test_dir, "file.exe")
    exe_file_2 = os.path.join(test_dir, "file2.exe")
    sys.argv = ["pycp", exe_file, exe_file_2]
    pycp_main()
    assert os.access(exe_file_2, os.X_OK)


def test_cp_file_dir(test_dir):
    "a_file -> b_dir"
    a_file = os.path.join(test_dir, "a_file")
    b_dir = os.path.join(test_dir, "b_dir")
    os.mkdir(b_dir)
    sys.argv = ["pycp", a_file, b_dir]
    pycp_main()
    dest = os.path.join(b_dir, "a_file")
    assert os.path.exists(dest)


def test_cp_dir_dir_1(test_dir):
    "a_dir -> b_dir (b_dir does not exist)"
    a_dir = os.path.join(test_dir, "a_dir")
    b_dir = os.path.join(test_dir, "b_dir")
    sys.argv = ["pycp", a_dir, b_dir]
    pycp_main()
    c_file = os.path.join(b_dir, "c_file")
    d_file = os.path.join(b_dir, "c_file")
    assert os.path.exists(c_file)
    assert os.path.exists(d_file)


def test_cp_dir_dir_2(test_dir):
    "a_dir -> b_dir (b_dir exists)"
    a_dir = os.path.join(test_dir, "a_dir")
    b_dir = os.path.join(test_dir, "b_dir")
    os.mkdir(b_dir)
    sys.argv = ["pycp", a_dir, b_dir]
    pycp_main()
    c_file = os.path.join(b_dir, "a_dir", "c_file")
    d_file = os.path.join(b_dir, "a_dir", "c_file")
    assert os.path.exists(c_file)
    assert os.path.exists(d_file)


def test_cp_dir_dir2_global(test_dir):
    a_dir = os.path.join(test_dir, "a_dir")
    b_dir = os.path.join(test_dir, "b_dir")
    os.mkdir(b_dir)
    sys.argv = ["pycp", "-g", a_dir, b_dir]
    pycp_main()
    c_file = os.path.join(b_dir, "a_dir", "c_file")
    d_file = os.path.join(b_dir, "a_dir", "c_file")
    assert os.path.exists(c_file)
    assert os.path.exists(d_file)


def test_no_source(test_dir):
    "d_file -> d_file.back but d_file does not exists"
    d_file = os.path.join(test_dir, "d_file")
    sys.argv = ["pycp", d_file, "d_file.back"]
    with pytest.raises(SystemExit):
        pycp_main()


def test_no_dest(test_dir):
    "a_file -> d_dir but d_dir does not exists"
    a_file = os.path.join(test_dir, "a_file")
    d_dir = os.path.join(test_dir, "d_dir" + os.path.sep)
    sys.argv = ["pycp", a_file, d_dir]
    with pytest.raises(SystemExit):
        pycp_main()


def test_several_sources_1(test_dir):
    "a_file b_file c_file"
    a_file = os.path.join(test_dir, "a_file")
    b_file = os.path.join(test_dir, "b_file")
    c_file = os.path.join(test_dir, "c_file")
    sys.argv = ["pycp", a_file, b_file, c_file]
    with pytest.raises(SystemExit):
        pycp_main()


def test_several_sources_2(test_dir):
    "a_file b_file c_dir but c_dir does not exists"
    a_file = os.path.join(test_dir, "a_file")
    b_file = os.path.join(test_dir, "b_file")
    c_dir = os.path.join(test_dir, "c_dir")
    sys.argv = ["pycp", a_file, b_file, c_dir]
    with pytest.raises(SystemExit):
        pycp_main()


def test_overwrite_1(test_dir):
    "a_file -> b_file and b_file already exists (unsafe)"
    a_file = os.path.join(test_dir, "a_file")
    b_file = os.path.join(test_dir, "b_file")
    sys.argv = ["pycp", a_file, b_file]
    pycp_main()
    b_file_desc = open(b_file, "r")
    b_contents = b_file_desc.read()
    b_file_desc.close()
    assert b_contents == "a\n"


def test_overwrite_2(test_dir):
    "a_file -> b_file and b_file already exists (safe)"
    a_file = os.path.join(test_dir, "a_file")
    b_file = os.path.join(test_dir, "b_file")
    sys.argv = ["pycp", "--safe",  a_file, b_file]
    pycp_main()
    b_file_desc = open(b_file, "r")
    b_contents = b_file_desc.read()
    b_file_desc.close()
    assert b_contents == "b\n"


def test_copy_readonly(test_dir):
    "a_file -> ro_dir but ro_dir is read only"
    a_file = os.path.join(test_dir, "a_file")
    ro_dir = tempfile.mkdtemp("pycp-test-ro")
    os.chmod(ro_dir, stat.S_IRUSR | stat.S_IXUSR)
    sys.argv = ["pycp", a_file, ro_dir]
    with pytest.raises(SystemExit):
        pycp_main()
    shutil.rmtree(ro_dir)


def test_preserve(test_dir):
    a_file = os.path.join(test_dir, "a_file")
    long_ago = time.time() - 10000
    os.utime(a_file, (long_ago, long_ago))
    a_copy = os.path.join(test_dir,  "a_copy")
    sys.argv = ["pycp", "--preserve", a_file, a_copy]
    pycp_main()
    copy_stat = os.stat(a_copy)
    assert copy_stat.st_mtime == long_ago


def test_output_does_not_wrap_1(test_dir, capsys, mocker):
    "Not using --global"
    a_file = os.path.join(test_dir, "a_file")
    a_file_back = os.path.join(test_dir, "a_file.back")

    expected_width = 90
    mock_term_size(mocker, expected_width)
    sys.argv = ["pycp", a_file, a_file_back]
    pycp_main()
    out, err = capsys.readouterr()
    lines = re.split(r"\r|\n", out)
    for line in lines:
        assert len(strip_ansi_colors(line)) <= expected_width


def test_output_does_not_wrap_2(test_dir, capsys, mocker):
    "Using --global"
    "a_dir -> b_dir (b_dir does not exist)"
    expected_width = 90
    mock_term_size(mocker, expected_width)
    a_dir = os.path.join(test_dir, "a_dir")
    b_dir = os.path.join(test_dir, "b_dir")

    sys.argv = ["pycp", "--global", a_dir, b_dir]
    pycp_main()

    out, err = capsys.readouterr()
    lines = re.split(r"\r|\n", out)
    for line in lines:
        assert len(strip_ansi_colors(line)) <= expected_width
