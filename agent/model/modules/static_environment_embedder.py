""" Environment embedder for static parts of an environment (e.g., terrain, static props).

Classes:
    StaticEnvironmentEmbedder (nn.Module): Embeds the static information about an environment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
import torch.nn as nn

from agent.environment import util as environment_util
from agent.learning import batch_util
from agent.model.modules import state_representation
from agent.model.modules import word_embedder

if TYPE_CHECKING:
    from typing import List


class StaticEnvironmentEmbedder(nn.Module):
    """ Embedder for the static parts of an environment.

    Args:
        state_rep: DenseStateRepresentation. Formal representation of the environment properties.
        embedding_size: int. The size of each underlying embedding.
        zero_out: bool. Whether or not to zero-out embeddings which represent absence of a property.
            The terrain embedder is never zeroed out.
    """

    def __init__(self,
                 state_rep: state_representation.StateRepresentation,
                 embedding_size: int,
                 zero_out: bool = True):
        super(StaticEnvironmentEmbedder, self).__init__()

        self._terrain_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(embedding_size,
                                                                                        state_rep.get_terrains(),
                                                                                        add_unk=False,
                                                                                        zero_out=False)

        self._hut_colors_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(embedding_size,
                                                                                           state_rep.get_hut_colors(),
                                                                                           add_unk=False,
                                                                                           zero_out=zero_out)

        self._hut_rotations_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(
            embedding_size, state_rep.get_hut_rotations(), add_unk=False, zero_out=zero_out)

        self._windmill_rotations_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(
            embedding_size, state_rep.get_windmill_rotations(), add_unk=False, zero_out=zero_out)

        self._tower_rotations_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(
            embedding_size, state_rep.get_tower_rotations(), add_unk=False, zero_out=zero_out)

        self._tent_rotations_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(
            embedding_size, state_rep.get_tent_rotations(), add_unk=False, zero_out=zero_out)

        self._tree_types_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(embedding_size,
                                                                                           state_rep.get_tree_types(),
                                                                                           add_unk=False,
                                                                                           zero_out=zero_out)

        self._plant_types_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(embedding_size,
                                                                                            state_rep.get_plant_types(),
                                                                                            add_unk=False,
                                                                                            zero_out=zero_out)

        self._prop_types_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(embedding_size,
                                                                                           state_rep.get_prop_types(),
                                                                                           add_unk=False,
                                                                                           zero_out=zero_out)

        self._embedders: List[word_embedder.WordEmbedder] = [self._prop_types_embedder,
                                                             self._hut_colors_embedder,
                                                             self._hut_rotations_embedder,
                                                             self._tree_types_embedder,
                                                             self._plant_types_embedder,
                                                             self._windmill_rotations_embedder,
                                                             self._tower_rotations_embedder,
                                                             self._tent_rotations_embedder,
                                                             self._terrain_embedder]

    def embedding_size(self) -> int:
        """ Returns the embedding size for a tensor coming out of the forward method. """
        return self._embedders[0].embedding_size()

    def forward(self, *args) -> torch.Tensor:
        input_tensors: List[torch.Tensor] = list(args)

        batch_size = input_tensors[0].size(0)

        # First, embed the properties independently
        embedded_tensors: List[torch.Tensor] = \
            [batch_util.bhwc_to_bchw(embedder(tensor.view(batch_size,
                                                          -1)).view(batch_size,
                                                                    environment_util.ENVIRONMENT_WIDTH,
                                                                    environment_util.ENVIRONMENT_DEPTH,
                                                                    embedder.embedding_size()))
             for embedder, tensor in zip(self._embedders, input_tensors)]

        stacked_tensors = torch.stack(tuple(embedded_tensors))
        permuted_tensor = stacked_tensors.permute(1, 0, 2, 3, 4)
        emb_state = torch.sum(permuted_tensor, dim=1)

        return emb_state
