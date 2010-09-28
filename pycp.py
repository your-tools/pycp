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


"""Little script to display progress bars
while transferring files from command line
"""

__author__ = "Yannick LM"
__author_email__  = "yannicklm1337 AT gmail DOT com"
__version__ = "5.0"

ERRORS = []

import os
import sys
import stat

from optparse import OptionParser

from progressbar import ProgressBar
from progressbar import ProgressBarWidget
from progressbar import Percentage
from progressbar import FileTransferSpeed
from progressbar import ETA
from progressbar import Bar

####
# Utilities functions:

def die(message):
    """An error occured.
    Write it to stderr and exit with error code 1

    """
    sys.stderr.write(str(message) + "\n")
    sys.exit(1)

def debug(message):
    """Useful for debug
    Messages will only be written if DEBUG env var is true

    """
    if os.environ.get("DEBUG"):
        print message

def human_readable(size):
    """Build a nice human readable string from a size given in
    bytes

    """
    if size < 1024**2:
        hreadable = float(size)/1024.0
        return "%.0fK" % hreadable
    elif size < (1024**3):
        hreadable = float(size)/(1024**2)
        return "%.1fM" % round(hreadable,1)
    else:
        hreadable = float(size)/(1024.0**3)
        return "%.2fG" % round(hreadable,2)

def samefile(src, dest):
    """Check if two files are the same in a
    crossplatform way

    """
    # If os.path.samefile exists, use it:
    if hasattr(os.path,'samefile'):
        try:
            return os.path.samefile(src, dest)
        except OSError:
            return False

    # All other platforms: check for same pathname.
    def normalise(path):
        """trying to be sure two paths are *really*
        equivalents

        """
        res = os.path.normcase(os.path.normpath(os.path.abspath(path)))
        return res

    return normalise(src) == normalise(dest)


def pprint_transfer(src, dest):
    """
    Directly borrowed from git's diff.c file.

    pprint_rename("/path/to/foo", "/path/to/bar")
    >>> /path/to/{foo => bar}
    """
    len_src = len(src)
    len_dest = len(dest)

    # Find common prefix
    pfx_length = 0
    i = 0
    j = 0
    while (i < len_src and j < len_dest and src[i] == dest[j]):
        if src[i] == os.path.sep:
            pfx_length = i + 1
        i += 1
        j += 1

    # Find common suffix
    sfx_length = 0
    i  = len_src - 1
    j = len_dest - 1
    while (i > 0 and j > 0 and src[i] == dest[j]):
        if src[i] == os.path.sep:
            sfx_length = len_src - i
        i -= 1
        j -= 1

    src_midlen  = len_src  - pfx_length - sfx_length
    dest_midlen = len_dest - pfx_length - sfx_length

    pfx   = src[:pfx_length]
    sfx   = dest[len_dest - sfx_length:]
    src_mid  = src [pfx_length:pfx_length + src_midlen ]
    dest_mid = dest[pfx_length:pfx_length + dest_midlen]

    if pfx == os.path.sep:
        # The common prefix is / ,
        # avoid print /{etc => tmp}/foo, and
        # print {/etc => /tmp}/foo
        pfx = ""
        src_mid  = os.path.sep + src_mid
        dest_mid = os.path.sep + dest_mid

    if not pfx and not sfx:
        return "%s => %s" % (src, dest)

    res = "%s{%s => %s}%s" % (pfx, src_mid, dest_mid, sfx)
    return res

class TransferError(Exception):
    """Custom exception: wraps IOError

    """
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message


class TransferInfo():
    """This class contains:
    * a list of tuples: to_transfer (src, dest) where:
       - src and dest are both files
       - basename(dest) is guaranteed to exist)
    * an add(src, dest) method
    * a get_size() which is the total size of the files to be
    transferred

    """
    def __init__(self, options, sources, destination):
        self.size = 0
        self.options = options
        # List of tuples (src, dest) of files to transfer
        self.to_transfer = list()
        # List of directories to remove
        self.to_remove = list()
        self._recursive_parse(sources, destination)

    def _recursive_parse(self, sources, destination):

        filenames    = [x for x in sources if os.path.isfile(x)]
        directories  = [x for x in sources if os.path.isdir (x)]

        for filename in filenames:
            self._parse_file(filename, destination)

        for directory in directories:
            self._parse_dir(directory, destination)

    def _parse_file(self, source, destination):
        """Add a tuple to self.transfer_info

        a_file, b_dir  => a_file, b_dir/a_file
        a_file, b_file => a_file, b_file
        """
        debug(":: file %s -> %s" % (source, destination))
        if os.path.isdir(destination):
            destination = os.path.join(destination, os.path.basename(source))
        self.add(source, destination)

    def _parse_dir(self, source, destination):
        """Parse a directory

        """
        debug(":: dir %s -> %s" % (source, destination))
        if os.path.isdir(destination):
            destination = os.path.join(destination, os.path.basename(source))
        debug(":: making dir %s" % destination)
        if not os.path.exists(destination):
            os.mkdir(destination)
        file_names = sorted(os.listdir(source))
        if not self.options.all:
            file_names = [f for f in file_names if not f.startswith(".")]
        file_names = [os.path.join(source, f) for f in file_names]
        self._recursive_parse(file_names, destination)
        self.to_remove.append(source)

    def add(self, src, dest):
        """Add a new tuple to the transfer list. """
        self.to_transfer.append((src, dest))
        self.size += os.path.getsize(src)


class NumFilesWidget(ProgressBarWidget):
    def update(self, pbar):
        return "(%i files / %i)" % \
            (pbar.num_done, pbar.num_total)


def transfer_file(parent, src, dest, callback):
    """Transfer src to dest, calling
    callback(done, total) while doing so.

    src and dest must be two valid file paths.

    If "move" option is True, remove src when done.
    """
    if samefile(src, dest):
        die("%s and %s are the same file!" % (src, dest))
    try:
        src_file = open(src, "rb")
    except IOError:
        raise TransferError("Could not open %s for reading" % src)
    try:
        dest_file = open(dest, "wb")
    except IOError:
        raise TransferError("Could not open %s for writing" % dest)

    buff_size = 18 * 1024
    done = 0
    total = os.path.getsize(src)

    try:
        while True:
            data = src_file.read(buff_size)
            if not data:
                break
            done += len(data)
            callback(done, total)
            dest_file.write(data)
    except IOError, err:
        mess  = "Problem when transferring %s to %s\n" % (src, dest)
        mess += "Error was: %s" % err
        raise TransferError(mess)
    finally:
        src_file.close()
        dest_file.close()

    try:
        post_transfer(parent, src, dest)
    except OSError, err:
        print "Warning: failed to finalize transfer of %s: %s" % (dest, err)

    if parent.options.move:
        try:
            debug("removing %s" % src)
            os.remove(src)
        except OSError:
            print "Warning: could not remove %s" % src


def post_transfer(parent, src, dest):
    """Handle stat of transferred file

    By default, preserve only permissions.
    If "preserve" option was given, preserve also
    utime and flags.

    """
    src_st = os.stat(src)
    if hasattr(os, 'chmod'):
        mode = stat.S_IMODE(src_st.st_mode)
        os.chmod(dest, mode)
    if not parent.options.preserve:
        return
    if hasattr(os, 'utime'):
        os.utime(dest, (src_st.st_atime, src_st.st_mtime))


class FileTransferManager():
    """This class contains the progressbar object.

    It also contains an options object, filled by optparse.

    It is initialized with a source and a destination, which
    should be correct files. (No dirs here!)

    """
    def __init__(self, parent, src, dest):
        self.parent = parent
        self.options = parent.options
        self.src = src
        self.dest = dest
        self.pbar = None

    def do_transfer(self):
        """Print src->dest in a nice way, initialize progressbar,
        close it when done

        """
        # Handle overwriting of files:
        if os.path.exists(self.dest):
            should_skip = self.handle_overwrite()
            if should_skip:
                return

        if not self.options.global_pbar:
            print pprint_transfer(self.src, self.dest)
            self.pbar = ProgressBar(
              widgets = [
                Percentage()                          ,
                " "                                   ,
                Bar(marker='#', left='[', right=']' ) ,
                " - "                                 ,
                FileTransferSpeed()                   ,
                " | "                                 ,
                ETA() ])
            self.pbar.start()
        try:
            transfer_file(self, self.src, self.dest, self.callback)
        except TransferError, err:
            if self.options.ignore_errors:
                # remove dest file
                global ERRORS
                ERRORS.append(self.src)
                if not self.options.move:
                    os.remove(self.dest)
            else:
                die(err)
        if not self.options.global_pbar:
            self.pbar.finish()

    def handle_overwrite(self):
        """Return True if we should skip the file.
        Ask user for confirmation if we were called
        with an 'interactive' option.

        """
        # Safe: always skip
        if self.options.safe:
            print "Warning: skipping", self.dest
            return True

        # Not safe and not interactive => overwrite
        if not self.options.interactive:
            return False

        # Interactive
        print "File: '%s' already exists" % self.dest
        print "Overwrite?"
        user_input = raw_input()
        if (user_input == "y"):
            return False
        else:
            return True

    def callback(self, done, total):
        """Called by transfer_file"""
        if self.options.global_pbar:
            self.parent.update(done)
        else:
            self.pbar.maxval = total
            self.pbar.update(done)


class TransferManager():
    """Handles transfer of a one or several sources to a destination

    if options.global_pbar is true, only
    one pbar will be created for the whole transfer.

    One FileTransferManager object will be created for each file
    to transfer.

    """
    def __init__(self, options, sources, destination):
        self.options = options
        self.sources = sources
        self.destination = destination
        self.transfer_info = TransferInfo(options, sources, destination)
        self.current_total = 0
        self.global_pbar = None

    def do_transfer(self):
        """Performs the real transfer"""
        if self.options.global_pbar:
            self.global_pbar = ProgressBar(
              widgets = [
                Percentage()                          ,
                " "                                   ,
                Bar(marker='#', left='[', right=']' ) ,
                " - "                                 ,
                FileTransferSpeed()                   ,
                " - "                                 ,
                ETA() ,
                " - ",
                NumFilesWidget()])
            total_size = self.transfer_info.size
            self.global_pbar.maxval = total_size
            to_print = ", ".join(self.sources)
            to_print += " => "
            to_print += self.destination
            to_print += " ( " + human_readable(total_size) + " ) "
            print to_print
            self.global_pbar.num_done = 0
            self.global_pbar.num_total = len(self.transfer_info.to_transfer)
            self.global_pbar.start()
        for (src, dest) in self.transfer_info.to_transfer:
            size = os.path.getsize(src)
            ftm = FileTransferManager(self, src, dest)
            ftm.do_transfer()
            if self.options.global_pbar:
                self.global_pbar.num_done += 1
                self.current_total += size

        if self.options.global_pbar:
            self.global_pbar.finish()

        if self.options.move and not self.options.ignore_errors:
            for to_remove in self.transfer_info.to_remove:
                os.rmdir(to_remove)

    def update(self, done):
        """Called during transfer of one file"""
        self.global_pbar.update(self.current_total + done)




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

    version = "%s version %s" % (prog_name, __version__)

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
        ignore_errors=False)

    (options, args) = parser.parse_args()
    options.move = move # This "option" is set by sys.argv[0]

    if len(args) < 2:
        parser.error("Incorrect number of arguments")

    sources = args[:-1]
    destination = args[-1]

    if len(sources) > 1:
        if not os.path.isdir(destination):
            die("%s is not an existing directory" % destination)

    for source in sources:
        if not os.path.exists(source):
            die("%s does not exist")

    transfer_manager = TransferManager(options, sources, destination)
    try:
        transfer_manager.do_transfer()
    except TransferError, err:
        die(err)
    except KeyboardInterrupt, err:
        die("Interrputed by user")

    global ERRORS
    if ERRORS:
        print "Error occurred when transferring the following files:"
        print "\n".join(ERRORS)


if __name__ == "__main__":
    main()
