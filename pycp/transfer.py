"""This module contains the TransferManager class.

This will do the work of transfering the files,
while using the FilePbar or the GlobalPbar from
pycp.progress

"""
import os
import stat

import pycp
from pycp.util import debug
from pycp.progress import FilePbar, GlobalPbar

class TransferError(Exception):
    """Custom exception: wraps IOError

    """
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

    def __str__(self):
        return self.message


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


def transfer_file(src, dest, callback):
    """Transfer src to dest, calling
    callback(xferd) while doing so,
    where xferd is the size of the buffer successfully transferred

    src and dest must be two valid file paths.

    If pycp.options.move is True, remove src when done.
    """
    if samefile(src, dest):
        raise TransferError("%s and %s are the same file!" % (src, dest))
    if os.path.islink(src):
        target = os.readlink(src)
        #remove existing stuff
        if os.path.lexists(dest):
            os.remove(dest)
        os.symlink(target, dest)
        callback(0)
        return
    try:
        src_file = open(src, "rb")
    except IOError:
        raise TransferError("Could not open %s for reading" % src)
    try:
        dest_file = open(dest, "wb")
    except IOError:
        raise TransferError("Could not open %s for writing" % dest)

    # FIXME: a buffer size this small consumes a lot of CPU ...
    buff_size = 100 * 1024
    xferd = 0
    try:
        while True:
            data = src_file.read(buff_size)
            if not data:
                callback(0)
                break
            xferd = len(data)
            callback(xferd)
            dest_file.write(data)
    except IOError, err:
        mess  = "Problem when transferring %s to %s\n" % (src, dest)
        mess += "Error was: %s" % err
        raise TransferError(mess)
    finally:
        src_file.close()
        dest_file.close()

    try:
        post_transfer(src, dest)
    except OSError, err:
        print "Warning: failed to finalize transfer of %s: %s" % (dest, err)

    if pycp.options.move:
        try:
            debug("removing %s" % src)
            os.remove(src)
        except OSError:
            print "Warning: could not remove %s" % src


def post_transfer(src, dest):
    """Handle stat of transferred file

    By default, preserve only permissions.
    If "preserve" option was given, preserve also
    utime and flags.

    """
    src_st = os.stat(src)
    if hasattr(os, 'chmod'):
        mode = stat.S_IMODE(src_st.st_mode)
        os.chmod(dest, mode)
    if not pycp.options.preserve:
        return
    if hasattr(os, 'utime'):
        os.utime(dest, (src_st.st_atime, src_st.st_mtime))


class TransferInfo():
    """This class contains:
    * a list of tuples: to_transfer (src, dest) where:
       - src and dest are both files
       - basename(dest) is guaranteed to exist)
    * an add(src, dest) method
    * a get_size() which is the total size of the files to be
    transferred

    """
    def __init__(self, sources, destination):
        self.size = 0
        # List of tuples (src, dest) of files to transfer
        self.to_transfer = list()
        # List of directories to remove
        self.to_remove = list()
        self.parse(sources, destination)

    def parse(self, sources, destination):
        """Recursively go through the sources, creating missing
        directories, computing total size to be transferred, and
        so on.

        """
        filenames    = [x for x in sources if os.path.isfile(x)]
        directories  = [x for x in sources if os.path.isdir (x)]

        for filename in filenames:
            self._parse_file(filename, destination)

        for directory in directories:
            self._parse_dir(directory, destination)

    def _parse_file(self, source, destination):
        """Parse a new source file

        """
        debug(":: file %s -> %s" % (source, destination))
        if os.path.isdir(destination):
            destination = os.path.join(destination, os.path.basename(source))
        self.add(source, destination)

    def _parse_dir(self, source, destination):
        """Parse a new source directory

        """
        debug(":: dir %s -> %s" % (source, destination))
        if os.path.isdir(destination):
            destination = os.path.join(destination, os.path.basename(source))
        debug(":: making dir %s" % destination)
        if not os.path.exists(destination):
            os.mkdir(destination)
        file_names = sorted(os.listdir(source))
        if not pycp.options.all:
            file_names = [f for f in file_names if not f.startswith(".")]
        file_names = [os.path.join(source, f) for f in file_names]
        self.parse(file_names, destination)
        self.to_remove.append(source)

    def add(self, src, dest):
        """Add a new tuple to the transfer list. """
        self.to_transfer.append((src, dest))
        if not os.path.islink(src):
            self.size += os.path.getsize(src)


class FileTransferManager():
    """This class handles transfering one file to an other
    It is initialized with a source and a destination, which
    should be correct files.

    The parent will be updated during transfer to monitor progress

    """
    def __init__(self, parent, src, dest):
        self.parent = parent
        self.src = src
        self.dest = dest
        self.pbar = None

    def do_transfer(self):
        """Called transfer_file, catch TransferError depending
        on the options.

        Returns an error message if something went wrong,
        and we did not raise

        """
        error = None
        # Handle overwriting of files:
        if os.path.exists(self.dest):
            should_skip = self.handle_overwrite()
            if should_skip:
                return
        try:
            transfer_file(self.src, self.dest, self.callback)
        except TransferError, err:
            if pycp.options.ignore_errors:
                error = err
                # remove dest file
                if not pycp.options.move:
                    os.remove(self.dest)
            else:
                # Re-raise
                raise
        return error

    def handle_overwrite(self):
        """Return True if we should skip the file.
        Ask user for confirmation if we were called
        with an 'interactive' option.

        """
        # Safe: always skip
        if pycp.options.safe:
            print "Warning: skipping", self.dest
            return True

        # Not safe and not interactive => overwrite
        if not pycp.options.interactive:
            return False

        # Interactive
        print "File: '%s' already exists" % self.dest
        print "Overwrite?"
        user_input = raw_input()
        if (user_input == "y"):
            return False
        else:
            return True

    def callback(self, xferd):
        """Called by transfer_file"""
        self.parent.update(xferd)


class TransferManager():
    """Handles transfer of a one or several sources to a destination

    One FileTransferManager object will be created for each file
    to transfer.

    """
    def __init__(self, sources, destination):
        self.sources = sources
        self.destination = destination
        self.transfer_info = TransferInfo(sources, destination)
        self.global_pbar = None
        self.file_pbar = None

    def do_transfer(self):
        """Performs the real transfer"""
        errors = dict()
        if pycp.options.global_pbar:
            num_files = len(self.transfer_info.to_transfer)
            total_size = self.transfer_info.size
            self.global_pbar = GlobalPbar(num_files, total_size)
            self.global_pbar.start()
        for (src, dest) in self.transfer_info.to_transfer:
            file_size = os.path.getsize(src)
            ftm = FileTransferManager(self, src, dest)
            self.on_new_transfer(src, dest, file_size)
            error = ftm.do_transfer()
            if error:
                errors[src] = error

        if pycp.options.move and not pycp.options.ignore_errors:
            for to_remove in self.transfer_info.to_remove:
                os.rmdir(to_remove)

        return errors

    def update(self, xferd):
        """Called during transfer of one file"""
        self.on_file_transfer(xferd)

    def on_new_transfer(self, src, dest, size):
        """If global pbar is false:
        create a new progress bar for just one file

        """
        if pycp.options.global_pbar:
            self.global_pbar.new_file(src, size)
        else:
            self.file_pbar = FilePbar(src, dest, size)
            self.file_pbar.start()

    def on_file_transfer(self, xferd):
        """If global pbar is False:
        update the file_pbar

        """
        if pycp.options.global_pbar:
            self.global_pbar.update(xferd)
        else:
            self.file_pbar.update(xferd)
