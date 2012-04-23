"""This module contains the main() function,
to parse command line

"""


import os
import sys

from optparse import OptionParser, SUPPRESS_HELP

import pycp
from pycp.transfer import TransferManager, TransferError


def die(message):
    """An error occured.
    Write it to stderr and exit with error code 1

    """
    sys.stderr.write(str(message) + "\n")
    sys.exit(1)


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

    parser = OptionParser(usage, version=version, prog=prog_name)

    parser.add_option("-i", "--interactive",
            action  = "store_true",
            dest    = "interactive",
            help    = "ask before overwriting existing files")

    parser.add_option("-s", "--safe",
            action  = "store_true",
            dest    = "safe",
            help    = "never overwirte existing files")

    parser.add_option("-f", "--force",
            action  = "store_false",
            dest    = "safe",
            help    = "silently overwirte existing files " + \
                "(this is the default)")

    parser.add_option("-a", "--all",
            action = "store_true",
            dest   = "all",
            help  = "transfer all files (including hidden files")

    parser.add_option("-p", "--preserve",
            action = "store_true",
            dest   = "preserve",
            help   = "preserve time stamps while copying")

    parser.add_option("--ignore-errors",
            action = "store_true",
            dest   = "ignore_errors",
            help   = "ignore errors, remove destination if cp\n" +
                     "Print problematic files at the end")

    parser.add_option("-g", "--global-pbar",
        action = "store_true",
        dest   = "global_pbar",
        help   = "display only one progress bar during transfer")

    parser.add_option("--i-love-candy",
        action = "store_true",
        dest   = "chomp",
        help   = SUPPRESS_HELP)

    parser.set_defaults(
        safe=False,
        interactive=False,
        all=False,
        ignore_errors=False,
        preserve=False)

    (options, args) = parser.parse_args()
    options.move = move # This "option" is set by sys.argv[0]

    pycp.options = options

    if len(args) < 2:
        parser.error("Incorrect number of arguments")

    sources = args[:-1]
    destination = args[-1]

    if len(sources) > 1:
        if not os.path.isdir(destination):
            die("%s is not an existing directory" % destination)

    for source in sources:
        if not os.path.exists(source):
            die("%s does not exist" % source)

    transfer_manager = TransferManager(sources, destination)
    try:
        errors = transfer_manager.do_transfer()
    except TransferError, err:
        die(err)
    except KeyboardInterrupt, err:
        die("Interrputed by user")

    if errors:
        print "Error occurred when transferring the following files:"
        for (file_name, error) in errors.iteritems():
            print file_name, error

if __name__ == "__main__":
    main()
