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
    from typing import List
    from agent.model.modules import state_representation


class DynamicEnvironmentEmbedder(nn.Module):
    """ Dynamic environment embedder.

    Args:
        state_rep: DenseStateRepresentation. Formal representation of the environment properties.
        embedding_size: int. The size of each underlying embedding.
        zero_out: bool. Whether or not to zero-out embeddings which represent absence of a property.
        concat: bool. Whether or not to combine the various property embeddings by concatenation.
            If False, will be combined via channelwise summation.
    """

    def __init__(self,
                 state_rep: state_representation.StateRepresentation,
                 embedding_size: int,
                 zero_out: bool = True):
        super(DynamicEnvironmentEmbedder, self).__init__()

        self._card_count_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(embedding_size,
                                                                                           state_rep.get_card_counts(),
                                                                                           add_unk=False,
                                                                                           zero_out=zero_out)
        self._card_color_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(embedding_size,
                                                                                           state_rep.get_card_colors(),
                                                                                           add_unk=False,
                                                                                           zero_out=zero_out)
        self._card_shape_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(embedding_size,
                                                                                           state_rep.get_card_shapes(),
                                                                                           add_unk=False,
                                                                                           zero_out=zero_out)
        self._card_selection_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(
            embedding_size, state_rep.get_card_selection(), add_unk=False, zero_out=zero_out)
        self._leader_rotation_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(
            embedding_size, state_rep.get_leader_rotation(), add_unk=False, zero_out=zero_out)
        self._follower_rotation_embedder: word_embedder.WordEmbedder = word_embedder.WordEmbedder(
            embedding_size, state_rep.get_follower_rotation(), add_unk=False, zero_out=zero_out)

        self._embedders: List[word_embedder.WordEmbedder] = [self._card_count_embedder,
                                                             self._card_color_embedder,
                                                             self._card_shape_embedder,
                                                             self._card_selection_embedder,
                                                             self._leader_rotation_embedder,
                                                             self._follower_rotation_embedder]

    def embedding_size(self) -> int:
        """ Returns the size of embeddings resulting from calling the forward method. """
        return self._embedders[0].embedding_size()

    def forward(self,
                card_counts: torch.Tensor,
                card_colors: torch.Tensor,
                card_shapes: torch.Tensor,
                card_selections: torch.Tensor,
                leader_rotations: torch.Tensor,
                follower_rotations: torch.Tensor) -> torch.Tensor:
        batch_size = card_counts.size(0)

        # First, embed the properties independently
        emb_card_counts: torch.Tensor = \
            batch_util.bhwc_to_bchw(self._card_count_embedder(
                card_counts.view(batch_size, -1)).view(batch_size,
                                                       environment_util.ENVIRONMENT_WIDTH,
                                                       environment_util.ENVIRONMENT_DEPTH,
                                                       self._card_count_embedder.embedding_size()))
        emb_card_colors: torch.Tensor = \
            batch_util.bhwc_to_bchw(self._card_color_embedder(
                card_colors.view(batch_size, -1)).view(batch_size,
                                                       environment_util.ENVIRONMENT_WIDTH,
                                                       environment_util.ENVIRONMENT_DEPTH,
                                                       self._card_color_embedder.embedding_size()))
        emb_card_shapes: torch.Tensor = \
            batch_util.bhwc_to_bchw(self._card_shape_embedder(
                card_shapes.view(batch_size, -1)).view(batch_size,
                                                       environment_util.ENVIRONMENT_WIDTH,
                                                       environment_util.ENVIRONMENT_DEPTH,
                                                       self._card_shape_embedder.embedding_size()))
        emb_card_selections: torch.Tensor = \
            batch_util.bhwc_to_bchw(self._card_selection_embedder(
                card_selections.view(batch_size, -1)).view(batch_size,
                                                           environment_util.ENVIRONMENT_WIDTH,
                                                           environment_util.ENVIRONMENT_DEPTH,
                                                           self._card_selection_embedder.embedding_size()))
        emb_leader_rotations: torch.Tensor = \
            batch_util.bhwc_to_bchw(self._leader_rotation_embedder(
                leader_rotations.view(batch_size, -1)).view(batch_size,
                                                            environment_util.ENVIRONMENT_WIDTH,
                                                            environment_util.ENVIRONMENT_DEPTH,
                                                            self._leader_rotation_embedder.embedding_size()))
        emb_follower_rotations: torch.Tensor = \
            batch_util.bhwc_to_bchw(self._follower_rotation_embedder(
                follower_rotations.view(batch_size, -1)).view(batch_size,
                                                              environment_util.ENVIRONMENT_WIDTH,
                                                              environment_util.ENVIRONMENT_DEPTH,
                                                              self._follower_rotation_embedder.embedding_size()))

        # Each embedding will be B x C x H x W, where C is the embedding size.
        # Stacking them gets a tensors of size N x B x C x H x W, where N is the number of embeddings.
        stacked_tensors = torch.stack((emb_card_counts,
                                       emb_card_colors,
                                       emb_card_shapes,
                                       emb_card_selections,
                                       emb_leader_rotations,
                                       emb_follower_rotations))
        # Permute so it has size B x N x C x H x W
        permuted_tensor = stacked_tensors.permute(1, 0, 2, 3, 4)

        # Then sum across that dimension
        emb_state = torch.sum(permuted_tensor, dim=1)

        return emb_state
