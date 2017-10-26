import ui

from pycp.util import pprint_transfer


def assert_pprint(src, dest, actual):
    res = pprint_transfer(src, dest)
    _, without_color = ui.process_tokens(res, sep="", end="")
    assert without_color == actual


def test_01():
    src = "/path/to/foo"
    dest = "/path/to/bar"
    assert_pprint(src, dest, "/path/to/{foo => bar}")


def test_02():
    src = "/path/to/foo/a/b"
    dest = "/path/to/spam/a/b"
    assert_pprint(src, dest, "/path/to/{foo => spam}/a/b")


def test_03():
    src = "/path/to/foo/a/b"
    dest = "/path/to/foo/bar/a/b"
    assert_pprint(src, dest, "/path/to/foo/{ => bar}/a/b")


def test_no_pfx():
    src = "/path/to/foo/a/b"
    dest = "/other/a/b"
    assert_pprint(src, dest, "{/path/to/foo => /other}/a/b")


def test_no_sfx():
    src = "/path/to/foo/a"
    dest = "/path/to/foo/b"
    assert_pprint(src, dest, "/path/to/foo/{a => b}")


def test_no_dir():
    src = "a"
    dest = "b"
    assert_pprint(src, dest, "a => b")
