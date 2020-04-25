from conftest import mock_term_size
import pycp.progress
from pycp.progress import (
    shorten_path,
    shorten_string,
    OneFileIndicator,
    GlobalIndicator,
)


def test_shorten_path():
    assert shorten_path("bazinga", 6) == "baz..."
    assert shorten_path("foo/bar/baz", 12) == "foo/bar/baz"
    assert shorten_path("foo/bar/baz", 10) == "f/b/baz"
    assert shorten_path("/foo/bar/baz", 11) == "/f/b/baz"
    assert shorten_path("foo/bar/bazinga", 10) == "f/b/baz..."
    assert shorten_path("foo/bar/baz/spam/eggs", 6) == "eggs"
    assert shorten_path("foo/bar/baz/spam/elephant", 4) == "e..."
    assert (
        shorten_path("Songs/17 Hippies/Sirba/02 Mad Bad Cat.mp3", 40)
        == "S/1/S/02 Mad Bad Cat.mp3"
    )


def test_shorten_string():
    assert shorten_string("foobar", 5) == "fo..."
    assert shorten_string("foobar", 3) == "f.."
    assert shorten_string("foobar", 2) == "f."
    assert shorten_string("foobar", 1) == "f"


# Note: there are no 'assert' here, so these tests only check
# that rendering does not crash
# I keep them because it helps when tweaking pycp's output


def test_global_indicator(mocker):
    expected_width = 90
    mock_term_size(mocker, expected_width)
    global_indicator = GlobalIndicator()

    progress = pycp.progress.Progress()
    progress.index = 2
    progress.count = 3
    progress.src = "src/foo"
    progress.dest = "dest/foo"
    progress.file_size = 100

    global_indicator.on_new_file(progress)
    global_indicator.on_progress(progress)
    global_indicator.on_file_done()

    progress.src = "src/bar"
    progress.dest = "dest/bar"
    global_indicator.on_new_file(progress)
    global_indicator.on_progress(progress)
    global_indicator.on_file_done()

    global_indicator.on_finish()


def test_indicates_progress_file_by_file():
    one_file_indicator = OneFileIndicator()
    one_file_indicator.on_start()

    progress = pycp.progress.Progress()
    progress.index = 2
    progress.count = 3
    progress.src = "src/foo"
    progress.dest = "dest/foo"
    progress.file_size = 100

    one_file_indicator.on_new_file(progress)
    progress.file_done = 25
    one_file_indicator.on_progress(progress)
    progress.file_done = 75
    one_file_indicator.on_progress(progress)
    progress.on_file_done = 100
    one_file_indicator.on_progress(progress)
    one_file_indicator.on_file_done()

    one_file_indicator.on_finish()
