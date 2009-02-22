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
"""

__author__ = "Yannick LM"
__author_email__  = "yannicklm1337 AT gmail DOT com"
__version__ = "2.1"

import subprocess
import sys
import time
import getopt

from os import path
from os import mkdir
from os import listdir

try:
    from progressbar import ProgressBar
    from progressbar import Percentage
    from progressbar import FileTransferSpeed
    from progressbar import ETA
    from progressbar import Bar
except ImportError:
    print "Error: Unable to find progressbar module"
    exit(1)


class CopyManager:
    """
    Class that manages cp process

    It is assumed that source and destination are both files.
    (No directory here)
    """
    def __init__(self, source, destination):
        self.cp_process         = None
        self.source             = source
        self.destination        = destination
        self.pbar               = None

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

        source_size = float(path.getsize(self.source))

        if source_size == 0: # Using pycp to copy an empty file. Why not?
            return

        # Use of wonderful constructor from progessbar.
        self.pbar = ProgressBar(
          widgets = [
            Percentage()                          ,
            " "                                   ,
            Bar(marker='#', left='[', right=']' ) ,
            " - "                                 ,
            FileTransferSpeed()                   ,
            " | "                                 ,
            ETA() ]                               ,
         maxval = source_size )

        while (self.cp_process.poll() is None):
            try:
                dest_size = float(path.getsize(self.destination))
            except OSError:  #Maybe file has not been created by cp yet
                dest_size = 0
            time.sleep(1)
            self.pbar.update(dest_size)

        self.pbar.finish()
        # Useful if something went wrong with cp
        if (self.cp_process.returncode != 0):
            exit (self.cp_process.returncode)

def usage():
    "Outputs short usage message"

    print """Usage: pycp SOURCE DESTINATION"
          or: pycp SOURCE ... DIRECTORY"
          copy SOURCE to DESTINATION, or multiple SOURCE(s) to DIRECTORY"

          Options:
            --version: outputs version of pycp
            -h, --help: this help
          """

def version():
    "Prints version of pycp."
    print "pycp version " + __version__
    print "Distributed under GPL license"


def main():
    "Main: manages options and values"

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv", ["help", "version"])
    except getopt.GetoptError, err:
        print err
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

    if len(args) < 2:
        print "Error: wrong number of arguments"
        usage()
        exit(1)

    sources = args[:-1]
    destination = args[-1]


    # If there is more than one source, destination must be an
    # existing directory
    if len(sources) > 1:
        if not (path.exists(destination)):
            print "Error: '" + destination + "' does not exists"
            exit(1)
        if not (path.isdir(destination)):
            print "Error: '" + destination + "' is not a directory"
            exit(1)

    ##______
    # Go!

    try:
        for source in sources:
            recursive_copy(source, destination)
    except KeyboardInterrupt:
        exit(1)


def _prepare_copy(source, destination):
    """ Do all the work needed to get back to a simple case:
    copying one file to an other file

    Create directories and modify destination when needed, and returns the new
    destination.

    Aborts if we are trying to override a file
    """

    new_destination = destination

    # First thing first ;)
    if not (path.exists(source)):
        print "Error: file '" + source + "' does not exist"
        exit(1)

    # If source is a file:
    if path.isfile(source):
        if (path.exists(destination)):
            if path.isdir(destination):
                # "cp /path/to/foo /bar" where bar is a  dir,
                # is in fact "cp /path/to/foo /bar/foo"
                new_destination = path.join(destination, path.basename(source))
            else:
                # refusing to override an exiting file
                print "Error: file '" + destination + "' already exists"
                exit(1)

        # Checks if we are trying to do a `cp foo .`:
        if path.abspath(source) == path.abspath(destination):
            print "Error: '" + source \
                             + "' and '" + destination + "' are the same file"
            exit(1)

    # If source is a dir:
    if path.isdir(source):
        # if destination exists, create a dir named source in destination ...
        if path.exists(destination):
            new_directory = path.join(destination, path.basename(source))

            # destination/source could already exist
            if not path.exists(new_directory):
                mkdir(new_directory)
            new_destination = new_directory

        # if destination does not exist, create a dir named destination
        else:
            mkdir(destination)

    return new_destination



def recursive_copy(source, destination):
    "To walk recursively through directories"

    # First prepare copy (creating directories if needed, and so on)
    new_destination = _prepare_copy(source, destination)

    if path.isdir(source):
        for file_name in listdir(source):
            recursive_copy(path.join(source,      file_name),
                           path.join(new_destination, file_name))
    else:
        copy_manager = CopyManager(source, new_destination)
        copy_manager.copy()


if __name__ == "__main__" :
    main()

