"""This module contains the main() function,
to parse command line

"""

import argparse
import multiprocessing
import os
import sys
import time

from pycp.transfer import TransferProcess, TransferError, TransferOptions
from pycp.progress import GlobalIndicator, OneFileIndicator


def is_pymv():
    return sys.argv[0].endswith("pymv")


def parse_commandline():
    """Parses command line arguments"""
    if is_pymv():
        prog_name = "pymv"
        action = "move"
    else:
        prog_name = "pycp"
        action = "copy"

    usage = """
    %s [options] SOURCE DESTINATION
    %s [options] SOURCE... DIRECTORY

    %s SOURCE to DESTINATION or mutliple SOURCE(s) to DIRECTORY
    """ % (prog_name, prog_name, action)

    parser = argparse.ArgumentParser(usage=usage, prog=prog_name)

    parser.add_argument("-v", "--version", action="version", version="8.0.1")
    parser.add_argument("-i", "--interactive",
                        action="store_true",
                        dest="interactive",
                        help="ask before overwriting existing files")

    parser.add_argument("-s", "--safe",
                        action="store_true",
                        dest="safe",
                        help="never overwrite existing files")

    parser.add_argument("-f", "--force",
                        action="store_false",
                        dest="safe",
                        help="silently overwrite existing files "
                             "(this is the default)")

    parser.add_argument("-p", "--preserve",
                        action="store_true",
                        dest="preserve",
                        help="preserve time stamps and ownership")

    parser.add_argument("--ignore-errors",
                        action="store_true",
                        dest="ignore_errors",
                        help="ignore errors, remove destination if cp\n"
                             "Print problematic files at the end")

    parser.add_argument("-g", "--global-pbar",
                        action="store_true",
                        dest="global_progress",
                        help="display only one progress bar during transfer")

    parser.add_argument("--i-love-candy",
                        action="store_true",
                        dest="pacman",
                        help=argparse.SUPPRESS)

    parser.set_defaults(
        safe=False,
        interactive=False,
        ignore_errors=False,
        preserve=False,
        global_progress=False)
    parser.add_argument("files", nargs="+")

    return parser.parse_args()


def parse_filelist(filelist):
    if len(filelist) < 2:
        sys.exit("Incorrect number of arguments")

    sources = filelist[:-1]
    destination = filelist[-1]

    if len(sources) > 1:
        if not os.path.isdir(destination):
            sys.exit("%s is not an existing directory" % destination)

    for source in sources:
        if not os.path.exists(source):
            sys.exit("%s does not exist" % source)

    return sources, destination


# pylint: disable=too-many-instance-attributes
class Application():
    def __init__(self, sources, destination, options):
        self.sources = sources
        self.destination = destination
        self.options = options
        if options.global_progress:
            self.progress_indicator = GlobalIndicator()
        else:
            self.progress_indicator = OneFileIndicator()
        self.parent_pipe = None
        self.transfer_process = None
        self.done = False
        self.last_progress = None
        self.last_progress_update = 0

    def run(self):
        self.parent_pipe, child_pipe = multiprocessing.Pipe()
        self.transfer_process = TransferProcess(child_pipe, self.sources, self.destination,
                                                self.options)
        self.transfer_process.start()
        while not self.done:
            data = self.parent_pipe.recv()
            self.handle_pipe_data(data)
        errors = self.transfer_process.errors
        if errors:
            print("Error occurred when transferring the following files:")
            for (file_name, error) in errors.items():
                print(file_name, error)
            sys.exit(1)

    def handle_pipe_data(self, data):
        key = data[0]
        if len(data) == 2:
            value = data[1]
        else:
            value = ()
        if key == "error":
            sys.exit(value)
        elif key == "on_progress":
            # Throttle calls to progress_indicator.on_progress,
            # but still save the value so we can dispaly it right before on_finish()
            self.last_progress = value
            now = time.time()
            if now - self.last_progress_update > 0.1:
                self.progress_indicator.on_progress(self.last_progress)
                self.last_progress_update = now
        elif key == 'on_new_file':
            self.progress_indicator.on_new_file(value)
        elif key == 'on_file_done':
            if self.last_progress:
                self.progress_indicator.on_progress(self.last_progress)
            self.progress_indicator.on_file_done()
        elif key == 'on_finish':
            self.progress_indicator.on_finish()
            self.transfer_process.join()
            self.done = True


def _main():
    args = parse_commandline()
    args.move = is_pymv()

    files = args.files
    sources, destination = parse_filelist(files)

    options = TransferOptions()
    options.update(args)

    app = Application(sources, destination, options)
    app.run()


def main():
    try:
        _main()
    except TransferError as err:
        sys.exit(err)
    except KeyboardInterrupt as err:
        sys.exit("Interrputed by user")


if __name__ == "__main__":
    main()
