"""Module for embedding words."""
from typing import Any, List

import torch
import torch.nn as nn

UNK_TOK: str = "_UNK"
PAD_TOK: str = "_PAD"


class WordEmbedder(nn.Module):
    def __init__(self, embedding_size: int, vocabulary: List[Any], add_unk: bool = True, zero_out: bool = False):
        super(WordEmbedder, self).__init__()

        self._vocabulary: List[Any] = [PAD_TOK] + vocabulary
        self._embedding_size: int = embedding_size
        self._zero_out: bool = zero_out

        if add_unk:
            self._vocabulary.append(UNK_TOK)

        self.embeddings: nn.Embedding = nn.Embedding(len(self._vocabulary), self._embedding_size)

        torch.nn.init.xavier_normal_(self.embeddings.weight)

    def embedding_size(self) -> int:
        return self._embedding_size

    def vocabulary_size(self) -> int:
        return len(self._vocabulary)

    def get_vocabulary(self) -> List[Any]:
        return self._vocabulary

    def get_index(self, token: Any) -> int:
        if token not in self._vocabulary:
            index = self._vocabulary.index(UNK_TOK)
        else:
            index = self._vocabulary.index(token)
        return index

    def forward(self, indices_tensor: torch.Tensor) -> torch.Tensor:
        """ Embeds an indexed string into a tensor."""
        # B x L x E
        embeddings = self.embeddings(indices_tensor)

        if self._zero_out:
            # Multiply embeddings by min(indices_tensor, 1)
            # indices_tensor is size B x L, mask is the same size
            mask: torch.Tensor = torch.clamp(indices_tensor, max=1.).unsqueeze(2).expand_as(embeddings).float()
            embeddings = embeddings * mask

        return embeddings
