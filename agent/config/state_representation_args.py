""" Contains arguments for the environment state representation.

Classes:
    ChannelType (Enum): The types of state representations.
    ChannelArgs (Args): The arguments for the state representation.
"""
from argparse import ArgumentParser, Namespace
from distutils.util import strtobool
from agent.config import args


class StateRepresentationArgs(args.Args):
    """ State representation arguments."""
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
        parser.add_argument('--learn_absence_embeddings',
                            default=True,
                            type=lambda x: bool(strtobool(x)),
                            help='Whether to learn and use embeddings corresponding to the absence of objects.')

        self._full_observability: bool = None
        self._property_embedding_size: int = None
        self._learn_absence_embeddings: bool = None

    def get_property_embedding_size(self) -> int:
        self.check_initialized()
        return self._property_embedding_size

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
        self._property_embedding_size = parsed_args.property_embedding_size

        super(StateRepresentationArgs, self).interpret_args(parsed_args)

    def __str__(self) -> str:
        str_rep: str = '*** State representation arguments ***' \
                       '\n\tFull observability? %r' \
                       '\n\tLearn absence embeddings? %r' \
                       '\n\tProperty embedding size: %r' % (self._full_observability, self._learn_absence_embeddings,
                                                            self._property_embedding_size)
        return str_rep

    def __eq__(self, other) -> bool:
        if isinstance(other, StateRepresentationArgs):
            return self._full_observability == other.full_observability() and self._learn_absence_embeddings == \
                   other.learn_absence_embeddings() and  \
                   self._property_embedding_size == other.get_property_embedding_size()
        return False
