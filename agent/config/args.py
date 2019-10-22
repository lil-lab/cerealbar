""" Contains the abstract class for arguments to the program.

Classes:
    Args (ABC): Abstract class for arguments allowing interpretation and initialization. Uses argparse.
"""
from abc import ABC
from argparse import Namespace


class Args(ABC):
    """ Abstract class for arguments.

    Members:
        initialized (bool): Whether the instance arguments are initialized and valid to use.

    """

    def __init__(self):
        self._initialized: bool = False

    def interpret_args(self, parsed_args: Namespace) -> None:
        """ Interprets the arguments included in the parsed command line arguments.

        Inputs:
            parsed_args (Namespace): The parsed command line arguments.
        """
        self._initialized = True

    def is_initialized(self) -> bool:
        """ Returns whether these arguments have been initialized.

        Returns:
            True if initialized; false otherwise.
        """
        return self._initialized

    def check_initialized(self) -> None:
        """ Raises a ValueError if not initialized. """
        if not self.is_initialized():
            raise ValueError('Arguments are not initialized.')
