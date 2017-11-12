
from conftest import mock_term_size
import pycp.progress
from pycp.progress import Text, Blue, Bold, Reset, LightGray,  Standout, Brown
from pycp.progress import shorten_path, shorten_string


def test_can_build_lines_out_of_widgets(mocker):
    expected_width = 90
    mock_term_size(mocker, expected_width)
    line = pycp.progress.Line()
    counter = pycp.progress.Counter()
    percent = pycp.progress.Percent()
    bar = pycp.progress.Bar()
    speed = pycp.progress.Speed()
    bold = Bold()
    eta = pycp.progress.ETA()
    blue = Blue()
    brown = Brown()
    lightgray = LightGray()
    reset = Reset()
    standout = Standout()
    space = Text(" ")
    dash = Text(" - ")
    pipe = Text(" | ")
    line.set_components([
        blue, counter, reset, space,
        bold, percent, reset, space,
        lightgray, bar, reset, dash,
        standout, speed, reset, pipe,
        brown, eta, reset,
    ])
    out = line.render(
        index=1,
        count=3,
        current_value=20,
        max_value=100,
        elapsed=10,
    )
    print(out)


# Note: there are no 'assert' here, so this test checks nothing :P
# I keep it because:
#  * It serves as "executable documentation"  for the pycp.progress module
#  * I might need it for a refactoring later
def test_indicates_progress_file_by_file():
    one_file_indicator = pycp.progress.OneFileIndicator()
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


def test_shorten_path():
    assert shorten_path("bazinga", 6) == 'baz...'
    assert shorten_path("foo/bar/baz", 12) == 'foo/bar/baz'
    assert shorten_path("foo/bar/baz", 10) == 'f/b/baz'
    assert shorten_path("/foo/bar/baz", 11) == '/f/b/baz'
    assert shorten_path("foo/bar/bazinga", 10) == 'f/b/baz...'
    assert shorten_path("foo/bar/baz/spam/eggs", 6) == 'eggs'
    assert shorten_path("foo/bar/baz/spam/elephant", 4) == 'e...'
    assert shorten_path(
        "Songs/17 Hippies/Sirba/02 Mad Bad Cat.mp3", 40) == 'S/1/S/02 Mad Bad Cat.mp3'


def test_shorten_string():
    assert shorten_string("foobar", 5) == 'fo...'
    assert shorten_string("foobar", 3) == 'f..'
    assert shorten_string("foobar", 2) == 'f.'
    assert shorten_string("foobar", 1) == 'f'
