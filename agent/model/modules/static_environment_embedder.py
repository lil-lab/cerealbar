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
    from typing import List, Optional


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
                 zero_out: bool = False):
        super(StaticEnvironmentEmbedder, self).__init__()

        self._state_rep: state_representation.StateRepresentation = state_rep

        if zero_out:
            raise ValueError('Zeroing out zero-value properties is no longer supported due to optimizations.')

        all_embeddings = state_rep.get_terrains() + state_rep.get_hut_colors() + state_rep.get_hut_rotations() + \
            state_rep.get_windmill_rotations() + state_rep.get_tower_rotations() + \
            state_rep.get_tent_rotations() + state_rep.get_tree_types() + state_rep.get_plant_types() + \
            state_rep.get_prop_types()
        self._embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(embedding_size, all_embeddings,
                                                                                add_unk=False, must_be_unique=False)

    def embedding_size(self) -> int:
        """ Returns the embedding size for a tensor coming out of the forward method. """
        return self._embedder.embedding_size()

    def forward(self, terrains, hut_colors, hut_rotations, windmill_rotations, tower_rotations, tent_rotations,
                tree_types, plant_types, prop_types) -> torch.Tensor:
        # TODO: Need to make this backwards compatible with old model saves.

        # [1] Update the indices of each tensor to come after the previous tensors
        prefix_length = len(self._state_rep.get_terrains())
        hut_colors = hut_colors + prefix_length
        prefix_length += len(self._state_rep.get_hut_colors())
        hut_rotations = hut_rotations + prefix_length
        prefix_length += len(self._state_rep.get_hut_rotations())
        windmill_rotations = windmill_rotations + prefix_length
        prefix_length += len(self._state_rep.get_windmill_rotations())
        tower_rotations = tower_rotations + prefix_length
        prefix_length += len(self._state_rep.get_tower_rotations())
        tent_rotations = tent_rotations + prefix_length
        prefix_length += len(self._state_rep.get_tent_rotations())
        tree_types = tree_types + prefix_length
        prefix_length += len(self._state_rep.get_tree_types())
        plant_types = plant_types + prefix_length
        prefix_length += len(self._state_rep.get_plant_types())
        prop_types = prop_types + prefix_length

        # [2] Stack the properties into a single tensor. Don't need to reshape it, because Pytorch embedding just
        # looks up an embedding for each index in the entire tensor, regardless of its size.
        stacked_properties = torch.stack((terrains, hut_colors, hut_rotations, windmill_rotations, tower_rotations,
                                          tent_rotations, tree_types, plant_types, prop_types))

        # [3] Embed.
        # The output should be of size N x B x H x W x C.
        #   N is the number of property types.
        #   B is the batch size.
        #   H is the height of the environment.
        #   W is the width of the environment.
        #   C is the embedding size.
        all_property_embeddings = self._embedder(stacked_properties)

        # Permute so it is B x N x C x H x W.
        all_property_embeddings = all_property_embeddings.permute(1, 0, 4, 2, 3)

        # Then sum across the property type dimension.
        emb_state = torch.sum(all_property_embeddings, dim=1)

        return emb_state
