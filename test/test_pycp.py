import os
import re
import shutil
import stat
import sys
import tempfile
import time
import typing

import pytest
from conftest import mock_term_size, strip_ansi_colors

from pycp.main import main as pycp_main


def test_zero() -> None:
    sys.argv = ["pycp"]
    with pytest.raises(SystemExit):
        pycp_main()


def test_cp_self_1(test_dir: str) -> None:
    """cp a_file -> a_file should fail (same file)"""
    a_file = os.path.join(test_dir, "a_file")
    sys.argv = ["pycp", a_file, a_file]
    with pytest.raises(SystemExit):
        pycp_main()


def test_cp_self_2(test_dir: str) -> None:
    """cp a_file -> . should fail (same file)"""
    a_file = os.path.join(test_dir, "a_file")
    sys.argv = ["pycp", a_file, test_dir]
    with pytest.raises(SystemExit):
        pycp_main()


def test_cp_file_file(test_dir: str) -> None:
    """cp a_file -> a_file.back should work"""
    # cp a_file a_file.back
    a_file = os.path.join(test_dir, "a_file")
    a_file_back = os.path.join(test_dir, "a_file.back")

    sys.argv = ["pycp", a_file, a_file_back]
    pycp_main()
    assert os.path.exists(a_file_back)


def test_cp_asbsolute_symlink(test_dir: str) -> None:
    """
    Scenario:
    * a_link is a link to /path/to/abs/target
    * we run `pycp a_link b_link`
    * b_link should point to /path/to/abs/target
    """
    # note: since shutil.copytree does not handle
    # symlinks the way we would like to, create
    # link now
    a_link = os.path.join(test_dir, "a_link")
    a_target = os.path.join(test_dir, "a_target")
    with open(a_target, "w") as fp:
        fp.write("a_target\n")
    os.symlink(a_target, a_link)
    b_link = os.path.join(test_dir, "b_link")
    sys.argv = ["pycp", a_link, b_link]
    pycp_main()
    assert os.path.islink(b_link)
    b_target = os.readlink(b_link)
    assert b_target == a_target


def test_cp_relative_symlink(test_dir: str) -> None:
    """
    Scenario:
    * a_link is a link to a_target
    * we run `pycp a_link b_link`
    * b_link should point to a_target
    """
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


def test_cp_exe_file(test_dir: str) -> None:
    """Copied exe file should still be executable"""
    exe_file = os.path.join(test_dir, "file.exe")
    exe_file_2 = os.path.join(test_dir, "file2.exe")
    sys.argv = ["pycp", exe_file, exe_file_2]
    pycp_main()
    assert os.access(exe_file_2, os.X_OK)


def test_cp_file_dir(test_dir: str) -> None:
    """cp a_file -> b_dir should work"""
    a_file = os.path.join(test_dir, "a_file")
    b_dir = os.path.join(test_dir, "b_dir")
    os.mkdir(b_dir)
    sys.argv = ["pycp", a_file, b_dir]
    pycp_main()
    dest = os.path.join(b_dir, "a_file")
    assert os.path.exists(dest)


def test_cp_dir_dir_1(test_dir: str) -> None:
    """cp a_dir -> b_dir should work when b_dir does not exist"""
    a_dir = os.path.join(test_dir, "a_dir")
    b_dir = os.path.join(test_dir, "b_dir")
    sys.argv = ["pycp", a_dir, b_dir]
    pycp_main()
    c_file = os.path.join(b_dir, "c_file")
    d_file = os.path.join(b_dir, "c_file")
    assert os.path.exists(c_file)
    assert os.path.exists(d_file)


def test_cp_dir_dir_2(test_dir: str) -> None:
    """cp a_dir -> b_dir should work when b_dir exists"""
    a_dir = os.path.join(test_dir, "a_dir")
    b_dir = os.path.join(test_dir, "b_dir")
    os.mkdir(b_dir)
    sys.argv = ["pycp", a_dir, b_dir]
    pycp_main()
    c_file = os.path.join(b_dir, "a_dir", "c_file")
    d_file = os.path.join(b_dir, "a_dir", "c_file")
    assert os.path.exists(c_file)
    assert os.path.exists(d_file)


def test_cp_dir_dir2_global(test_dir: str) -> None:
    """cp a_dir -> b_dir should work when using `--global"""
    a_dir = os.path.join(test_dir, "a_dir")
    b_dir = os.path.join(test_dir, "b_dir")
    os.mkdir(b_dir)
    sys.argv = ["pycp", "-g", a_dir, b_dir]
    pycp_main()
    c_file = os.path.join(b_dir, "a_dir", "c_file")
    d_file = os.path.join(b_dir, "a_dir", "c_file")
    assert os.path.exists(c_file)
    assert os.path.exists(d_file)


def test_no_source(test_dir: str) -> None:
    """cp d_file -> d_file.back should fail if d_file does not exist"""
    d_file = os.path.join(test_dir, "d_file")
    sys.argv = ["pycp", d_file, "d_file.back"]
    with pytest.raises(SystemExit):
        pycp_main()


def test_no_dest(test_dir: str) -> None:
    """cp a_file -> d_dir should fail if d_dir does not exist"""
    a_file = os.path.join(test_dir, "a_file")
    d_dir = os.path.join(test_dir, "d_dir" + os.path.sep)
    sys.argv = ["pycp", a_file, d_dir]
    with pytest.raises(SystemExit):
        pycp_main()


def test_several_sources_1(test_dir: str) -> None:
    """cp a_file b_file -> c_dir should work"""
    a_file = os.path.join(test_dir, "a_file")
    b_file = os.path.join(test_dir, "b_file")
    c_dir = os.path.join(test_dir, "c_dir")
    os.mkdir(c_dir)
    sys.argv = ["pycp", a_file, b_file, c_dir]
    pycp_main()


def test_several_sources_2(test_dir: str) -> None:
    """cp a_file b_file -> c_file should fail"""
    a_file = os.path.join(test_dir, "a_file")
    b_file = os.path.join(test_dir, "b_file")
    c_file = os.path.join(test_dir, "c_file")
    sys.argv = ["pycp", a_file, b_file, c_file]
    with pytest.raises(SystemExit):
        pycp_main()


def test_several_sources_3(test_dir: str) -> None:
    """cp a_file b_file -> c_dir should fail if c_dir does not exist"""
    a_file = os.path.join(test_dir, "a_file")
    b_file = os.path.join(test_dir, "b_file")
    c_dir = os.path.join(test_dir, "c_dir")
    sys.argv = ["pycp", a_file, b_file, c_dir]
    with pytest.raises(SystemExit):
        pycp_main()


def test_overwrite_1(test_dir: str) -> None:
    """cp a_file -> b_file should overwrite b_file when not using --safe"""
    a_file = os.path.join(test_dir, "a_file")
    b_file = os.path.join(test_dir, "b_file")
    sys.argv = ["pycp", a_file, b_file]
    pycp_main()
    b_file_desc = open(b_file, "r")
    b_contents = b_file_desc.read()
    b_file_desc.close()
    assert b_contents == "a\n"


def test_overwrite_2(test_dir: str) -> None:
    """cp a_file -> b_file should not overwrite b_file when using --safe"""
    a_file = os.path.join(test_dir, "a_file")
    b_file = os.path.join(test_dir, "b_file")
    sys.argv = ["pycp", "--safe", a_file, b_file]
    pycp_main()
    b_file_desc = open(b_file, "r")
    b_contents = b_file_desc.read()
    b_file_desc.close()
    assert b_contents == "b\n"


def test_copy_readonly(test_dir: str) -> None:
    """cp a_file -> ro_dir should fail if ro_dir is read only"""
    a_file = os.path.join(test_dir, "a_file")
    ro_dir = tempfile.mkdtemp("pycp-test-ro")
    os.chmod(ro_dir, stat.S_IRUSR | stat.S_IXUSR)
    sys.argv = ["pycp", a_file, ro_dir]
    with pytest.raises(SystemExit):
        pycp_main()
    shutil.rmtree(ro_dir)


def test_preserve(test_dir: str) -> None:
    """Check that mtimes are preserved"""
    a_file = os.path.join(test_dir, "a_file")
    long_ago = time.time() - 10000
    os.utime(a_file, (long_ago, long_ago))
    a_copy = os.path.join(test_dir, "a_copy")
    sys.argv = ["pycp", "--preserve", a_file, a_copy]
    pycp_main()
    copy_stat = os.stat(a_copy)
    assert copy_stat.st_mtime == pytest.approx(long_ago, abs=1)


@pytest.mark.xfail()
def test_output_does_not_wrap_1(
    test_dir: str, capsys: typing.Any, mocker: typing.Any
) -> None:
    """
    When not using --global, each printed line length
    should be less that the terminal size
    """
    # and we'll trigger this bug:
    # https://github.com/dmerejkowsky/pycp/issues/29
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


def test_output_does_not_wrap_2(
    test_dir: str, capsys: typing.Any, mocker: typing.Any
) -> None:
    """
    When using --global, each printed line length
    should be less that the terminal size
    """
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
