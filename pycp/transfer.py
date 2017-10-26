"""This module contains the TransferManager class.

This will do the work of transfering the files,
while using the FilePbar or the GlobalPbar from
pycp.progress

"""

import os
import stat

from pycp.util import debug
from pycp.progress import OneFileIndicator, GlobalIndicator


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
    if hasattr(os.path, 'samefile'):
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


def transfer_file(src, dest, callback, *, move=False, preserve=False):
    """Transfer src to dest, calling
    callback(xferd) while doing so,
    where xferd is the size of the buffer successfully transferred

    src and dest must be two valid file paths.

    If move is True, remove src when done.
    """
    check_same_file(src, dest)
    if os.path.islink(src):
        handle_symlink(src, dest)
        callback(0)
        return

    src_file, dest_file = open_files(src, dest)
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
    except IOError as err:
        mess = "Problem when transferring %s to %s\n" % (src, dest)
        mess += "Error was: %s" % err
        raise TransferError(mess)
    finally:
        src_file.close()
        dest_file.close()

    try:
        post_transfer(src, dest, preserve=preserve)
    except OSError as err:
        print("Warning: failed to finalize transfer of %s: %s" % (dest, err))

    if move:
        try:
            debug("removing %s" % src)
            os.remove(src)
        except OSError:
            print("Warning: could not remove %s" % src)


def check_same_file(src, dest):
    if samefile(src, dest):
        raise TransferError("%s and %s are the same file!" % (src, dest))


def handle_symlink(src, dest):
    target = os.readlink(src)
    # remove existing stuff
    if os.path.lexists(dest):
        os.remove(dest)
    os.symlink(target, dest)


def open_files(src, dest):
    try:
        src_file = open(src, "rb")
    except IOError:
        raise TransferError("Could not open %s for reading" % src)
    try:
        dest_file = open(dest, "wb")
    except IOError:
        raise TransferError("Could not open %s for writing" % dest)
    return src_file, dest_file


def post_transfer(src, dest, preserve=False):
    """Handle stat of transferred file

    By default, preserve only permissions.
    If "preserve" option was given, preserve also
    utime and flags.

    """
    src_st = os.stat(src)
    if hasattr(os, 'chmod'):
        mode = stat.S_IMODE(src_st.st_mode)
        os.chmod(dest, mode)
    if not preserve:
        return
    if hasattr(os, 'utime'):
        os.utime(dest, (src_st.st_atime, src_st.st_mtime))
    uid = src_st.st_uid
    gid = src_st.st_gid
    try:
        os.chown(dest, uid, gid)
    except OSError:
        # we likely don't have enough permissions to do this
        # just ignore
        pass


class TransferInfo():
    """This class contains:
    * a list of tuples: to_transfer (src, dest) where:
       - src and dest are both files
       - basename(dest) is guaranteed to exist)
    * an add(src, dest) method
    * a get_size() which is the total size of the files to be
    transferred

    """
    def __init__(self, sources, destination, *, all_files=False):
        self.all_files = all_files
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
        filenames = [x for x in sources if os.path.isfile(x)]
        directories = [x for x in sources if os.path.isdir(x)]

        for filename in filenames:
            self._parse_file(filename, destination)

        for directory in directories:
            self._parse_dir(directory, destination)

    def _parse_file(self, source, destination):
        """Parse a new source file

        """
        debug(":: file %s -> %s" % (source, destination))
        if os.path.isdir(destination):
            basename = os.path.basename(os.path.normpath(source))
            destination = os.path.join(destination, basename)
        self.add(source, destination)

    def _parse_dir(self, source, destination):
        """Parse a new source directory

        """
        debug(":: dir %s -> %s" % (source, destination))
        if os.path.isdir(destination):
            basename = os.path.basename(os.path.normpath(source))
            destination = os.path.join(destination, basename)
        debug(":: making dir %s" % destination)
        if not os.path.exists(destination):
            os.mkdir(destination)
        file_names = sorted(os.listdir(source))
        if not self.all_files:
            file_names = [f for f in file_names if not f.startswith(".")]
        file_names = [os.path.join(source, f) for f in file_names]
        self.parse(file_names, destination)
        self.to_remove.append(source)

    def add(self, src, dest):
        """Add a new tuple to the transfer list. """
        file_size = os.path.getsize(src)
        if not os.path.islink(src):
            self.size += file_size
        self.to_transfer.append((src, dest, file_size))


# pylint: disable=too-many-instance-attributes
class FileTransferManager():
    """This class handles transfering one file to an other
    It is initialized with a source and a destination, which
    should be correct files.

    The parent will be updated during transfer to monitor progress

    """
    def __init__(self, parent, src, dest, *, ignore_errors=False,
                 move=False, safe=False, interactive=False):
        self.safe = safe
        self.interactive = interactive
        self.ignore_errors = ignore_errors
        self.move = move
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
            transfer_file(self.src, self.dest, self.callback,
                          move=self.move)
        except TransferError as exception:
            if self.ignore_errors:
                error = exception
                # remove dest file
                if not self.move:
                    try:
                        os.remove(self.dest)
                    except OSError:
                        # We don't want to raise here
                        pass

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
        if self.safe:
            print("Warning: skipping", self.dest)
            return True

        # Not safe and not interactive => overwrite
        if not self.interactive:
            return False

        # Interactive
        print("File: '%s' already exists" % self.dest)
        print("Overwrite?")
        user_input = input()
        if user_input == "y":
            return False
        else:
            return True

    def callback(self, xferd):
        """Called by transfer_file"""
        self.parent.update(xferd)


# pylint: disable=too-many-instance-attributes
class TransferManager():
    """Handles transfer of a one or several sources to a destination

    One FileTransferManager object will be created for each file
    to transfer.

    """
    def __init__(self, sources, destination, *, global_progress=False, move=False,
                 ignore_errors=False, all_files=False, safe=False, interactive=False):
        self.sources = sources
        self.destination = destination
        self.transfer_info = TransferInfo(sources, destination)
        self.global_progress = global_progress
        self.ignore_errors = ignore_errors
        self.move = move
        self.all_files = all_files
        self.safe = safe
        self.interactive = interactive
        self.global_pbar = None
        self.file_pbar = None
        self.num_files = 0
        self.file_index = 0

    def do_transfer(self):
        """Performs the real transfer"""
        errors = dict()
        self.num_files = len(self.transfer_info.to_transfer)
        if self.global_progress:
            total_size = self.transfer_info.size
            self.global_pbar = GlobalIndicator(self.num_files, total_size)
            self.global_pbar.start()
        for (src, dest, file_size) in self.transfer_info.to_transfer:
            self.file_index += 1
            ftm = FileTransferManager(self, src, dest,
                                      safe=self.safe, interactive=self.interactive,
                                      ignore_errors=self.ignore_errors, move=self.move)
            self.on_new_transfer(src, dest, file_size)
            error = ftm.do_transfer()
            if self.file_pbar:
                self.file_pbar.on_file_done()
            if self.global_pbar:
                self.global_pbar.on_file_done()
            if error:
                errors[src] = error

        if not self.global_progress:
            self.file_pbar.stop()

        if self.move and not self.ignore_errors:
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
        if self.global_progress:
            self.global_pbar.on_new_file(src, size)
        else:
            self.file_pbar = OneFileIndicator(
                src=src,
                dest=dest,
                index=self.file_index,
                count=self.num_files,
                size=size)
            self.file_pbar.start()

    def on_file_transfer(self, xferd):
        """If global pbar is False:
        update the file_pbar

        """
        if self.global_progress:
            self.global_pbar.on_file_transfer(xferd)
        else:
            self.file_pbar.on_file_transfer(xferd)
