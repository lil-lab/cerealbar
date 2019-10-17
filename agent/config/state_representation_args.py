""" Contains arguments for the environment state representation.

Classes:
    ChannelType (Enum): The types of state representations.
    ChannelArgs (Args): The arguments for the state representation.
"""
import numpy as np
import pickle

from argparse import ArgumentParser, Namespace
from distutils.util import strtobool
from agent.config import args
from agent.environment import card
from agent.model.state_representation import dense_state_representation

from typing import Dict, Tuple


class StateRepresentationArgs(args.Args):
    """ State representation arguments.

    Members:
        representation_type (ChannelType): The type of representation to use.
        out_channels (List[int]): The output size (# of channels) for each convolutional layer.
        kernel_sizes (List[int]): The sizes of the kernel for each convolutional layer.
        strides (List[int]): The strides of each convolutional layer.
    """
    # TODO: should refactor out the parameters specific to the state representation.

    def __init__(self, parser: ArgumentParser):
        super(StateRepresentationArgs, self).__init__()

        parser.add_argument('--full_observability',
                            default=True,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to assume full observability of the environment.')
        parser.add_argument('--property_embedding_size',
                            default=32,
                            type=int,
                            help='The size of the embeddings for each property if using a dense representation.')
        parser.add_argument('--build_style',
                            default=dense_state_representation.DenseBuildStyle.SUM,
                            type=dense_state_representation.DenseBuildStyle,
                            help='How to combine embeddings of properties into a single environment embedding.')
        parser.add_argument('--learn_absence_embeddings',
                            default=True,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to learn and use embeddings corresponding to the absence of objects.')

        self._full_observability: bool = None
        self._property_embedding_size: int = None
        self._build_style: dense_state_representation.DenseBuildStyle = None
        self._learn_absence_embeddings: bool = None

    def get_property_embedding_size(self) -> int:
        self.check_initialized()
        return self._property_embedding_size

    def get_build_style(self) -> dense_state_representation.DenseBuildStyle:
        self.check_initialized()
        return self._build_style

    def learn_absence_embeddings(self) -> bool:
        self.check_initialized()
        return self._learn_absence_embeddings

    def full_observability(self) -> bool:
        self.check_initialized()
        return self._full_observability

    def interpret_args(self, parsed_args: Namespace) -> None:
        self._full_observability = parsed_args.full_observability

        if not self._full_observability:
            raise ValueError('Partial observability is not yet supported.')

        self._learn_absence_embeddings = parsed_args.learn_absence_embeddings
        self._build_style = parsed_args.build_style
        self._property_embedding_size = parsed_args.property_embedding_size

        super(StateRepresentationArgs, self).interpret_args(parsed_args)

    def __str__(self) -> str:
        str_rep: str = '*** State representation arguments ***' \
                       '\n\tFull observability? %r' \
                       '\n\tLearn absence embeddings? %r' \
                       '\n\tBuild style: %r' \
                       '\n\tProperty embedding size: %r' % (self._full_observability, self._learn_absence_embeddings,
                                                            self._build_style, self._property_embedding_size)
        return str_rep

    def __eq__(self, other) -> bool:
        if isinstance(other, StateRepresentationArgs):
            return self._full_observability == other.full_observability() and self._learn_absence_embeddings == \
                   other.learn_absence_embeddings() and self._build_style == other.get_build_style() and \
                   self._property_embedding_size == other.get_property_embedding_size()
        return False
