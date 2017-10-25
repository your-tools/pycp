"""This module contains the main() function,
to parse command line

"""

import argparse
import os
import sys

import pkg_resources

from pycp.transfer import TransferManager, TransferError


# pylint: disable=too-many-locals,too-many-statements
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

    pycp_distribution = pkg_resources.get_distribution("pycp")
    version = pycp_distribution.version
    version = "%s version %s" % (prog_name, version)

    parser = argparse.ArgumentParser(usage=usage, prog=prog_name)

    parser.add_argument("-v", "--version", action="version",
                        version=version)
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

    parser.add_argument("-a", "--all",
                        action="store_true",
                        dest="all",
                        help="transfer all files (including hidden files)")

    parser.add_argument("-p", "--preserve",
                        action="store_true",
                        dest="preserve",
                        help="preserve time stamps while copying")

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
        all=False,
        ignore_errors=False,
        preserve=False,
        global_progress=False)
    parser.add_argument("files", nargs="+")

    args = parser.parse_args()
    files = args.files
    ignore_errors = args.ignore_errors
    all_files = args.all
    global_progress = args.global_progress
    safe = args.safe
    interactive = args.interactive

    if len(files) < 2:
        parser.error("Incorrect number of arguments")

    sources = files[:-1]
    destination = files[-1]

    if len(sources) > 1:
        if not os.path.isdir(destination):
            sys.exit("%s is not an existing directory" % destination)

    for source in sources:
        if not os.path.exists(source):
            sys.exit("%s does not exist" % source)

    # FIXME: this is a hack until we have proper 'style' support
    if args.pacman:
        os.environ["PYCP_PACMAN"] = True

    transfer_manager = TransferManager(sources, destination,
                                       move=move, ignore_errors=ignore_errors,
                                       all_files=all_files, global_progress=global_progress,
                                       safe=safe, interactive=interactive)
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
