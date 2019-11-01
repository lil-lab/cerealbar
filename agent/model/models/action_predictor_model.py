""" Model which predicts the set of cards that should be touched by an agent when following an instruction.

Clases:
    CardPredictorModel (nn.Module): Given an instruction and environment state, predicts which of the possible card
        combinations should be touched by the agent when executing the instruction.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import copy
import torch
from torch import nn

from agent import util
from agent.environment import agent_actions
from agent.environment import util as environment_util
from agent.learning import auxiliary
from agent.learning import batch_util
from agent.learning import plan_metrics
from agent.learning import sampling
from agent.model.models import plan_predictor_model
from agent.model.modules import map_distribution_embedder
from agent.model.modules import word_embedder
from agent.model.utilities import rnn
from agent.simulation import planner

if TYPE_CHECKING:
    from typing import Any, Dict, List, Optional, Tuple

    from agent.config import evaluation_args
    from agent.config import model_args
    from agent.data import instruction_example
    from agent.environment import state_delta
    from agent.simulation import game


class ActionPredictorModel(nn.Module):
    """ Module which predicts an action to take given a distribution over hexes.

    Args:
        args: model_args.ModelArgs. The model arguments used to create this model.
    """

    def __init__(self,
                 args: model_args.ModelArgs,
                 input_vocabulary: List[str],
                 auxiliaries: List[auxiliary.Auxiliary],
                 load_pretrained: bool = True,
                 end_to_end: bool = False):
        super(ActionPredictorModel, self).__init__()
        self._args: model_args.ModelArgs = args
        self._end_to_end = end_to_end

        # If end-to-end, also add in the hex predictor model.
        self._plan_predictor: Optional[plan_predictor_model.PlanPredictorModel] = None
        if self._end_to_end:
            self._plan_predictor: plan_predictor_model.PlanPredictorModel = plan_predictor_model.PlanPredictorModel(
                args, input_vocabulary, auxiliaries)

        self._output_layer = None
        self._rnn = None
        self._action_embedder = None

        if self._args.get_decoder_args().use_recurrence():
            self._action_embedder: word_embedder.WordEmbedder = \
                word_embedder.WordEmbedder(
                    self._args.get_decoder_args().get_action_embedding_size(),
                    [str(action) for action in agent_actions.AGENT_ACTIONS],
                    add_unk=False)

            self._rnn: nn.Module = nn.LSTM(self._args.get_decoder_args().get_state_internal_size()
                                           + self._args.get_decoder_args().get_action_embedding_size(),
                                           self._args.get_decoder_args().get_hidden_size(),
                                           self._args.get_decoder_args().get_num_layers(),
                                           batch_first=True)

            # Add a different output layer
            self._output_layer: nn.Module = nn.Linear(
                self._args.get_decoder_args().get_hidden_size()
                + self._args.get_decoder_args().get_state_internal_size(),
                len(agent_actions.AGENT_ACTIONS))
            torch.nn.init.orthogonal_(self._output_layer.weight, torch.nn.init.calculate_gain("leaky_relu"))
            self._output_layer.bias.data.fill_(0)

        distribution_num_channels: int = 0
        if self._args.get_decoder_args().use_trajectory_distribution():
            distribution_num_channels += 1
        if self._args.get_decoder_args().use_goal_probabilities():
            distribution_num_channels += 1
        if self._args.get_decoder_args().use_obstacle_probabilities():
            distribution_num_channels += 1
        if self._args.get_decoder_args().use_avoid_probabilities():
            distribution_num_channels += 1

        self._map_distribution_embedder: map_distribution_embedder.MapDistributionEmbedder = \
            map_distribution_embedder.MapDistributionEmbedder(
                distribution_num_channels,
                self._args.get_decoder_args().get_state_internal_size(),
                self._args.get_decoder_args().get_state_internal_size()
                if self._args.get_decoder_args().use_recurrence() else len(
                    agent_actions.AGENT_ACTIONS),
                self._args.get_decoder_args().get_crop_size(),
                self._args.get_decoder_args().convolution_encode_map_distributions(),
                self._args.get_decoder_args().use_recurrence())

        if load_pretrained:
            raise ValueError('Not supported yet')
            if self._args.get_decoder_args().pretrained_generator():
                load_pretrained_parameters(self._args.get_decoder_args().pretrained_generator_filepath(),
                                           self._args.get_decoder_args().freeze_pretrained_generator(),
                                           module=self)
            if self._args.get_decoder_args().pretrained_hex_predictor():
                load_pretrained_parameters(self._args.get_decoder_args().pretrained_hex_predictor_filepath(),
                                           self._args.get_decoder_args().freeze_pretrained_hex_predictor(),
                                           module=self._plan_predictor)

    def _encode_and_expand_map_distributions(self,
                                             goal_probabilities: torch.Tensor,
                                             trajectory_distributions: torch.Tensor,
                                             obstacle_probabilities: torch.Tensor,
                                             avoid_probabilities: torch.Tensor,
                                             positions: torch.Tensor,
                                             rotations: torch.Tensor) -> torch.Tensor:
        if goal_probabilities is not None:
            batch_size, _, raw_height, raw_width = goal_probabilities.size()
        else:
            batch_size, _, raw_height, raw_width = trajectory_distributions.size()

        num_actions: int = rotations.size(1)

        # [1] Expand the trajectories
        expanded_trajectory_distribution = None
        if self._args.get_decoder_args().use_trajectory_distribution():
            # Do the same thing as above.
            expanded_trajectory_distribution = \
                trajectory_distributions.unsqueeze(4).expand(
                    (batch_size, 1, raw_height, raw_width, num_actions)).permute(
                    0, 4, 1, 2, 3).contiguous().view(batch_size * num_actions, 1, raw_height, raw_width)

        # Rotate to the current positions.
        map_to_embed = None
        if expanded_trajectory_distribution is not None:
            map_to_embed: torch.Tensor = expanded_trajectory_distribution
        if self._args.get_decoder_args().use_goal_probabilities():
            if map_to_embed is not None:
                map_to_embed = \
                    torch.cat((batch_util.expand_flat_map_distribution(goal_probabilities, num_actions), map_to_embed),
                              dim=1)
            else:
                map_to_embed = batch_util.expand_flat_map_distribution(goal_probabilities, num_actions)
        if self._args.get_decoder_args().use_obstacle_probabilities():
            if map_to_embed is not None:
                map_to_embed = \
                    torch.cat((batch_util.expand_flat_map_distribution(obstacle_probabilities, num_actions),
                               map_to_embed), dim=1)
            else:
                map_to_embed = batch_util.expand_flat_map_distribution(obstacle_probabilities, num_actions)
        if self._args.get_decoder_args().use_avoid_probabilities():
            if map_to_embed is not None:
                map_to_embed = \
                    torch.cat((batch_util.expand_flat_map_distribution(avoid_probabilities, num_actions),
                               map_to_embed), dim=1)
            else:
                map_to_embed = batch_util.expand_flat_map_distribution(avoid_probabilities, num_actions),

        return self._map_distribution_embedder(map_to_embed,
                                               positions.view(batch_size * num_actions, 2),
                                               rotations.view(batch_size * num_actions)).view(batch_size,
                                                                                              num_actions,
                                                                                              -1)

    def _predict_one_action(
            self, action_sequence: List[agent_actions.AgentAction], game_server: game.Game,
            state_distribution: torch.Tensor,
            rnn_state: Optional[Tuple[torch.Tensor,
                                      torch.Tensor]]) -> Tuple[agent_actions.AgentAction,
                                                               Optional[Tuple[torch.Tensor, torch.Tensor]],
                                                               state_delta.StateDelta]:
        # Deal with the state
        follower = game_server.get_game_info().follower
        current_position = follower.get_position()

        # Transform and crop
        embedded_state = \
            self._map_distribution_embedder(
                state_distribution,
                torch.tensor([[float(current_position.x), float(current_position.y)]]).to(util.DEVICE),
                torch.tensor([follower.get_rotation().to_radians()]).to(util.DEVICE))

        new_rnn_state: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
        if self._args.get_decoder_args().use_recurrence():
            rnn_input = \
                self._action_embedder(torch.tensor([self._action_embedder.get_index(str(action_sequence[-1]))],
                                                   dtype=torch.long).to(util.DEVICE))

            rnn_input = torch.cat((rnn_input, embedded_state), dim=1)

            output, new_rnn_state = self._rnn(rnn_input.unsqueeze(1), rnn_state)

            # Predict an action
            action_scores: torch.Tensor = \
                self._output_layer(torch.cat((output.view(1, -1), embedded_state), dim=1))[0]
        else:
            action_scores: torch.Tensor = embedded_state[0]

        predicted_action: agent_actions.AgentAction = sampling.constrained_argmax_sampling(
            nn.functional.softmax(action_scores, dim=0), planner.get_possible_actions(game_server, follower))

        resulting_game_state = game_server.execute_follower_action(predicted_action)

        return predicted_action, new_rnn_state, resulting_game_state

    def _initialize_rnn(self, batch_size: int):
        return (torch.zeros(self._args.get_decoder_args().get_num_layers(),
                            batch_size,
                            self._args.get_decoder_args().get_hidden_size()).to(util.DEVICE),
                torch.zeros(self._args.get_decoder_args().get_num_layers(),
                            batch_size,
                            self._args.get_decoder_args().get_hidden_size()).to(util.DEVICE))

    def _predict_action_sequence(
            self, goal_probabilities: torch.Tensor, trajectory_distribution: torch.Tensor,
            obstacle_probabilities: torch.Tensor, avoid_probabilities: torch.Tensor, game_server: game.Game,
            evaluation_arguments: evaluation_args.EvaluationArgs) -> Tuple[List[agent_actions.AgentAction],
                                                                           List[state_delta.StateDelta]]:
        action_sequence: List[agent_actions.AgentAction] = [agent_actions.AgentAction.START]
        stopped: bool = False
        timestep: int = 0

        rnn_state: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
        if self._args.get_decoder_args().use_recurrence():
            rnn_state = self._initialize_rnn(1)

        resulting_game_state = copy.deepcopy(game_server.get_game_info())
        visited_states: List[state_delta.StateDelta] = [resulting_game_state]

        while (timestep < evaluation_arguments.get_maximum_generation_length() or
               evaluation_arguments.get_maximum_generation_length() < 0) and not stopped:
            # [1] Expand the trajectories
            timestep_map = None
            if self._args.get_decoder_args().use_trajectory_distribution():
                timestep_map: torch.Tensor = trajectory_distribution

            if self._args.get_decoder_args().use_goal_probabilities():
                if timestep_map is not None:
                    timestep_map = torch.cat((goal_probabilities.unsqueeze(0), timestep_map), dim=1)
                else:
                    timestep_map = goal_probabilities.unsqueeze(0)
            if self._args.get_decoder_args().use_obstacle_probabilities():
                if timestep_map is not None:
                    timestep_map = torch.cat((obstacle_probabilities, timestep_map), dim=1)
                else:
                    timestep_map = obstacle_probabilities
            if self._args.get_decoder_args().use_avoid_probabilities():
                if timestep_map is not None:
                    timestep_map = torch.cat((avoid_probabilities, timestep_map), dim=1)
                else:
                    timestep_map = avoid_probabilities

            predicted_action, rnn_state, resulting_game_state = \
                self._predict_one_action(action_sequence,
                                         game_server,
                                         timestep_map.to(util.DEVICE),
                                         rnn_state)
            visited_states.append(resulting_game_state)

            action_sequence.append(predicted_action)
            if predicted_action == agent_actions.AgentAction.STOP or not game_server.valid_state():
                stopped = True

            timestep += 1

        return action_sequence[1:], visited_states

    def save(self, save_file: str) -> None:
        """ Saves the model parameters to a specified location.

        Args:
            save_file: str. The location to save to.
        """
        torch.save(self.state_dict(), save_file)

    def batch_inputs(self, examples: List[instruction_example.InstructionExample]) -> List[torch.Tensor]:
        """ Batches the examples into inputs for the network.

        Arguments:
            examples: List[Example]. The examples to batch.
        """
        # INPUT BATCHING PREPARATION
        instruction_index_tensor = None
        instruction_lengths_tensor = None

        action_lengths_tensor: torch.Tensor = None
        action_index_tensor: torch.Tensor = None

        # [0] Batch the action sequences (if applicable)
        if self._args.get_decoder_args().use_recurrence():
            action_index_tensor, action_lengths_tensor = batch_util.batch_action_sequences(examples,
                                                                                           self._action_embedder)

        # Currently, the distributions should just be one per example.
        if not self._args.get_state_rep_args().full_observability():
            raise ValueError('Partial observability is not supported.')

        # [1] Get the gold distributions
        batched_map_components: List[torch.Tensor] = \
            batch_util.batch_map_distributions(examples,
                                               environment_util.ENVIRONMENT_WIDTH,
                                               environment_util.ENVIRONMENT_DEPTH,
                                               self._args.get_decoder_args().weight_trajectory_by_time())

        # [2] Get the rotations
        positions, rotations = batch_util.batch_agent_configurations(
            examples, max([len(example.get_state_deltas()) for example in examples]) + 1)

        tensors: List[torch.Tensor] = list(batched_map_components[:-1]) + [positions,
                                                                           rotations,
                                                                           action_lengths_tensor,
                                                                           action_index_tensor,
                                                                           instruction_lengths_tensor,
                                                                           instruction_index_tensor]

        # [3] If the model is end to end, also batch the environment information.
        if self._end_to_end:
            # TODO: this is just taking the first state for each example.
            tensors = tensors \
                      + self._plan_predictor.batch_inputs([(example, 0) for example in examples], True) \
                      + [batched_map_components[-1]]

        device_tensors = []
        for tensor in tensors:
            if tensor is not None:
                device_tensors.append(tensor.to(util.DEVICE))
            else:
                device_tensors.append(None)

        return device_tensors

    def forward(self, *args) -> Tuple[torch.Tensor, Dict[auxiliary.Auxiliary, torch.Tensor]]:
        """ Forward pass for the CardPredictorModel.

        B = batch size
        L_in = maximum input sequence length
        V_in = vocabulary size of input
        C_static = number of static channels in the environment
        C_dynamic = number of dynamic states in the environment
        H = height of the environment
        W = width of the environment
        """
        args: List[torch.Tensor] = list(args)

        # First, if training end-to-end, get the predicted distributions
        auxiliary_predictions: Dict[auxiliary.Auxiliary, torch.Tensor] = dict()
        if self._end_to_end:
            # Predict card and trajectory distributions (and any other auxiliaries) using the hex predictor
            card_mask: torch.Tensor = args[-1]

            auxiliary_predictions = self._plan_predictor(*args[11:-1])

            # Card distributions should be put through a sigmoid and masked.
            goal_probabilities = None
            if auxiliary.Auxiliary.FINAL_GOALS in auxiliary_predictions:
                goal_probabilities = torch.sigmoid(auxiliary_predictions[auxiliary.Auxiliary.FINAL_CARDS]) * card_mask

            avoid_probabilities = None
            if auxiliary.Auxiliary.AVOID_LOCS in auxiliary_predictions:
                # Put through a sigmoid and a mask.
                avoid_probabilities = torch.sigmoid(auxiliary_predictions[auxiliary.Auxiliary.AVOID_LOCS]) * card_mask

            # Normalize the trajectory.
            trajectory_distributions = None
            if auxiliary.Auxiliary.TRAJECTORY in auxiliary_predictions:
                trajectory_distributions = plan_metrics.normalize_trajectory_distribution(
                    auxiliary_predictions[auxiliary.Auxiliary.TRAJECTORY])

            obstacle_probabilities = None
            if auxiliary.Auxiliary.IMPASSABLE_LOCS in auxiliary_predictions:
                # Need to put this through a sigmoid.
                obstacle_probabilities = torch.sigmoid(auxiliary_predictions[auxiliary.Auxiliary.OBSTACLES])

        else:
            # Using the gold distributions
            trajectory_distributions: torch.Tensor = args[0]
            goal_probabilities: torch.Tensor = args[1]
            obstacle_probabilities: torch.Tensor = args[2]
            avoid_probabilities: torch.Tensor = args[3]

        embedded_state = self._encode_and_expand_map_distributions(goal_probabilities,
                                                                   trajectory_distributions,
                                                                   obstacle_probabilities,
                                                                   avoid_probabilities,
                                                                   args[4],  # position
                                                                   args[5])  # rotation

        if self._args.get_decoder_args().use_recurrence():
            action_embeddings: torch.Tensor = self._action_embedder(args[7])  # action indices

            # args[7] is action lengths
            rnn_outputs = rnn.fast_run_rnn(args[6], torch.cat((action_embeddings, embedded_state), dim=2), self._rnn)

            return self._output_layer(torch.cat((rnn_outputs, embedded_state), dim=2)), auxiliary_predictions

        # If not using recurrence, these are already the action scores.
        return embedded_state, auxiliary_predictions

    def get_predictions(self,
                        example: instruction_example.InstructionExample,
                        game_server: game.Game,
                        evaluation_arguments: evaluation_args.EvaluationArgs,
                        goal_probabilities: torch.Tensor = None,
                        trajectory_distribution: torch.Tensor = None,
                        time_vector: torch.Tensor = None,
                        obstacle_probabilities: torch.Tensor = None,
                        avoid_probabilities: torch.Tensor = None) -> Tuple[List[agent_actions.AgentAction],
                                                                           Dict[auxiliary.Auxiliary, torch.Tensor],
                                                                           List[state_delta.StateDelta]]:
        """ Gets predictions for a model doing inference (i.e., not gold forcing).

        Arguments:
            example: Example. The example to get outputs for.
            game_server: Game. The game server to use and query during inference.
            evaluation_arguments: EvalArgs. The arguments for evaluation.
            goal_probabilities: torch.Tensor. An optional distribution over cards.
            trajectory_distribution: torch.Tensor. An optional distribution over trajectories.
            time_vector: torch.Tensor. An optional score for each timestep.
            obstacle_probabilities: torch.Tensor. An optional distribution over impassable locations.
            avoid_probabilities: torch.Tensor. An optional distribution over locations to avoid.
        """
        # Not gold forcing.
        if evaluation_arguments is None:
            raise ValueError('Evaluation arguments must be passed if providing a game server.')

        # Get the distribution
        auxiliary_predictions: Dict[auxiliary.Auxiliary, Any] = dict()
        if trajectory_distribution is None:
            if self._end_to_end:
                raise NotImplementedError
                # Outputs of this should be masked if necessary.
                goal_probabilities, auxiliary_predictions = self._hex_predictor.get_predictions(example)

                avoid_probabilities = None
                if auxiliary.Auxiliary.AVOID_LOCS in auxiliary_predictions:
                    # This has already gone through sigmoid (and mask if masked).
                    avoid_probabilities = auxiliary_predictions[auxiliary.Auxiliary.AVOID_LOCS].unsqueeze(1)

                # These need to be normalized -- hex_predictor does not return normalized trajectories.
                trajectory_distribution = None
                if auxiliary.Auxiliary.TRAJECTORY in auxiliary_predictions:
                    trajectory_distribution, time_vector = \
                        normalize_trajectory_distribution(
                            auxiliary_predictions[auxiliary.Auxiliary.TRAJECTORY][0],
                            auxiliary_predictions[auxiliary.Auxiliary.TRAJECTORY][1].unsqueeze(0)
                            if auxiliary_predictions[auxiliary.Auxiliary.TRAJECTORY][1] is not None else None)

                # These are already masked and put through a sigmoid.
                if goal_probabilities is not None:
                    auxiliary_predictions[auxiliary.Auxiliary.FINAL_CARDS] = goal_probabilities.squeeze()

                obstacle_probabilities = None
                if self._args.get_decoder_args().use_impassable_locations():
                    # This is already put through a sigmoid.
                    obstacle_probabilities = auxiliary_predictions[auxiliary.Auxiliary.IMPASSABLE_LOCS].unsqueeze(1)
            else:
                (trajectory_distribution,
                 goal_probabilities,
                 obstacle_probabilities,
                 avoid_probabilities,
                 _) = batch_util.batch_map_distributions([example],
                                                         environment_util.ENVIRONMENT_WIDTH,
                                                         environment_util.ENVIRONMENT_DEPTH,
                                                         self._args.get_decoder_args().weight_trajectory_by_time())
                goal_probabilities = goal_probabilities[0]

        if evaluation_arguments.visualize_auxiliaries():
            if not isinstance(game_server, unity_game.UnityGame):
                raise ValueError('Can only visualize auxiliaries with a Unity game.')

            hex_inference.visualize_probabilities(goal_probabilities.numpy()[0], trajectory_distribution.numpy()[0][0],
                                                  obstacle_probabilities.numpy()[0][0],
                                                  avoid_probabilities.numpy()[0][0], game_server)

        action_sequence, visited_states = self._predict_action_sequence(goal_probabilities,
                                                                        trajectory_distribution,
                                                                        obstacle_probabilities,
                                                                        avoid_probabilities,
                                                                        game_server,
                                                                        evaluation_arguments)

        return action_sequence, auxiliary_predictions, visited_states
