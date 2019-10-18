""" Contains utility functions for configurations and arguments.

Methods:
    get_args: Uses an argparser to build and interpret the command-line arguments.
"""

from argparse import ArgumentParser

from config.program_args import ProgramArgs


def get_args() -> ProgramArgs:
    """ Interprets command line arguments, returning them as a ProgramArgs."""
    parser: ArgumentParser = ArgumentParser(description='Train or evaluate a Cereal Bar agent.')
    program_args: ProgramArgs = ProgramArgs(parser)
    program_args.interpret_args(parser.parse_args())

    return program_args
