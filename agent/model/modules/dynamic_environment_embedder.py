""" Environment embedder for dynamic parts of an environment (e.g., card information; player information).

Classes:
    DynamicEnvironmentEmbedder (nn.Module): Embeds the dynamic information about an environment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
import torch.nn as nn

from agent.environment import util as environment_util
from agent.learning import batch_util
from agent.model.modules import word_embedder

if TYPE_CHECKING:
    from agent.model.modules import state_representation


class DynamicEnvironmentEmbedder(nn.Module):
    """ Dynamic environment embedder.

    Args:
        state_rep: DenseStateRepresentation. Formal representation of the environment properties.
        embedding_size: int. The size of each underlying embedding.
        zero_out: bool. Whether or not to zero-out embeddings which represent absence of a property.
    """

    def __init__(self,
                 state_rep: state_representation.StateRepresentation,
                 embedding_size: int,
                 zero_out: bool = False):
        super(DynamicEnvironmentEmbedder, self).__init__()

        self._state_rep: state_representation.StateRepresentation = state_rep

        if zero_out:
            raise ValueError('Zeroing out zero-value properties is no longer supported due to optimizations.')

        # A single embedding lookup is used for all properties.
        all_embeddings = state_rep.get_card_counts() + state_rep.get_card_colors() + state_rep.get_card_shapes() + \
            state_rep.get_card_selection() + state_rep.get_leader_rotation() + \
            state_rep.get_follower_rotation()
        self._embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(embedding_size,
                                                                                all_embeddings,
                                                                                add_unk=False,
                                                                                must_be_unique=False)

    def embedding_size(self) -> int:
        """ Returns the size of embeddings resulting from calling the forward method. """
        return self._embedder.embedding_size()

    def forward(self,
                card_counts: torch.Tensor,
                card_colors: torch.Tensor,
                card_shapes: torch.Tensor,
                card_selections: torch.Tensor,
                leader_rotations: torch.Tensor,
                follower_rotations: torch.Tensor) -> torch.Tensor:
        # TODO: Need to make this backwards compatible with old model saves.

        # [1] Update the indices of each tensor to come after the previous tensors
        prefix_length = len(self._state_rep.get_card_counts())
        card_colors = card_colors + prefix_length
        prefix_length += len(self._state_rep.get_card_colors())
        card_shapes = card_shapes + prefix_length
        prefix_length += len(self._state_rep.get_card_shapes())
        card_selections = card_selections + prefix_length
        prefix_length += len(self._state_rep.get_card_selection())
        leader_rotations = leader_rotations + prefix_length
        prefix_length += len(self._state_rep.get_leader_rotation())
        follower_rotations = follower_rotations + prefix_length

        # [2] Stack the properties into a single tensor. Don't need to reshape it, because Pytorch embedding just
        # looks up an embedding for each index in the entire tensor, regardless of its size.
        stacked_properties = torch.stack((
            card_counts, card_colors, card_shapes, card_selections, leader_rotations, follower_rotations))

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
