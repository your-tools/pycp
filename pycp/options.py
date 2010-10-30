"""This modules contains
a Options class.

The attributes of this class can be set from
command line and read every where.
"""


class Options:
    """A simple class to represent all the available options

    """
    def __init__(self):
        self.opts = None

    def __getattr__(self, name):
        return getattr(self.opts, name)

OPTS = Options()

