"""Class for encoding text.

Classes:
    InstructionEncoder (nn.Module): Encodes a sequence of tokens (an instruction) into a sequence of hidden states.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

import torch
import torch.nn as nn

from agent.model.modules import word_embedder
from agent.model.utilities import initialization
from agent.model.utilities import rnn

if TYPE_CHECKING:
    from agent.config import text_encoder_args
    from typing import List


class TextEncoder(nn.Module):
    """ Module which encodes an instruction.

    Args:
        args: model_args.ModelArgs. The model arguments.
        vocabulary: List[str]. The sorted vocabulary.
        dropout: float. The amount of dropout to apply in the model. Default is 0.
    """
    def __init__(self, args: text_encoder_args.TextEncoderArgs,
                 vocabulary: List[str],
                 dropout: float = 0.):
        super(TextEncoder, self).__init__()

        self._args = args

        self._embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(self._args.get_word_embedding_size(),
                                                                                vocabulary)

        self._each_dir_hidden_size: int = int(self._args.get_hidden_size() / 2)

        self._dropout = nn.Dropout(dropout)

        self._rnn: nn.LSTM = nn.LSTM(self._args.get_word_embedding_size(),
                                     self._each_dir_hidden_size,
                                     self._args.get_number_of_layers(),
                                     batch_first=True,
                                     bidirectional=True,
                                     dropout=dropout)
        initialization.initialize_rnn(self._rnn)

    def get_vocabulary(self) -> List[str]:
        """ Returns the vocabulary for the model. """
        return self._embedder.get_vocabulary()

    def get_word_embedder(self) -> word_embedder.WordEmbedder:
        """ Returns the word embedder. """
        return self._embedder

    def forward(self, batched_instructions: torch.Tensor, batched_instruction_lengths: torch.Tensor) -> torch.Tensor:
        """ batched_instructions is a tensor of size B x T_in representing the token indices. """
        batch_embeddings: torch.Tensor = self._dropout(self._embedder(batched_instructions))

        return rnn.fast_run_rnn(batched_instruction_lengths, batch_embeddings, self._rnn)

    def encode(self, instructions: List[List[str]]) -> torch.Tensor:
        """ Encodes a list of instructions into a tensor.

        Args:
            instructions: List[List[str]]. The instructions to encode.

        """
        batch_indices: List[List[int]] = [[self._embedder.get_index(tok) for tok in seq] for seq in instructions]
        seq_lens: List[int] = [len(instruction) for instruction in instructions]

        # Basis of the sequence tensor: fill it with zeros first
        torch_indices: torch.Tensor = torch.zeros((len(instructions), max(seq_lens)), dtype=torch.long)
        for idx, (sequence, sequence_length) in enumerate(zip(batch_indices, seq_lens)):
            torch_indices[idx, :sequence_length] = torch.tensor(sequence, dtype=torch.long)

        # Now embed things
        batch_embeddings: torch.Tensor = self._embedder(torch_indices.to(DEVICE))

        return rnn.fast_run_rnn(torch.tensor(seq_lens, dtype=torch.long).to(DEVICE), batch_embeddings, self._rnn)
