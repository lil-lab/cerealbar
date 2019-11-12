""" Model which predicts the set of cards that should be touched by an agent when following an instruction.

Clases:
    CardPredictorModel (nn.Module): Given an instruction and environment state, predicts which of the possible card
        combinations should be touched by the agent when executing the instruction.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import torch
import torch.nn as nn

from agent import util
from agent.environment import agent
from agent.environment import position
from agent.environment import state_delta
from agent.environment import util as environment_util
from agent.learning import auxiliary
from agent.learning import batch_util
from agent.model.map_transformations import map_transformer
from agent.model.map_transformations import pose
from agent.model.modules import dynamic_environment_embedder
from agent.model.modules import lingunet
from agent.model.modules import state_representation
from agent.model.modules import static_environment_embedder
from agent.model.modules import text_encoder
from agent.model.modules import word_embedder

if TYPE_CHECKING:
    from agent.config import model_args
    from agent.config import state_representation_args
    from agent.data import instruction_example
    from agent.data import partial_observation
    from typing import Any, List, Dict, Optional, Tuple


class PlanPredictorModel(nn.Module):
    """ Module which predicts either an independent distribution per hex, or a joint distribution over a game board.

    Args:
        args: model_args.ModelArgs. The model arguments used to create this model.
        input_vocabulary: List[str]. The list of word types to expect in instructions.
    """

    def __init__(self,
                 args: model_args.ModelArgs,
                 input_vocabulary: List[str],
                 auxiliaries: List[auxiliary.Auxiliary]):
        super(PlanPredictorModel, self).__init__()

        # first, it embeds the representation
        self._args: model_args.ModelArgs = args
        self._env_feature_channels: int = 0
        self._auxiliaries: List[auxiliary.Auxiliary] = auxiliaries

        state_rep_args: state_representation_args.StateRepresentationArgs = self._args.get_state_rep_args()

        self._state_rep: state_representation.StateRepresentation = state_representation.StateRepresentation(
            state_rep_args)

        self._static_embedder: static_environment_embedder.StaticEnvironmentEmbedder = \
            static_environment_embedder.StaticEnvironmentEmbedder(self._state_rep,
                                                                  state_rep_args.get_property_embedding_size(),
                                                                  not state_rep_args.learn_absence_embeddings())

        self._dynamic_embedder: dynamic_environment_embedder.DynamicEnvironmentEmbedder = \
            dynamic_environment_embedder.DynamicEnvironmentEmbedder(
                self._state_rep,
                state_rep_args.get_property_embedding_size(),
                not state_rep_args.learn_absence_embeddings())

        self._env_feature_channels = self._static_embedder.embedding_size()

        # Instruction encoder.
        self._instruction_encoder: text_encoder.TextEncoder = text_encoder.TextEncoder(
            self._args.get_text_encoder_args(), input_vocabulary)
        text_feature_size = self._args.get_text_encoder_args().get_hidden_size()

        # Lingunet predicts on top of this.

        # Apply a 1x1 convolution on top of the semantic map taking into account the instruction.
        # The grounding map has the same number of channels.

        # TODO: No magic numbers
        self._grounding_map_channels = 4

        self._initial_text_kernel_ll = nn.Linear(text_feature_size,
                                                 (self._env_feature_channels * self._grounding_map_channels))

        # Add intermediate card visitation predictors if computing intermediate card visitation loss.
        self._intermediate_goal_ll: Optional[nn.Module] = None
        if auxiliary.Auxiliary.INTERMEDIATE_GOALS in auxiliaries:
            self._intermediate_goal_ll = nn.Linear(self._grounding_map_channels, 1, bias=False)

        self._into_lingunet_transformer: map_transformer.MapTransformer = map_transformer.MapTransformer(
            source_map_size=environment_util.ENVIRONMENT_WIDTH,
            dest_map_size=environment_util.PADDED_WIDTH,
            world_size_px=environment_util.ENVIRONMENT_WIDTH,
            world_size_m=environment_util.ENVIRONMENT_WIDTH)
        self._after_lingunet_transformer: map_transformer.MapTransformer = map_transformer.MapTransformer(
            source_map_size=environment_util.PADDED_WIDTH,
            dest_map_size=environment_util.ENVIRONMENT_WIDTH,
            world_size_px=environment_util.PADDED_WIDTH,
            world_size_m=environment_util.PADDED_WIDTH)
        if torch.cuda.device_count() >= 1:
            self._into_lingunet_transformer = self._into_lingunet_transformer.cuda(device=util.DEVICE)
            self._after_lingunet_transformer = self._after_lingunet_transformer.cuda(device=util.DEVICE)

        # Predict two output channels if computing a trajectory distribution auxiliary loss.
        lingunet_out_channels: int = 0
        extra_head_channels: int = 0
        if auxiliary.Auxiliary.FINAL_GOALS in auxiliaries:
            lingunet_out_channels += 1
        if auxiliary.Auxiliary.TRAJECTORY in auxiliaries:
            lingunet_out_channels += 1
        if auxiliary.Auxiliary.AVOID_LOCS in auxiliaries:
            lingunet_out_channels += 1
        if auxiliary.Auxiliary.OBSTACLES in auxiliaries:
            lingunet_out_channels += 1

        self._lingunet = lingunet.LingUNet(
            self._args.get_state_encoder_args(),
            self._env_feature_channels + self._grounding_map_channels,
            text_feature_size,
            lingunet_out_channels,
            self._args.get_dropout(),
            extra_head_channels=extra_head_channels,
            input_img_size=environment_util.PADDED_WIDTH,
            layer_single_preds=auxiliary.Auxiliary.IMPLICIT in self._auxiliaries)

    def _embed_environment(self, *args) -> torch.Tensor:
        list_args: List[torch.Tensor] = list(args)

        dynamic_args: List[torch.Tensor] = list_args[0:6]
        static_args: List[torch.Tensor] = list_args[6:-1]
        state_mask: torch.Tensor = list_args[-1]

        emb_delta: torch.Tensor = self._dynamic_embedder(*dynamic_args)
        emb_static: torch.Tensor = self._static_embedder(*static_args)

        embedded_environment: torch.Tensor = torch.sum(torch.stack((emb_delta, emb_static)), dim=0)

        masked_environment = embedded_environment * state_mask

        return masked_environment

    def get_instruction_embedder(self) -> word_embedder.WordEmbedder:
        return self._instruction_encoder.get_word_embedder()

    def batch_inputs(self,
                     examples: List[Tuple[instruction_example.InstructionExample,
                                          partial_observation.PartialObservation]],
                     put_on_device: bool = False) -> List[torch.Tensor]:
        """ Batches inputs for the hex predictor model into a list of tensors.

        Arguments:
            examples: List[instruction_example.InstructionExample]. The examples to batch.
            put_on_device: bool. Whether to put the batched tensors on a device.

        Returns:
            List[torch.Tensor], representing an ordered list of batched inputs to the network.
        """
        # INPUT BATCHING PREPARATION
        instruction_index_tensor, instruction_lengths_tensor = batch_util.batch_instructions(
            [example[0] for example in examples], self.get_instruction_embedder())

        # Use indices to represent properties of the environment
        if self._state_rep.get_args().full_observability():
            delta_tensors = self._state_rep.batch_state_delta_indices(
                [example.get_state_deltas()[i] for example, i in examples])
            static_tensors = self._state_rep.batch_static_indices([example[0] for example in examples])
            state_tensors = delta_tensors + static_tensors

            # The mask is 1 -- no hexes are unknown.
            state_mask = torch.ones(state_tensors[0].size(), dtype=torch.float32).unsqueeze(1)
        else:
            state_tensors, state_mask = self._state_rep.batch_partially_observable_indices(examples)

        # These are initial rotations and positions because LingUNet is always rotated to the initial position
        # of the agent so that the instruction makes sense.
        # TODO: With partial observability, should it transform/rotate wrt. current orientation, or stay according to
        #  the initial orientation?
        initial_positions: List[torch.Tensor] = []
        initial_rotations: List[torch.Tensor] = []

        for example, _ in examples:
            initial_state: state_delta.StateDelta = example.get_initial_state()
            initial_follower: agent.Agent = initial_state.follower
            initial_position: position.Position = initial_follower.get_position()
            initial_positions.append(torch.tensor([float(initial_position.x), float(initial_position.y)]))
            initial_rotations.append(torch.tensor(initial_follower.get_rotation().to_radians()))

        # B x 2
        initial_position_tensor: torch.Tensor = torch.stack(tuple(initial_positions))
        # B
        initial_rotation_tensor: torch.Tensor = torch.stack(tuple(initial_rotations))

        tensors: List[torch.Tensor] = [instruction_index_tensor,
                                       instruction_lengths_tensor,
                                       initial_position_tensor,
                                       initial_rotation_tensor] + state_tensors + [state_mask]

        if put_on_device:
            cuda_inputs: List[Optional[torch.Tensor]] = list()
            for tensor in tensors:
                if tensor is not None:
                    cuda_inputs.append(tensor.to(util.DEVICE))
                else:
                    cuda_inputs.append(tensor)
            tensors = cuda_inputs

        return tensors

    def load(self, save_file: str) -> None:
        """ Loads the model parameters from a file.

        Arguments:
            save_file: str. The filename to read from.
        """
        self.load_state_dict(torch.load(save_file, map_location=util.DEVICE))

    def save(self, save_file: str) -> None:
        """ Saves the model parameters to a specified location.

        Arguments:
            save_file: str. The location to save to.
        """
        torch.save(self.state_dict(), save_file)

    def forward(self, *args) -> Dict[auxiliary.Auxiliary, Any]:
        """ Forward pass for the CardPredictorModel.

        B = batch size
        L_in = maximum input sequence length
        V_in = vocabulary size of input
        C_static = number of static channels in the environment
        C_dynamic = number of dynamic states in the environment
        H = height of the environment
        W = width of the environment
        """
        list_args: List[torch.Tensor] = list(args)

        # TODO: Magic numbers
        batched_instructions: torch.Tensor = list_args[0]
        batched_instruction_lengths: torch.Tensor = list_args[1]
        current_positions: torch.Tensor = list_args[2]
        current_rotations: torch.Tensor = list_args[3]

        batch_size: int = batched_instructions.size(0)

        auxiliary_dict: Dict[auxiliary.Auxiliary, Any] = dict()

        embedded_environment = self._embed_environment(*list_args[4:])

        encoded_instructions: torch.Tensor = self._instruction_encoder(batched_instructions,
                                                                       batched_instruction_lengths)
        # Get a single representation
        instruction_rep: torch.Tensor = \
            encoded_instructions[torch.arange(encoded_instructions.size(0)), batched_instruction_lengths - 1, :]

        # Do the lingunet.LingUNet prediction
        text_kernel_shape = (batch_size, self._grounding_map_channels, self._env_feature_channels, 1, 1)
        text_kernels = self._initial_text_kernel_ll(instruction_rep).view(text_kernel_shape)
        initial_text_outputs: List[torch.Tensor] = []
        for emb_env, text_kernel in zip(embedded_environment, text_kernels):
            initial_text_outputs.append(nn.functional.conv2d(emb_env.unsqueeze(0), text_kernel))
        initial_text_outputs: torch.Tensor = torch.cat(tuple(initial_text_outputs), dim=0)

        # Predict the intermediate cards if this is one of the auxiliaries.
        if auxiliary.Auxiliary.INTERMEDIATE_GOALS in self._auxiliaries:
            initial_text_outputs = initial_text_outputs.permute(0, 2, 3, 1).contiguous()
            flattened_text_outputs = initial_text_outputs.view(
                batch_size * environment_util.ENVIRONMENT_WIDTH * environment_util.ENVIRONMENT_DEPTH, -1)
            auxiliary_dict[auxiliary.Auxiliary.INTERMEDIATE_GOALS] = self._intermediate_goal_ll(
                flattened_text_outputs).view(
                batch_size, environment_util.ENVIRONMENT_WIDTH, environment_util.ENVIRONMENT_DEPTH)
            initial_text_outputs = initial_text_outputs.permute(0, 3, 1, 2)

        concat_states = torch.cat((embedded_environment, initial_text_outputs), dim=1)

        # Transform it the first time
        transformed_state = self._into_lingunet_transformer(concat_states,
                                                            None,
                                                            pose.Pose(current_positions, current_rotations))[0]
        # Then apply lingunet
        lingunet_map_preds, lingunet_time_preds, single_layer_preds = self._lingunet(transformed_state, instruction_rep)

        # Then transform it back
        retransformed_state = self._after_lingunet_transformer(lingunet_map_preds,
                                                               pose.Pose(current_positions, current_rotations),
                                                               None)[0]

        # Separate the transformed state into channels if computing the trajectory distribution
        channel_idx = 0
        if auxiliary.Auxiliary.FINAL_GOALS in self._auxiliaries:
            auxiliary_dict[auxiliary.Auxiliary.FINAL_GOALS] = retransformed_state[:, channel_idx, :, :].unsqueeze(1)
            channel_idx += 1

        if auxiliary.Auxiliary.IMPLICIT in self._auxiliaries:
            auxiliary_dict[auxiliary.Auxiliary.IMPLICIT] = single_layer_preds

        if auxiliary.Auxiliary.TRAJECTORY in self._auxiliaries:
            auxiliary_dict[auxiliary.Auxiliary.TRAJECTORY] = (
                retransformed_state[:, channel_idx:channel_idx + 1, :, :],
                lingunet_time_preds)
            channel_idx += 1
        if auxiliary.Auxiliary.OBSTACLES in self._auxiliaries:
            auxiliary_dict[auxiliary.Auxiliary.OBSTACLES] = \
                retransformed_state[:, channel_idx:channel_idx + 1, :, :]
            channel_idx += 1
        if auxiliary.Auxiliary.AVOID_LOCS in self._auxiliaries:
            auxiliary_dict[auxiliary.Auxiliary.AVOID_LOCS] = retransformed_state[:, channel_idx:channel_idx + 1, :, :]

        return auxiliary_dict

    def get_predictions(self,
                        example: instruction_example.InstructionExample,
                        observation: partial_observation.PartialObservation = None) -> Dict[auxiliary.Auxiliary, Any]:
        """ Gets the predictions of the model for an example.

        Arguments:
            example: instruction_example.InstructionExample. The example to predict for.
            observation: partial_observation.PartialObsevation. The observation to predict for (may be None).
        """
        batched_inputs = self.batch_inputs([(example, observation)])

        if torch.cuda.device_count() >= 1:
            cuda_inputs = []
            for i in batched_inputs:
                if i is not None:
                    cuda_inputs.append(i.to(util.DEVICE))
                else:
                    cuda_inputs.append(i)
            batched_inputs = cuda_inputs

        auxiliary_scores = self(*batched_inputs)

        auxiliary_predictions: Dict[auxiliary.Auxiliary, Any] = dict()

        card_mask = torch.zeros((environment_util.ENVIRONMENT_WIDTH, environment_util.ENVIRONMENT_DEPTH),
                                device=util.DEVICE)

        if observation:
            for card in observation.get_card_beliefs():
                card_mask[card.get_position().x][card.get_position().y] = 1.
        else:
            for card in example.get_initial_cards():
                card_mask[card.get_position().x][card.get_position().y] = 1.

        if auxiliary.Auxiliary.INTERMEDIATE_GOALS in self._auxiliaries:
            # Also mask these.
            auxiliary_predictions[auxiliary.Auxiliary.INTERMEDIATE_GOALS] = \
                torch.sigmoid(auxiliary_scores[auxiliary.Auxiliary.INTERMEDIATE_GOALS][0]) * card_mask

        if auxiliary.Auxiliary.FINAL_GOALS in self._auxiliaries:
            # Also mask these.
            auxiliary_predictions[auxiliary.Auxiliary.FINAL_GOALS] = \
                torch.sigmoid(auxiliary_scores[auxiliary.Auxiliary.FINAL_GOALS][0]) * card_mask

        if auxiliary.Auxiliary.TRAJECTORY in self._auxiliaries:
            auxiliary_predictions[auxiliary.Auxiliary.TRAJECTORY] = \
                (auxiliary_scores[auxiliary.Auxiliary.TRAJECTORY][0])

        if auxiliary.Auxiliary.OBSTACLES in self._auxiliaries:
            # Not masked, because all hexes could be impassable, but put through a sigmoid.
            auxiliary_predictions[auxiliary.Auxiliary.OBSTACLES] = \
                torch.sigmoid(auxiliary_scores[auxiliary.Auxiliary.OBSTACLES][0])

        if auxiliary.Auxiliary.AVOID_LOCS in self._auxiliaries:
            # Masked (for now, restricting to cards only), and put through a sigmoid.
            auxiliary_predictions[auxiliary.Auxiliary.AVOID_LOCS] = (
                    torch.sigmoid(auxiliary_scores[auxiliary.Auxiliary.AVOID_LOCS][0]) * card_mask)

        if auxiliary.Auxiliary.IMPLICIT in self._auxiliaries:
            auxiliary_predictions[auxiliary.Auxiliary.IMPLICIT] = (
                torch.sigmoid(auxiliary_scores[auxiliary.Auxiliary.IMPLICIT][0]))

        return auxiliary_predictions
