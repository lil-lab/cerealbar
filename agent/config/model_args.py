""" Contains arguments for defining the model architecture.

Classes:
    ModelArgs (Args): Arguments that define the model architecture.
"""

from argparse import ArgumentParser, Namespace
from enum import Enum

from agent.config import action_generator_args
from agent.config import args
from agent.config import instruction_encoder_args
from agent.config import state_encoder_args
from agent.config import state_rep_args


class Task(Enum):
    """Various tasks that a model can have that affect its architecture."""

    # The plan predictor ONLY predicts distributions over the map.
    PLAN_PREDICTOR: str = 'CARDS_TO_REACH'

    # The action generator predicts actions, either using gold plan predictions, or predicted ones.
    ACTION_GENERATOR: str = 'PATH_FROM_TRAJ_JOINT'

    # A sequence-to-sequence baseline.
    SEQ2SEQ: str = 'SEQ2SEQ'

    def __str__(self) -> str:
        return self.value


class ModelArgs(args.Args):
    """ Model architecture arguments."""

    def __init__(self, parser: ArgumentParser):
        super(ModelArgs, self).__init__()

        parser.add_argument('--model_type',
                            default=Task.ACTION_GENERATOR,
                            type=Task,
                            help='Which type of model to train.')

        parser.add_argument('--dropout',
                            default=0.,
                            type=float,
                            help='The amount of dropout to apply in the network.')

        self._instruction_encoder_args: instruction_encoder_args.InstructionEncoderArgs = \
            instruction_encoder_args.InstructionEncoderArgs(parser)
        self._state_encoder_args: state_encoder_args.StateEncoderArgs = state_encoder_args.StateEncoderArgs(parser)
        self._state_rep_args: state_rep_args.StateRepresentationArgs = state_rep_args.StateRepresentationArgs(parser)
        self._decoder_args: action_generator_args.ActionGeneratorArgs = action_generator_args.ActionGeneratorArgs(
            parser)

        self._task: Task = None

        self._dropout: float = None

    def get_task(self) -> Task:
        self.check_initialized()
        return self._task

    def get_dropout(self) -> float:
        self.check_initialized()
        return self._dropout

    def get_decoder_args(self) -> action_generator_args.ActionGeneratorArgs:
        self.check_initialized()
        return self._decoder_args

    def get_state_rep_args(self) -> state_rep_args.StateRepresentationArgs:
        self.check_initialized()
        return self._state_rep_args

    def get_instruction_encoder_args(self) -> instruction_encoder_args.InstructionEncoderArgs:
        self.check_initialized()
        return self._instruction_encoder_args

    def get_state_encoder_args(self) -> state_encoder_args.StateEncoderArgs:
        self.check_initialized()
        return self._state_encoder_args

    def interpret_args(self, parsed_args: Namespace) -> None:
        self._task = parsed_args.model_type

        self._dropout = parsed_args.dropout

        self._state_encoder_args.interpret_args(parsed_args)
        self._state_rep_args.interpret_args(parsed_args)
        self._instruction_encoder_args.interpret_args(parsed_args)
        self._decoder_args.interpret_args(parsed_args)

        super(ModelArgs, self).interpret_args(parsed_args)

    def __str__(self) -> str:
        str_rep: str = '***Model arguments ***\nmodel type: %r\ndropout: %r' % (self._task, self._dropout)
        str_rep += str(self._instruction_encoder_args) + '\n'
        str_rep += str(self._state_encoder_args) + '\n' + str(self._state_rep_args) + '\n'
        str_rep += str(self._decoder_args) + '\n'

        return str_rep

    def __eq__(self, other) -> bool:
        still_same: bool = self._task == other.get_task()
        still_same = still_same and self._instruction_encoder_args == other.get_instruction_encoder_args()
        still_same = still_same and self._state_encoder_args == other.get_state_encoder_args()
        still_same = still_same and self._decoder_args == other.get_decoder_args()

        return still_same
