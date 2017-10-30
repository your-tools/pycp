import ui

from conftest import mock_term_size
import pycp.progress


def test_can_build_lines_out_of_widgets(mocker):
    expected_width = 90
    mock_term_size(mocker, expected_width)
    line = pycp.progress.Line()
    counter = pycp.progress.Counter()
    percent = pycp.progress.Percent()
    bar = pycp.progress.Bar()
    speed = pycp.progress.Speed()
    eta = pycp.progress.ETA()
    line.set_components([
        ui.blue, counter, ui.reset, " ",
        ui.bold, percent, ui.reset, " ",
        ui.lightgray, bar, ui.reset, " - ",
        ui.standout, speed, ui.reset, " | ",
        ui.brown, eta, ui.reset
    ])
    tokens = line.render(
        index=1,
        count=3,
        current_value=20,
        max_value=100,
        elapsed=10,
    )
    _, no_color = ui.process_tokens(tokens, sep="", end="")
    assert len(no_color) == expected_width


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
