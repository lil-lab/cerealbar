"""Defines how data is processed and loaded."""
import os
from argparse import ArgumentParser, Namespace
from distutils.util import strtobool

from agent.config import args
from agent.data import dataset_split


class DataArgs(args.Args):
    def __init__(self, parser: ArgumentParser):
        super(DataArgs, self).__init__()
        parser.add_argument('--saved_game_directory',
                            type=str,
                            help='The directory where the game data is stored.')
        parser.add_argument('--game_state_filename',
                            type=str,
                            help='Filename storing game information for all examples in the dataset')
        parser.add_argument('--case_sensitive',
                            default=False,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to take into account the case of characters in the instructions.')
        parser.add_argument('--minimum_wordtype_occurrence',
                            default=2,
                            type=int,
                            help='The minimum number of times a word type must occur in the training set '
                                 'to be in the vocabulary.')
        parser.add_argument('--validation_proportion',
                            default=0.05,
                            type=float,
                            help='The proportion of games to hold out from the official training set during training '
                                 '(NOT the dev set).')
        parser.add_argument('--maximum_instruction_index',
                            default=-1,
                            type=int,
                            help='The maximum instruction index; i.e., no instructions past this index will be '
                                 'included as examples.')

        self._game_directory: str = None
        self._case_sensitive: bool = None
        self._minimum_wordtype_occurrence: int = None
        self._game_state_filename: str = None
        self._validation_proportion: float = None
        self._maximum_instruction_index: int = None

    def get_split_filename(self, split: dataset_split.DatasetSplit) -> str:
        self.check_initialized()
        return os.path.join(self._game_directory, str(split).lower() + '.json')

    def get_game_state_filename(self) -> str:
        self.check_initialized()
        return self._game_state_filename

    def presaved(self, dataset_split: dataset_split.DatasetSplit, directory: str) -> bool:
        self.check_initialized()
        return os.path.exists(os.path.join(directory, str(dataset_split)))

    def case_sensitive(self) -> bool:
        self.check_initialized()
        return self._case_sensitive

    def get_minimum_wordtype_occurrence(self) -> int:
        self.check_initialized()
        return self._minimum_wordtype_occurrence

    def get_validation_proportion(self) -> float:
        self.check_initialized()
        return self._validation_proportion

    def get_maximum_instruction_index(self) -> int:
        self.check_initialized()
        return self._maximum_instruction_index

    def interpret_args(self, parsed_args: Namespace) -> None:
        self._game_directory = parsed_args.saved_game_directory
        self._case_sensitive = parsed_args.case_sensitive
        self._minimum_wordtype_occurrence = parsed_args.minimum_wordtype_occurrence
        self._game_state_filename = parsed_args.game_state_filename
        self._validation_proportion = parsed_args.validation_proportion
        self._maximum_instruction_index = parsed_args.maximum_instruction_index

        super(DataArgs, self).interpret_args(parsed_args)

    def __str__(self) -> str:
        print(self._initialized)
        str_rep: str = '*** Data arguments ***' \
                       '\n\tGame directory: %r' \
                       '\n\tGame state filename: %r' \
                       '\n\tValidation proportion: %r' \
                       '\n\tMaximum instruction index: %r' \
                       '\n\tCase sensitive? %r' \
                       '\n\tMinimum wordtype frequency: %r' % (self._game_directory, self._game_state_filename,
                                                               self.get_validation_proportion(),
                                                               self._maximum_instruction_index, self.case_sensitive(),
                                                               self.get_minimum_wordtype_occurrence())
        return str_rep

    def __eq__(self, other) -> bool:
        return self._game_state_filename == other.get_game_state_filename() \
               and self._case_sensitive == other.case_sensitive() \
               and self._minimum_wordtype_occurrence == other.get_minimum_wordtype_occurrence() \
               and self._maximum_instruction_index == other.get_maximum_instruction_index()
