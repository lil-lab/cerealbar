"""Contains arguments for a text encoder."""
from argparse import ArgumentParser, Namespace

from agent.config import args


class TextEncoderArgs(args.Args):
    def __init__(self, parser: ArgumentParser):
        super(TextEncoderArgs, self).__init__()

        parser.add_argument('--encoder_cell_type',
                            default='LSTM',
                            type=str,
                            choices=['RNN', 'GRU', 'LSTM'],
                            help='The RNN cell type for the text encoder.')
        parser.add_argument('--word_embedding_size',
                            default=64,
                            type=int,
                            help='Size of the embeddings for the text tokens.')
        parser.add_argument('--encoder_hidden_size',
                            default=64,
                            type=int,
                            help='Size of the RNN cell in the text encoder.')
        parser.add_argument('--encoder_number_layers',
                            default=1,
                            type=int,
                            help='Number of layers in the RNN of the text encoder.')

        self._cell_type: str = None
        self._word_embedding_size: int = None
        self._hidden_size: int = None
        self._number_layers: int = None

    def get_hidden_size(self) -> int:
        self.check_initialized()
        return self._hidden_size

    def get_word_embedding_size(self) -> int:
        self.check_initialized()
        return self._word_embedding_size

    def get_number_of_layers(self) -> int:
        self.check_initialized()
        return self._number_layers

    # TODO: Getters for the other properties

    def interpret_args(self, parsed_args: Namespace):
        self._cell_type = parsed_args.encoder_cell_type
        self._word_embedding_size = parsed_args.word_embedding_size
        self._hidden_size = parsed_args.encoder_hidden_size
        self._number_layers = parsed_args.encoder_number_layers

        super(TextEncoderArgs, self).interpret_args(parsed_args)

    def __str__(self) -> str:
        str_rep: str = '*** Encoder arguments ***' \
                       '\n\tWord embedding size: %r' \
                       '\n\tRNN hidden size: %r' \
                       '\n\tRNN cell type: %r' \
                       '\n\tRNN number of layers: %r' % (self._word_embedding_size, self._hidden_size, self._cell_type,
                                                         self._number_layers)
        return str_rep

    def __eq__(self, other) -> bool:
        assert isinstance(other, TextEncoderArgs)
        return (self._cell_type == other._cell_type and self._word_embedding_size == other.get_word_embedding_size()
                and self._hidden_size == other.get_hidden_size() and self._number_layers ==
                other.get_number_of_layers())
