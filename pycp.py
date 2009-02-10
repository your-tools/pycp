#!/usr/bin/env python
# -*- coding: utf-8 -*-

##########
# PYCP
#########

##########################################################################
# Copyright 2009 Dimitri Merejkowsky                                     #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program.  If not, see <http://www.gnu.org/licenses/>. #
##########################################################################


"""
Trying to have a progress bar while copying stuff

Main idea : forking `cp` in background,
read size of source, and read size of
destination while copying.

WARNING: for the moment, can only copy one file at a time
"""

__author__ = "Yannick LM"
__author_email__  = "yannicklm1337 AT gmail DOT com"
__version__ = "1.2"

import subprocess
import sys
import os
import time
import getopt

try:
    import progressbar
except ImportError:
    print "Error: Unable to find progressbar module"
    exit(1)


class CopyManager:
    """
    Class that manages cp process
    """
    def __init__(self, source, destination):
        self.cp_process = None
        self.source = source
        self.destination = destination
        self.pbar = progressbar.ProgressBar()

    def copy(self):
        "Main method of CopyManager"
        self.cp_process = subprocess.Popen(["cp",
            self.source,
            self.destination],
            stdout=subprocess.PIPE)
        print self.source + " -> " + self.destination
        self.monitor_copy()

    def monitor_copy(self):
        "Executed during copy to print progressbar"

        while (self.cp_process.poll() is None):
            source_size = float(os.path.getsize(self.source))
            try:
                dest_size = float(os.path.getsize(self.destination))
            except OSError:  #Maybe file has not been created by cp yet
                dest_size = 0
            time.sleep(1)
            if source_size == 0: # Using pycp to copy an empty file. Why not?
                break
            self.pbar.update( (dest_size / source_size) * 100 )

        self.pbar.finish()
        exit (self.cp_process.returncode)

def usage():
    "Ouputs short usage message"
    print("Usage: pycp <SOURCE> <DESTINATION>")
    print("copy SOURCE to DESTINATION")
    print("""Options:
    --version: outputs version of pycp
    -h, --help: this help
    """)

def version():
    "Print version of pycp."
    print("pycp version " + __version__)
    print("Distributed under GPL license")


def main():
    "Main: manages options and values"

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv", ["help", "version"])
    except getopt.GetoptError, err:
        print(str(err))
        usage()
        exit(2)

    # dummy_value will never be used,
    # none of the options should take an argument
    for opt , dummy_value in opts:
        if opt in ("-h", "--help"):
            usage()
            exit(0)
        elif opt == "--version":
            version()
            exit(0)

    source = ""
    destination = ""

    #________
    # Do a few checks
    try:
        source = args[0]
        destination = args[1]
    except IndexError:
        print("Error: wrong number of arguments")
        print()
        usage()
        exit(1)

    if not (os.path.exists(source)):
        print("Error: file '" + source + "' does not exist")
        exit(1)

    if (os.path.exists(destination)):
        if os.path.isdir(destination):
            # "cp foo /bar" where bar is a  dir, is in fact "cp foo bar/foo"
            destination = os.path.join(destination, source)
        else:
            # refusing to override an exiting file
            print("Error: file '" + destination + "' already exists")
            exit(1)

    # Checks if we are trying to do a `cp foo .`:
    if os.path.abspath(source) == os.path.abspath(destination):
        print("Error: '" +
               source + "' and '" + destination + "' are the same file")
        exit(1)

    #________
    # Everything OK, proceed:
    copy_manager = CopyManager(source, destination)

    try:
        copy_manager.copy()
    except KeyboardInterrupt:
        exit(1)

if __name__ == "__main__" :
    main()

