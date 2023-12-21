""" Tests for the TransferText component, used to print each file transfer
one by one.
Like:

```
pycp /path/to/foo /path/to/bar
/path/to/{foo => bar}
```
"""

from conftest import strip_ansi_colors

from pycp.progress import TransferText


def assert_pprint(src: str, dest: str, actual: str) -> None:
    transfer_text = TransferText()
    _, out = transfer_text.render({"src": src, "dest": dest, "width": 40})
    assert strip_ansi_colors(out) == actual


def test_01() -> None:
    src = "/path/to/foo"
    dest = "/path/to/bar"
    assert_pprint(src, dest, "/path/to/{foo => bar}")


def test_02() -> None:
    src = "/path/to/foo/a/b"
    dest = "/path/to/spam/a/b"
    assert_pprint(src, dest, "/path/to/{foo => spam}/a/b")


def test_03() -> None:
    src = "/path/to/foo/a/b"
    dest = "/path/to/foo/bar/a/b"
    assert_pprint(src, dest, "/path/to/foo/{ => bar}/a/b")


def test_no_pfx() -> None:
    src = "/path/to/foo/a/b"
    dest = "/other/a/b"
    assert_pprint(src, dest, "{/path/to/foo => /other}/a/b")


def test_no_sfx() -> None:
    src = "/path/to/foo/a"
    dest = "/path/to/foo/b"
    assert_pprint(src, dest, "/path/to/foo/{a => b}")


def test_no_dir() -> None:
    src = "a"
    dest = "b"
    assert_pprint(src, dest, "a => b")
