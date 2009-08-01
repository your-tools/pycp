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
Having a progress bar while transferring files

Main idea : forking the file transfer in background, while reading size of
sources and destinations.

Module is called pycp because only copy was supported at the beginning
"""

__author__ = "Yannick LM"
__author_email__  = "yannicklm1337 AT gmail DOT com"
__version__ = "3.2"

import subprocess
import time

from optparse import OptionParser

import os
from os import path
from os import mkdir
from os import listdir
from os import access

try:
    from progressbar import ProgressBar
    from progressbar import Percentage
    from progressbar import FileTransferSpeed
    from progressbar import ETA
    from progressbar import Bar
except ImportError:
    print "Error: Unable to find progressbar module"
    exit(1)


class FileTransferManager:
    """
    Class that manages file transfer process

    It is assumed that source and destination are both files.
    (No directory here)
    """
    def __init__(self, source, destination, executable, opts):
        self.file_transfer_process = None
        self.source                = source
        self.destination           = destination
        self.pbar                  = None
        self.executable            = executable
        self.opts                  = opts

    def transfer_file(self):
        "Main method of FileTransferManager"

        self.file_transfer_process = subprocess.Popen([self.executable,
        self.source,
        self.destination],
        stdout=subprocess.PIPE)

        print self.source + " -> " + self.destination
        self.monitor_file_transfer()

    def monitor_file_transfer(self):
        "Executed during file transfer to print progressbar"

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

        while (self.file_transfer_process.poll() is None):
            try:
                dest_size = float(path.getsize(self.destination))
            except OSError:  # Maybe file has not been created yet
                dest_size = 0
            time.sleep(1)
            self.pbar.update(dest_size)

        self.pbar.finish()
        # Useful if something went wrong.
        if (self.file_transfer_process.returncode != 0):
            exit (self.file_transfer_process.returncode)


def main(action="copy"):
    """
    Main: manages options and values

    The parameter action is the kind of file transfer we wish to do.
    (move or copy, for the moment)
    """


    file_transfer_opts = []
    executable = _get_exectuable(action)

    prog_name = "pycp"
    if action == "move":
        prog_name = "pymv"

    usage   =                                                      \
      "usage: " + prog_name + " [options] SOURCE DESTINATION\n"    \
    + "       " + prog_name + " [options] SOURCE ... DIRECTORY\n"  \
    + action + " SOURCE to DESTINATION, or multiple SOURCE(s) to DIRECTORY"

    version = prog_name + " version " + __version__ + "\n" \
              + "Distributed under GPL license"

    parser = OptionParser(usage, version=version)

    parser.add_option("-i", "--interactive",
            action  = "store_true",
            dest    = "interactive",
            help    = "ask before overwriting existing files",
            default = False)

    (options, args) = parser.parse_args()


    if len(args) < 2:
        parser.error("Incorrect number of arguments")


    if options.interactive:
        file_transfer_opts.append("interactive")

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
            recursive_file_transfer(source,
                    destination,
                    executable,
                    file_transfer_opts)
    except KeyboardInterrupt:
        exit(1)




def _prepare_file_transfer(source, destination, opts):
    """
    Do all the work needed to get back to a simple case:
    copying or move one file to an other file

    Create directories and modify destination when needed, and returns the new
    destination.

    If we are trying to overwrite a file, and that the corresponding option is
    not present, return (True, new_destination)
    """

    new_destination = destination
    skip            = False

    # First thing first ;)
    if not (path.exists(source)):
        print "Error: file '" + source + "' does not exist"
        exit(1)

    # If source is a file:
    if path.isfile(source):
        if path.exists(destination):
            if path.isdir(destination):
                # "cp /path/to/foo /bar" where bar is a  dir,
                # is in fact "cp /path/to/foo /bar/foo"
                source_file = path.basename(source)
                destination_file = path.join(destination, source_file)
                new_destination = destination_file

                # if /bar/foo exists, check if we should overwrite it:
                if path.exists(destination_file):
                    skip = _should_skip(destination_file, opts)
                    new_destination = destination_file

            else:
                # destination exists and is a file, (not a dir)
                # checking if we should overwrite it:
                skip = _should_skip(destination, opts)

    #! source is a file

    # If source is a dir:
    if path.isdir(source):
        # if destination exists, create a dir named source in destination
        if path.exists(destination):
            new_directory = path.join(destination, path.basename(source))

            # destination/source could already exist
            if not path.exists(new_directory):
                mkdir(new_directory)
                new_destination = new_directory

        # if destination does not exist, create a dir named destination
        else:
            mkdir(destination)
    #! source is is a dir

    # Checks if we are trying to do a `cp foo .`, or something similar:
    if path.abspath(source) == path.abspath(new_destination):
        print "Error: '" + source \
                         + "' and '" + new_destination + "' are the same file"
        skip = True

    return new_destination, skip


def recursive_file_transfer(source, destination, executable, opts):
    "To walk recursively through directories"

    # First prepare file transfer (creating directories if needed, and so on)
    new_destination, skip = _prepare_file_transfer(source,
            destination,
            opts)

    if not skip:
        if path.isdir(source):
            for file_name in listdir(source):
                recursive_file_transfer(path.join(source, file_name),
                               path.join(new_destination, file_name),
                               executable,
                               opts)
        else:
            file_transfer_manager = FileTransferManager(source,
                    new_destination,
                    executable,
                    opts)
            file_transfer_manager.transfer_file()


def _should_skip(destination, opts):
    """
    Returns True is we should skip the file.
    Ask for user confirmation if FileTransferManager was
    called with -i
    """

    if 'interactive' in opts:
        print "File: '" + destination +"' already exists"
        print "Overwrite?"
        user_input = raw_input()
        if (user_input == "y"):
            return False
        else:
            return True
    else:
        return False


def _get_exectuable(action):
    """
    Check that executable exists.

    Return full path of the executable
    """
    if action == "copy":
        executable_full_path = "/bin/cp"
    elif action == "move":
        executable_full_path = "/bin/mv"
    else:
        print "Error: action: " + action + "not supported (yet)"
        exit(1)

    if not access(executable_full_path, os.X_OK):
        print "Error: could not exectue " + executable_full_path + "!"
        exit(1)

    return executable_full_path



if __name__ == "__main__" :
    main()

