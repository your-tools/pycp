"""This module contains the main() function,
to parse command line

"""

import argparse
import os
import sys

from pycp.transfer import TransferManager, TransferError, TransferOptions


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

    parser.add_argument("-v", "--version", action="version", version="8.0.5")
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


def main():
    args = parse_commandline()
    args.move = is_pymv()

    files = args.files
    sources, destination = parse_filelist(files)

    transfer_options = TransferOptions()
    transfer_options.update(args)

    transfer_manager = TransferManager(sources, destination, transfer_options)
    try:
        errors = transfer_manager.do_transfer()
    except TransferError as err:
        sys.exit(err)
    except KeyboardInterrupt as err:
        sys.exit("Interrputed by user")

    if errors:
        print("Error occurred when transferring the following files:")
        for (file_name, error) in errors.items():
            print(file_name, error)


if __name__ == "__main__":
    main()
