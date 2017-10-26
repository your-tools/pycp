import shutil
import time

import attr
import ui

import pycp.progress


def test_can_build_lines_out_of_widgets():
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
    ui.info("\n", *tokens, sep="")


def test_indicates_progress_file_by_file():
    src = "src/foo"
    dest = "dest/foo"
    one_file_indicator = pycp.progress.OneFileIndicator(src=src, dest=dest,
                                                        index=1, count=3,
                                                        size=100)

    one_file_indicator.start()
    one_file_indicator.on_file_transfer(25)
    one_file_indicator.on_file_transfer(75)
    one_file_indicator.stop()
