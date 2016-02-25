"""This module contains the main() function,
to parse command line

"""

from __future__ import print_function

import os
import sys

import argparse

import pycp
from pycp.transfer import TransferManager, TransferError

def main():
    """Parses command line arguments"""
    if sys.argv[0].endswith("pymv"):
        move = True
        prog_name = "pymv"
        action = "move"
    else:
        move = False
        prog_name = "pycp"
        action = "copy"

    usage = """
    %s [options] SOURCE DESTINATION
    %s [options] SOURCE... DIRECTORY

    %s SOURCE to DESTINATION or mutliple SOURCE(s) to DIRECTORY
    """ % (prog_name, prog_name, action)

    version = "%s version %s" % (prog_name, pycp.__version__)

    parser = argparse.ArgumentParser(usage=usage, prog=prog_name)

    parser.add_argument("-v", "--version", action="version",
            version=version)
    parser.add_argument("-i", "--interactive",
            action  = "store_true",
            dest    = "interactive",
            help    = "ask before overwriting existing files")

    parser.add_argument("-s", "--safe",
            action  = "store_true",
            dest    = "safe",
            help    = "never overwrite existing files")

    parser.add_argument("-f", "--force",
            action  = "store_false",
            dest    = "safe",
            help    = "silently overwrite existing files " + \
                "(this is the default)")

    parser.add_argument("-a", "--all",
            action = "store_true",
            dest   = "all",
            help  = "transfer all files (including hidden files)")

    parser.add_argument("-p", "--preserve",
            action = "store_true",
            dest   = "preserve",
            help   = "preserve time stamps while copying")

    parser.add_argument("--ignore-errors",
            action = "store_true",
            dest   = "ignore_errors",
            help   = "ignore errors, remove destination if cp\n" +
                     "Print problematic files at the end")

    parser.add_argument("-g", "--global-pbar",
        action = "store_true",
        dest   = "global_pbar",
        help   = "display only one progress bar during transfer")

    parser.add_argument("--i-love-candy",
        action = "store_true",
        dest   = "chomp",
        help   = argparse.SUPPRESS)

    parser.set_defaults(
        safe=False,
        interactive=False,
        all=False,
        ignore_errors=False,
        preserve=False)
    parser.add_argument("files", nargs="+")

    args = parser.parse_args()
    args.move = move # This "option" is set by sys.argv[0]

    pycp.options = args

    if len(args.files) < 2:
        parser.error("Incorrect number of arguments")

    sources = args.files[:-1]
    destination = args.files[-1]

    if len(sources) > 1:
        if not os.path.isdir(destination):
            sys.exit("%s is not an existing directory" % destination)

    for source in sources:
        if not os.path.exists(source):
            sys.exit("%s does not exist" % source)

    transfer_manager = TransferManager(sources, destination)
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
