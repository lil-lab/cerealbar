""" Contains utility functions for configurations and arguments.

Methods:
    get_args: Uses an argparser to build and interpret the command-line arguments.
"""

from argparse import ArgumentParser
from agent.config import program_args


def get_args() -> program_args.ProgramArgs:
    """ Interprets command line arguments, returning them as a ProgramArgs."""
    parser: ArgumentParser = ArgumentParser(description='Train or evaluate a Cereal Bar agent.')
    args: program_args.ProgramArgs = program_args.ProgramArgs(parser)
    args.interpret_args(parser.parse_args())

    return args
