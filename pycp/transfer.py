"""This module contains the TransferManager class.

This will do the work of transferring the files,
while using the FilePbar or the GlobalPbar from
pycp.progress

"""

import os
import stat
import time
import typing

from pycp.progress import GlobalIndicator, OneFileIndicator, Progress, ProgressIndicator

BUFFER_SIZE = 100 * 1024


class TransferError(Exception):
    """Custom exception: wraps IOError"""

    def __init__(self, message: str) -> None:
        Exception.__init__(self)
        self.message = message

    def __str__(self) -> str:
        return self.message


class TransferOptions:
    def __init__(self) -> None:
        self.ignore_errors = False
        self.global_progress = False
        self.interactive = False
        self.preserve = False
        self.safe = False
        self.move = False

    def update(self, args: typing.Dict[str, typing.Any]) -> None:
        for name, value in vars(args).items():
            if hasattr(self, name):
                setattr(self, name, value)


def samefile(src: str, dest: str) -> bool:
    """Check if two files are the same in a
    crossplatform way

    """
    try:
        return os.path.samefile(src, dest)
    except OSError:
        return False


def check_same_file(src: str, dest: str) -> None:
    if samefile(src, dest):
        raise TransferError("%s and %s are the same file!" % (src, dest))


def handle_symlink(src: str, dest: str) -> None:
    target = os.readlink(src)
    # remove existing stuff
    if os.path.lexists(dest):
        os.remove(dest)
    os.symlink(target, dest)


def open_files(src: str, dest: str) -> typing.Tuple[typing.BinaryIO, typing.BinaryIO]:
    try:
        src_file = open(src, "rb")
    except IOError:
        raise TransferError("Could not open %s for reading" % src)
    try:
        dest_file = open(dest, "wb")
    except IOError:
        raise TransferError("Could not open %s for writing" % dest)
    return src_file, dest_file


class TransferInfo:
    """This class contains:
    * a list of tuples: to_transfer (src, dest) where:
       - src and dest are both files
       - basename(dest) is guaranteed to exist)
    * an add(src, dest) method
    * a get_size() which is the total size of the files to be
    transferred

    """

    def __init__(self, sources: typing.List[str], destination: str) -> None:
        self.size = 0
        # List of tuples (src, dest, size) of files to transfer
        self.to_transfer: typing.List[typing.Tuple[str, str, int]] = list()
        # List of directories to remove
        self.to_remove: typing.List[str] = list()
        self.parse(sources, destination)

    def parse(self, sources: typing.List[str], destination: str) -> None:
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

    def _parse_file(self, source: str, destination: str) -> None:
        """Parse a new source file"""
        if os.path.isdir(destination):
            basename = os.path.basename(os.path.normpath(source))
            destination = os.path.join(destination, basename)
        self.add(source, destination)

    def _parse_dir(self, source: str, destination: str) -> None:
        """Parse a new source directory"""
        if os.path.isdir(destination):
            basename = os.path.basename(os.path.normpath(source))
            destination = os.path.join(destination, basename)
        if not os.path.exists(destination):
            os.mkdir(destination)
        file_names = sorted(os.listdir(source))
        file_names = [os.path.join(source, f) for f in file_names]
        self.parse(file_names, destination)
        self.to_remove.append(source)

    def add(self, src: str, dest: str) -> None:
        """Add a new tuple to the transfer list."""
        file_size = os.path.getsize(src)
        if not os.path.islink(src):
            self.size += file_size
        self.to_transfer.append((src, dest, file_size))


Callback = typing.Callable[[int], None]


class FileTransferManager:
    """This class handles transferring one file to an other"""

    def __init__(self, src: str, dest: str, options: TransferOptions) -> None:
        self.src = src
        self.dest = dest
        self.options = options
        self.callback: Callback = lambda _: None

    def set_callback(self, callback: Callback) -> None:
        self.callback = callback

    def do_transfer(self) -> typing.Optional[Exception]:
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
                return None
        try:
            self.transfer_file()
        except TransferError as exception:
            if self.options.ignore_errors:
                error = exception
                # remove dest file
                if not self.options.move:
                    try:
                        os.remove(self.dest)
                    except OSError:
                        # We don't want to raise here
                        pass

            else:
                # Re-raise
                raise
        return error

    def transfer_file(self) -> None:
        """Transfer src to dest, calling
        callback(transferred) while doing so,
        where transferred is the size of the buffer successfully transferred

        src and dest must be two valid file paths.

        If move is True, remove src when done.
        """
        check_same_file(self.src, self.dest)
        if os.path.islink(self.src):
            handle_symlink(self.src, self.dest)
            self.callback(0)
            return

        src_file, dest_file = open_files(self.src, self.dest)
        transferred = 0
        try:
            while True:
                data = src_file.read(BUFFER_SIZE)
                if not data:
                    self.callback(0)
                    break
                transferred = len(data)
                self.callback(transferred)
                dest_file.write(data)
        except IOError as err:
            mess = "Problem when transferring %s to %s\n" % (self.src, self.dest)
            mess += "Error was: %s" % err
            raise TransferError(mess)
        finally:
            src_file.close()
            dest_file.close()

        try:
            self.post_transfer()
        except OSError as err:
            print("Warning: failed to finalize transfer of %s: %s" % (self.dest, err))

        if self.options.move:
            try:
                os.remove(self.src)
            except OSError:
                print("Warting: could not remove %s" % self.src)

    def post_transfer(self) -> None:
        """Handle state of transferred file

        By default, preserve only permissions.
        If "preserve" option was given, preserve also
        utime and flags.

        """
        src_st = os.stat(self.src)
        if hasattr(os, "chmod"):
            mode = stat.S_IMODE(src_st.st_mode)
            os.chmod(self.dest, mode)
        if not self.options.preserve:
            return
        if hasattr(os, "utime"):
            os.utime(self.dest, (src_st.st_atime, src_st.st_mtime))
        uid = src_st.st_uid
        gid = src_st.st_gid
        try:
            os.chown(self.dest, uid, gid)
        except OSError:
            # we likely don't have enough permissions to do this
            # just ignore
            pass

    def handle_overwrite(self) -> bool:
        """Return True if we should skip the file.
        Ask user for confirmation if we were called
        with an 'interactive' option.

        """
        # Safe: always skip
        if self.options.safe:
            print("Waning: skipping", self.dest)
            return True

        # Not safe and not interactive => overwrite
        if not self.options.interactive:
            return False

        # Interactive
        print("File: '%s' already exists" % self.dest)
        print("Overwrite?")
        user_input = input()
        if user_input == "y":
            return False
        else:
            return True


class TransferManager:
    """Handles transfer of a one or several sources to a destination

    One FileTransferManager object will be created for each file
    to transfer.

    """

    def __init__(
        self, sources: typing.List[str], destination: str, options: TransferOptions
    ) -> None:
        self.sources = sources
        self.destination = destination
        self.options = options
        self.transfer_info = TransferInfo(sources, destination)

        self.progress_indicator: ProgressIndicator = (
            GlobalIndicator() if self.options.global_progress else OneFileIndicator()
        )
        self.last_progress_update = 0.0
        self.last_progress: typing.Optional[Progress] = None

    def do_transfer(self) -> typing.Dict[str, Exception]:
        """Performs the real transfer"""
        errors: typing.Dict[str, Exception] = dict()
        progress = Progress()
        total_start = time.time()
        progress.total_done = 0
        progress.total_size = self.transfer_info.size
        progress.index = 0
        progress.count = len(self.transfer_info.to_transfer)
        self.progress_indicator.on_start()

        def on_file_transfer(transferred: int) -> None:
            progress.file_done += transferred
            progress.total_done += transferred
            now = time.time()
            progress.total_elapsed = now - total_start
            progress.file_elapsed = now - file_start
            self.last_progress = progress
            if now - self.last_progress_update > 0.1:
                self.progress_indicator.on_progress(progress)
                self.last_progress_update = now

        for src, dest, file_size in self.transfer_info.to_transfer:
            file_start = time.time()
            progress.index += 1
            progress.src = src
            progress.dest = dest
            progress.file_size = file_size
            progress.file_start = time.time()
            progress.file_done = 0

            ftm = FileTransferManager(src, dest, self.options)
            ftm.set_callback(on_file_transfer)
            self.progress_indicator.on_new_file(progress)
            error = ftm.do_transfer()
            if self.last_progress:
                self.progress_indicator.on_progress(self.last_progress)
            self.progress_indicator.on_file_done()
            if error:
                errors[src] = error

        self.progress_indicator.on_finish()
        if self.options.move and not self.options.ignore_errors:
            for to_remove in self.transfer_info.to_remove:
                try:
                    os.rmdir(to_remove)
                except OSError as error:
                    print(
                        "Warning: Failed to remove ",
                        to_remove,
                        ":\n",
                        error,
                        end="\n",
                        sep="",
                    )

        return errors
