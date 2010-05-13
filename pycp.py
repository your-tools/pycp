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
__version__ = "4.3"

import sys
import time
import shutil

from threading import Thread
from threading import Event
from optparse import OptionParser

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
    sys.exit(1)


class FileTransferManager:
    """
    Class that manages file transfer process

    It is assumed that source and destination are both files.
    (No directory here)

    """
    def __init__(self, source, destination, action, opts):
        self.file_transfer = None
        self.source        = source
        self.destination   = destination
        self.pbar          = None
        self.action        = action
        self.opts          = opts


    def transfer_file(self):
        """
        Create a FileTransfer instance to start transfer
        in a thread, and start monitoring transfer

        """
        self.file_transfer = FileTransfer(self.source,
                self.destination,
                self.action)
        self.file_transfer.start()
        to_print = pprint_transfer(self.source, self.destination)
        print to_print
        self.monitor_file_transfer()


    def monitor_file_transfer(self):
        """
        Executed during file transfer to update the progressbar

        """
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

        while (not self.file_transfer.is_finished()):
            try:
                dest_size = float(path.getsize(self.destination))
            except OSError:  # Maybe file has not been created yet
                dest_size = 0
            time.sleep(1)
            self.pbar.update(dest_size)

        self.pbar.finish()

def main(action="copy"):
    """
    Main: manages options and values

    The parameter action is the kind of file transfer we wish to do.
    (move or copy, for the moment)

    """
    prog_name = "pycp"
    if action == "move":
        prog_name = "pymv"

    usage   =                                                      \
      "usage: " + prog_name + " [options] SOURCE... DESTINATION\n"    \
    + action + " SOURCE(s) to DESTINATION\n"

    version = prog_name + " version " + __version__ + "\n" \
              + "Distributed under GPL license"

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

    parser.set_defaults(
        safe       = False,
        interactive = False)

    (options, args) = parser.parse_args()

    if len(args) < 2:
        parser.error("Incorrect number of arguments")

    sources = args[:-1]
    destination = args[-1]

    # If there is more than one source, destination must be an
    # existing directory
    if len(sources) > 1:
        if not (path.isdir(destination)):
            print "Error: '" + destination + "' is not an existing directory"
            sys.exit(1)

    ##______
    # Go!

    try:
        for source in sources:
            recursive_file_transfer(source,
                    destination,
                    action,
                    options)
    except KeyboardInterrupt:
        sys.exit(1)



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
        sys.exit(1)

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

        else:
            # destination does not exist
            if destination.endswith(path.sep):
                print "Error, directory destination: %s does not exists" % \
                    destination
                sys.exit(1)

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
        sys.exit(2)

    return new_destination, skip


def recursive_file_transfer(source, destination, action, opts):
    """
    Recursively wakl through directories,

    """
    # First prepare file transfer (creating directories if needed, and so on)
    new_destination, skip = _prepare_file_transfer(source,
            destination,
            opts)

    if not skip:
        if path.isdir(source):
            for file_name in listdir(source):
                recursive_file_transfer(path.join(source, file_name),
                               path.join(new_destination, file_name),
                               action,
                               opts)
        else:
            file_transfer_manager = FileTransferManager(source,
                    new_destination,
                    action,
                    opts)
            file_transfer_manager.transfer_file()


def _should_skip(destination, opts):
    """
    Returns True is we should skip the file.
    Ask for user confirmation if FileTransferManager was
    called with -i

    """
    if opts.safe:
        print "Warning: skipping", destination
        return True

    if opts.interactive:
        print "File: '" + destination +"' already exists"
        print "Overwrite?"
        user_input = raw_input()
        if (user_input == "y"):
            return False
        else:
            return True
    else:
        return False



class FileTransfer(Thread):
    """
    Lauch a shutil command in a thread

    """
    def __init__(self, source, destination, action):
        self.source      = source
        self.destination = destination
        self.action      = action
        self._is_finished = Event()
        self._is_finished.clear()
        Thread.__init__(self)


    def run(self):
        """
        Main method of FileTransfer

        Executed when start() is called
        """
        if self.action == "copy":
            shutil.copy(self.source, self.destination)
        elif self.action == "move":
            shutil.move(self.source, self.destination)
        self._is_finished.set()

    def is_finished(self):
        """
        Getter for _is_finished Event

        """
        return self._is_finished.isSet()



def pprint_transfer(a, b):
    """
    Directly borrowed from git's diff.c file.

    *pprint_rename(const char *a, const char *b)
    """
    len_a = len(a)
    len_b = len(b)

    # Find common prefix
    pfx_length = 0
    i1 = 0
    i2 = 0
    while (i1 < len_a and i2 < len_b and a[i1] == b[i2]):
        if a[i1] == path.sep:
            pfx_length = i1 + 1
        i1 += 1
        i2 += 1

    # Find common suffix
    sfx_length = 0
    i1 = len_a - 1
    i2 = len_b - 1
    while (i1 > 0 and i2 > 0 and a[i1] == b[i2]):
        if a[i1] == path.sep:
            sfx_length = len_a - i1
        i1 -= 1
        i2 -= 1

    a_midlen = len_a - pfx_length - sfx_length
    b_midlen = len_b - pfx_length - sfx_length

    pfx   = a[:pfx_length]
    sfx   = b[len_b - sfx_length:]
    a_mid = a[pfx_length:pfx_length+a_midlen]
    b_mid = b[pfx_length:pfx_length+b_midlen]

    if pfx == path.sep:
        pfx = ""
        a_mid = path.sep + a_mid
        b_mid = path.sep + b_mid

    if not pfx and not sfx:
        return "%s => %s" % (a, b)

    res = "%s{%s => %s}%s" % (pfx, a_mid, b_mid, sfx)
    return res


if __name__ == "__main__" :
    main()

