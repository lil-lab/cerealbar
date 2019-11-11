"""Contains arguments for evaluating a saved model."""
from argparse import ArgumentParser, Namespace
from distutils.util import strtobool
from agent.config import args
from agent.data import dataset_split


class EvaluationArgs(args.Args):
    def __init__(self, parser: ArgumentParser):
        super(EvaluationArgs, self).__init__()
        parser.add_argument('--save_file',
                            default='',
                            type=str,
                            help='The model save file to load from.')
        parser.add_argument('--maximum_generation_length',
                            default=-1,
                            type=int,
                            help='The maximum output length. If less than zero, there is no limit.')
        parser.add_argument('--reset_after_instruction',
                            default=False,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to reset each game after each instruction to the correct state.')
        parser.add_argument('--use_unity',
                            default=True,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to use the Unity compiled game to run simulations.')
        parser.add_argument('--split',
                            default=dataset_split.DatasetSplit.DEV,
                            type=dataset_split.DatasetSplit,
                            help='The split to evaluate on.')
        parser.add_argument('--metric_distance_threshold',
                            default=0,
                            type=int,
                            help='The maximum distance the follower must be from a correct position to be considered in'
                                 ' the correct final state (relaxed metric)')
        parser.add_argument('--examples_filename',
                            default='',
                            type=str,
                            help='If split is SPECIFIED, this is the filename containing the IDs for the examples.')
        parser.add_argument('--visualize_auxiliaries',
                            default=False,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to show the auxiliary distributions in the Unity game.')
        parser.add_argument('--evaluation_results_filename',
                            default='',
                            type=str,
                            help='Filename to write evaluation results to. If empty string, will not be written.')

        self._save_file: str = None
        self._maximum_generation_length: int = None
        self._reset_after_instruction: bool = None
        self._use_unity: bool = None
        self._split: dataset_split.DatasetSplit = None
        self._distance_threshold: int = None
        self._examples_filename: str = None
        self._visualize_auxiliaries: bool = None
        self._evaluation_results_filename: str = None

    def get_evaluation_results_filename(self) -> str:
        self.check_initialized()
        return self._evaluation_results_filename

    def get_save_file(self) -> str:
        self.check_initialized()
        return self._save_file

    def get_maximum_generation_length(self) -> int:
        self.check_initialized()
        return self._maximum_generation_length

    def reset_after_instruction(self) -> bool:
        self.check_initialized()
        return self._reset_after_instruction

    def get_distance_threshold(self) -> int:
        self.check_initialized()
        return self._distance_threshold

    def use_unity(self) -> bool:
        self.check_initialized()
        return self._use_unity

    def get_split(self) -> dataset_split.DatasetSplit:
        self.check_initialized()
        return self._split

    def get_examples_filename(self) -> str:
        self.check_initialized()
        return self._examples_filename

    def visualize_auxiliaries(self) -> bool:
        self.check_initialized()
        return self._visualize_auxiliaries

    def interpret_args(self, parsed_args: Namespace):
        self._save_file = parsed_args.save_file
        self._maximum_generation_length = parsed_args.maximum_generation_length
        self._reset_after_instruction = parsed_args.reset_after_instruction
        self._use_unity = parsed_args.use_unity
        self._split = parsed_args.split
        self._distance_threshold = parsed_args.metric_distance_threshold
        self._visualize_auxiliaries = parsed_args.visualize_auxiliaries
        self._evaluation_results_filename = parsed_args.evaluation_results_filename

        if self._visualize_auxiliaries and not self._use_unity:
            raise ValueError('Need to use Unity to visualize auxiliaries.')

        if (self._split == dataset_split.DatasetSplit.SPECIFIED) != bool(self._examples_filename):
            raise ValueError('Examples filename must only be provided when dataset split is specified, '
                             'and must be provided in that case.')

        self._examples_filename = parsed_args.examples_filename

        super(EvaluationArgs, self).interpret_args(parsed_args)

    def __str__(self) -> str:
        str_rep: str = '*** Inference arguments ***' \
                       '\n\tUse Unity? %r' \
                       '\n\tVisualize auxiliaries? %r' \
                       '\n\tSave file: %r' \
                       '\n\tWriting to filename: %r' \
                       '\n\tMaximum output sequence length: %r' \
                       '\n\tReset after instruction? %r' \
                       '\n\tSplit: %r' \
                       '\n\tDistance threshold: %r' % (self.use_unity(), self.visualize_auxiliaries(),
                                                       self.get_save_file(),
                                                       self._evaluation_results_filename,
                                                       self.get_maximum_generation_length(),
                                                       self.reset_after_instruction(), self.get_split(),
                                                       self.get_distance_threshold())
        if self.get_split() == dataset_split.DatasetSplit.SPECIFIED:
            str_rep += '\n\tSpecified example IDs: %r' % self.get_examples_filename()
        return str_rep

    def __eq__(self, other) -> bool:
        return True
