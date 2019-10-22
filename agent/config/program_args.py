""" Contains arguments for running the main program.

Classes:
    RunType (Enum): Various modes of running the program.
    ProgramArgs (Args): The arguments for running the program.

Methods:
    save_args: Saves the program args to a specified directory.
    check_args: Checks args in a specified location for equality and replaces them if necessary.
"""
import os
import pickle
from argparse import ArgumentParser, Namespace
from enum import Enum

from agent.config import args
from agent.config import data_args
from agent.config import evaluation_args
from agent.config import game_args
from agent.config import model_args
from agent.config import replay_args
from agent.config import training_args


class RunType(Enum):
    """ Different types of running the program: training, evaluation, or replaying recorded interactions. """
    TRAIN: str = 'TRAIN'
    EVALUATE: str = 'EVALUATE'
    REPLAY: str = 'REPLAY'

    def __str__(self) -> str:
        return self.value


class ProgramArgs(args.Args):
    """ Arguments for running the program.

    Members:
        _run_type (RunType): The run type for this run.
        _model_args (ModelArgs): The arguments for the model parameters.
        _game_args (GameArgs): The arguments for playing the game.
        _training_args (TrainingArgs): The arguments for training the agent.
        _replay_args (ReplayArgs): The arguments for replaying a static game.
        _evaluation_args (EvalArgs): The arguments for evaluating a model.
    """

    def __init__(self, parser: ArgumentParser):
        super(ProgramArgs, self).__init__()

        parser.add_argument('--run_type',
                            default=RunType.TRAIN,
                            type=RunType,
                            help='The run type for this run of the program.')

        self._run_type: RunType = None

        self._model_args: model_args.ModelArgs = model_args.ModelArgs(parser)
        self._game_args: game_args.GameArgs = game_args.GameArgs(parser)
        self._training_args: training_args.TrainingArgs = training_args.TrainingArgs(parser)
        self._replay_args: replay_args.ReplayArgs = replay_args.ReplayArgs(parser)
        self._evaluation_args: evaluation_args.EvaluationArgs = evaluation_args.EvaluationArgs(parser)
        self._data_args: data_args.DataArgs = data_args.DataArgs(parser)

    def interpret_args(self, parsed_args: Namespace) -> None:
        self._run_type = parsed_args.run_type

        # Interpret the sub-configs.

        self._game_args.interpret_args(parsed_args)
        if self._run_type in {RunType.TRAIN, RunType.EVALUATE}:
            self._model_args.interpret_args(parsed_args)
            self._training_args.interpret_args(parsed_args)
            self._data_args.interpret_args(parsed_args)

            self._evaluation_args.interpret_args(parsed_args)
        elif self._run_type == RunType.REPLAY:
            self._replay_args.interpret_args(parsed_args)

        super(ProgramArgs, self).interpret_args(parsed_args)

    def get_run_type(self) -> RunType:
        self.check_initialized()
        return self._run_type

    def get_model_args(self) -> model_args.ModelArgs:
        self._model_args.check_initialized()
        return self._model_args

    def get_evaluation_args(self) -> evaluation_args.EvaluationArgs:
        self._evaluation_args.check_initialized()
        return self._evaluation_args

    def get_data_args(self) -> data_args.DataArgs:
        self._data_args.check_initialized()
        return self._data_args

    def set_data_args(self, new_args: data_args.DataArgs) -> None:
        self._data_args = new_args

    def get_game_args(self) -> game_args.GameArgs:
        self._game_args.check_initialized()
        return self._game_args

    def get_training_args(self) -> training_args.TrainingArgs:
        self._training_args.check_initialized()
        return self._training_args

    def get_replay_args(self) -> replay_args.ReplayArgs:
        self._replay_args.check_initialized()
        return self._replay_args

    def set_model_args(self, new_args: model_args.ModelArgs):
        self._model_args = new_args

    def set_training_args(self, new_args: training_args.TrainingArgs):
        self._training_args = new_args

    def __str__(self) -> str:
        str_rep: str = '*** Program arguments ***\n\trun type: %r\n\n%r' % (str(self._run_type),
                                                                            str(self._game_args))

        if self._run_type in {RunType.TRAIN, RunType.EVALUATE}:
            str_rep += '\n%r' % str(self._data_args)
            str_rep += '\n%r' % str(self._model_args)
            str_rep += '\n%r' % str(self._evaluation_args)
        elif self._run_type == RunType.REPLAY:
            str_rep += '\n%r' % str(self._replay_args)

        return str_rep.replace('\\n', '\n').replace('\\t', '\t').replace('"', '')

    def __eq__(self, other) -> bool:
        # We don't care about run type being the same, but do care about the model arguments.
        still_same: bool = (self._game_args == other.get_game_args() and self._evaluation_args ==
                            other.get_evaluation_args())
        if self._run_type == RunType.TRAIN:
            still_same = still_same and self._training_args == other.get_training_args()
        if self._run_type not in (RunType.REPLAY, RunType.AUTOPLAY):
            still_same = still_same and self._model_args == other.get_model_args()

        return still_same


def save_args(program_args: ProgramArgs, save_dir: str):
    """Saves the program args to a pkl file.

    Inputs:
        program_args (ProgramArgs): The args to save.
        save_dir (str): The directory to save the args in.

    Raises:
        ValueError, if arguments already exist at the target filename.

    """
    args_filename: str = os.path.join(save_dir, 'args.pkl')

    if os.path.exists(args_filename):
        raise ValueError('Args already exist at ' + args_filename)
    with open(args_filename, 'wb') as ofile:
        pickle.dump(program_args, ofile)


def check_args(program_args: ProgramArgs, replace: bool = True):
    """Checks the equality between two ProgramArgs.

    It will load another ProgramArgs from memory, determine where a previous version might have been saved,
    and check against it.

    Inputs:
        program_args (ProgramArgs): The specified ProgramArgs.
        replace (bool): Whether to replace the specified ProgramArgs with the ones loaded from the pkl file.

    Raises:
        ValueError, if
            - The specified ProgramArgs describes a save filepath that doesn't exist
            - The loaded ProgramArgs don't match the specified ProgramArgs (after replacement, if set)

    """

    # Load the ProgramArgs specified by program_args
    save_dir: str = program_args.get_training_args().get_save_directory()
    args_filename: str = os.path.join(save_dir, 'args.pkl')

    if not os.path.exists(args_filename):
        raise ValueError('Could not find program arguments in ' + save_dir)
    with open(args_filename, 'rb') as infile:
        loaded_args: ProgramArgs = pickle.load(infile)

    if replace:
        # If replacing then replace the model arguments to reflect what was loaded.
        program_args.set_model_args(loaded_args.get_model_args())
        program_args.set_training_args(loaded_args.get_training_args())

    if program_args != loaded_args:
        raise ValueError('Args are not the same (see above for mismatches).')
