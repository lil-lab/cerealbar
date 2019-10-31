""" Contains arguments for the model's decoder.

Classes:
    DecoderArgs (Args): Arguments for the decoder.
"""
from argparse import ArgumentParser, Namespace
from distutils.util import strtobool

from agent.config import args


class ActionGeneratorArgs(args.Args):
    """ Decoder arguments for the action decoder. """
    def __init__(self, parser: ArgumentParser):
        super(ActionGeneratorArgs, self).__init__()

        # Recurrence over actions
        parser.add_argument('--use_recurrence',
                            default=True,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to use recurrence linking observed states in the decoder.')
        parser.add_argument('--action_embedding_size',
                            default=32,
                            type=int,
                            help='Size of the embeddings for the agent actions.')
        parser.add_argument('--decoder_hidden_size',
                            default=128,
                            type=int,
                            help='Size of the RNN cell in the decoder.')
        parser.add_argument('--decoder_num_layers',
                            default=1,
                            type=int,
                            help='Number of layers in the RNN of the decoder.')

        # State representation
        parser.add_argument('--state_internal_size',
                            default=64,
                            type=int,
                            help='The size to compress the inputs (e.g., distributions over the map) to before passing '
                                 'to '
                                 'the RNN.')
        parser.add_argument('--crop_size',
                            default=5,
                            type=int,
                            help='The size to crop a transformed distribution to.')
        parser.add_argument('--convolution_encode_map_distributions',
                            default=True,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to use convolutional encodings of the map distributions.')

        # Types of inputs to the action predictor
        parser.add_argument('--use_goal_probabilities',
                            default=False,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to use card information to predict actions.')
        parser.add_argument('--use_obstacle_probabilities',
                            default=False,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to use impassable locations as input to the action predictor.')
        parser.add_argument('--use_avoid_probabilities',
                            default=False,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to use locations to avoid as input to the action predictor.')
        parser.add_argument('--use_trajectory_distribution',
                            default=False,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to use trajectory as input to the action predictor.')
        parser.add_argument('--weight_trajectory_by_time',
                            default=True,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to weight trajectory visitation probabilities by the number of timesteps '
                                 'spent on that hex.')

        # Parameter freezing and training
        parser.add_argument('--end_to_end',
                            default=False,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to train plan predictor in addition (end-to-end) '
                                 'with the action generator.')
        parser.add_argument('--pretrained_action_generator_filepath',
                            default='',
                            type=str,
                            help='The path containing a pretrained action decoder.')
        parser.add_argument('--pretrained_plan_predictor_filepath',
                            default='',
                            type=str,
                            help='The path containing a pretrained hex predictor.')

        self._use_goal_probabilities: bool = None
        self._use_trajectory_distribution: bool = None
        self._use_avoid_probabilities: bool = None
        self._use_obstacle_probabilities: bool = None
        self._weight_trajectory_by_time: bool = None

        self._use_recurrence: bool = None
        self._action_embedding_size: int = None
        self._hidden_size: int = None
        self._num_layers: int = None

        self._state_internal_size: int = None
        self._crop_size: int = None
        self._convolution_encode_map_distributions: bool = None

        self._end_to_end: bool = None
        self._pretrained_action_generator_filepath: str = None
        self._pretrained_plan_predictor_filepath: str = None

    def convolution_encode_map_distributions(self) -> bool:
        self.check_initialized()
        return self._convolution_encode_map_distributions

    def use_avoid_probabilities(self) -> bool:
        self.check_initialized()
        return self._use_avoid_probabilities

    def use_trajectory_distribution(self) -> bool:
        self.check_initialized()
        return self._use_trajectory_distribution

    def use_obstacle_probabilities(self) -> bool:
        self.check_initialized()
        return self._use_obstacle_probabilities

    def use_goal_probabilities(self) -> bool:
        self.check_initialized()
        return self._use_goal_probabilities

    def pretrained_generator(self) -> bool:
        self.check_initialized()
        return bool(self._pretrained_action_generator_filepath)

    def pretrained_action_generator_filepath(self) -> str:
        self.check_initialized()
        return self._pretrained_action_generator_filepath

    def pretrained_plan_predictor(self) -> bool:
        self.check_initialized()
        return bool(self._pretrained_plan_predictor_filepath)

    def pretrained_plan_predictor_filepath(self) -> str:
        self.check_initialized()
        return self._pretrained_plan_predictor_filepath

    def end_to_end(self) -> bool:
        self.check_initialized()
        return self._end_to_end

    def use_recurrence(self) -> bool:
        self.check_initialized()
        return self._use_recurrence

    def get_action_embedding_size(self) -> int:
        self.check_initialized()
        return self._action_embedding_size

    def get_hidden_size(self) -> int:
        self.check_initialized()
        return self._hidden_size

    def get_num_layers(self) -> int:
        self.check_initialized()
        return self._num_layers

    def get_state_internal_size(self) -> int:
        self.check_initialized()
        return self._state_internal_size

    def get_crop_size(self) -> int:
        self.check_initialized()
        return self._crop_size

    def weight_trajectory_by_time(self) -> bool:
        self.check_initialized()
        return self._weight_trajectory_by_time

    def interpret_args(self, parsed_args: Namespace) -> None:
        self._use_recurrence = parsed_args.use_recurrence
        if self._use_recurrence:
            self._action_embedding_size = parsed_args.action_embedding_size
            self._hidden_size = parsed_args.decoder_hidden_size
            self._num_layers = parsed_args.decoder_num_layers

        self._end_to_end = parsed_args.end_to_end
        self._pretrained_action_generator_filepath = parsed_args.pretrained_action_generator_filepath
        self._pretrained_plan_predictor_filepath = parsed_args.pretrained_plan_predictor_filepath

        self._use_goal_probabilities = parsed_args.use_goal_probabilities
        self._use_avoid_probabilities = parsed_args.use_avoid_probabilities
        self._use_obstacle_probabilities = parsed_args.use_obstacle_probabilities
        self._use_trajectory_distribution = parsed_args.use_trajectory_distribution
        self._weight_trajectory_by_time = parsed_args.weight_trajectory_by_time

        if not (self._use_goal_probabilities or self._use_avoid_probabilities or self._use_obstacle_probabilities or
                self._use_trajectory_distribution):
            raise ValueError('At least one of goal/avoid/obstacle/trajectory should be used as input to action '
                             'predictor.')

        self._convolution_encode_map_distributions = parsed_args.convolution_encode_map_distributions
        self._state_internal_size = parsed_args.state_internal_size
        self._crop_size = parsed_args.crop_size

        if not self._end_to_end:
            if self._pretrained_plan_predictor_filepath or self._pretrained_action_generator_filepath:
                raise ValueError('Should be end to end when providing pretrained components.')

        super(ActionGeneratorArgs, self).interpret_args(parsed_args)

    def __str__(self) -> str:
        str_rep: str = '*** Action Generator arguments ***' \
                       '\n\tUse recurrence? %r ' % self.use_recurrence()
        if self.use_recurrence():
            str_rep += '\n\tAction embedding size: %r' \
                       '\n\tHidden size: %r' \
                       '\n\tNumber of layers: %r\n' % (self._action_embedding_size, self._hidden_size, self._num_layers)

        str_rep += '\n\tUse goal probabilities? %r' \
                   '\n\tUse avoid probabilities? %r' \
                   '\n\tUse obstacle probabilities? %r' \
                   '\n\tUse trajectory distribution? %r' % (self.use_goal_probabilities(),
                                                          self.use_avoid_probabilities(),
                                                          self.use_obstacle_probabilities(),
                                                          self.use_trajectory_distribution())
        if self.use_trajectory_distribution():
            str_rep += '\n\tWeight trajectory by time? %r\n' % self._weight_trajectory_by_time

        str_rep += '\n\tConvolution encoding of map distributions? %r' \
                   '\n\tMap encoding internal size: %r' \
                   '\n\tCrop size: %r' % (self._convolution_encode_map_distributions, self._state_internal_size,
                                        self._crop_size)
        str_rep += '\n\n\tTrain end to end? %r' \
                   '\n\tLoading plan predictor from: %r' \
                   '\n\tLoading action generator from: %r' % (self.end_to_end(),
                                                            self.pretrained_plan_predictor_filepath(),
                                                            self.pretrained_action_generator_filepath())

        return str_rep

    def __eq__(self, other) -> bool:
        return self._action_embedding_size == other.get_action_embedding_size() \
               and self._hidden_size == other.get_hidden_size() \
               and self._num_layers == other.get_num_layers() \
               and self._state_internal_size == other.get_state_internal_size() \
               and self._crop_size == other.get_crop_size() \
               and self._use_recurrence == other.use_recurrence() \
               and self._use_goal_probabilities == other.use_goal_probabilities() \
               and self._weight_trajectory_by_time == other.weight_trajectory_by_time() \
               and self.use_obstacle_probabilities() == other.use_obstacle_probabilities() \
               and self.use_avoid_probabilities() == other.use_avoid_probabilities() \
               and self.use_trajectory_distribution() == other.use_trajectory_distribution() \
               and self.convolution_encode_map_distributions() == other.convolution_encode_map_distributions()
