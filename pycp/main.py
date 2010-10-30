#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Copyright (c) 2010 Dimitri Merejkowsky                                       #
#                                                                              #
# Permission is hereby granted, free of charge, to any person obtaining a copy #
# of this software and associated documentation files (the "Software"), to deal#
# in the Software without restriction, including without limitation the rights #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell    #
# copies of the Software, and to permit persons to whom the Software is        #
# furnished to do so, subject to the following conditions:                     #
#                                                                              #
# The above copyright notice and this permission notice shall be included in   #
# all copies or substantial portions of the Software.                          #
#                                                                              #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR   #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,     #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE  #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER       #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,#
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN    #
# THE SOFTWARE.                                                                #
################################################################################

import os
import sys

from optparse import OptionParser

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
        for (file, error) in errors.iteritems():
            print file, error

if __name__ == "__main__":
    main()
