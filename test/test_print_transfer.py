from pycp.util import pprint_transfer


def test_01():
    src = "/path/to/foo"
    dest = "/path/to/bar"
    res = pprint_transfer(src, dest)
    assert res == "/path/to/{foo => bar}"


def test_02():
    src = "/path/to/foo/a/b"
    dest = "/path/to/spam/a/b"
    res = pprint_transfer(src, dest)
    assert res == "/path/to/{foo => spam}/a/b"


def test_03():
    src = "/path/to/foo/a/b"
    dest = "/path/to/foo/bar/a/b"
    res = pprint_transfer(src, dest)
    assert res == "/path/to/foo/{ => bar}/a/b"


def test_no_pfx():
    src = "/path/to/foo/a/b"
    dest = "/other/a/b"
    res = pprint_transfer(src, dest)
    assert res == "{/path/to/foo => /other}/a/b"


def test_no_sfx():
    src = "/path/to/foo/a"
    dest = "/path/to/foo/b"
    res = pprint_transfer(src, dest)
    assert res == "/path/to/foo/{a => b}"


def test_no_dir():
    src = "a"
    dest = "b"
    res = pprint_transfer(src, dest)
    assert res == "a => b"
