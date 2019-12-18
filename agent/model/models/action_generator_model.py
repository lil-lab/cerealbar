""" Model which predicts the set of cards that should be touched by an agent when following an instruction.

Clases:
    CardPredictorModel (nn.Module): Given an instruction and environment state, predicts which of the possible card
        combinations should be touched by the agent when executing the instruction.
"""
from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING

import numpy as np
import torch
from torch import nn

from agent import util
from agent.data import partial_observation
from agent.environment import agent_actions
from agent.environment import util as environment_util
from agent.evaluation import distribution_visualizer
from agent.evaluation import plan_metrics
from agent.learning import auxiliary
from agent.learning import batch_util
from agent.learning import plan_losses
from agent.learning import sampling
from agent.model.models import plan_predictor_model
from agent.model.modules import map_distribution_embedder
from agent.model.modules import word_embedder
from agent.model.utilities import initialization
from agent.model.utilities import rnn
from agent.simulation import planner
from agent.simulation import unity_game

if TYPE_CHECKING:
    from typing import Any, Dict, List, Optional, Tuple

    from agent.config import evaluation_args
    from agent.config import model_args
    from agent.data import instruction_example
    from agent.evaluation import evaluation_logger
    from agent.environment import state_delta
    from agent.simulation import game


class ActionGeneratorModel(nn.Module):
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
        super(ActionGeneratorModel, self).__init__()
        self._args: model_args.ModelArgs = args
        self._end_to_end = end_to_end

        # If end-to-end, also add in the hex predictor model.
        self._plan_predictor: Optional[plan_predictor_model.PlanPredictorModel] = None
        if self._end_to_end or load_pretrained:
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
            if self._args.get_decoder_args().pretrained_generator():
                initialization.load_pretrained_parameters(
                    self._args.get_decoder_args().pretrained_action_generator_filepath(),
                    module=self)
            if self._args.get_decoder_args().pretrained_plan_predictor():
                initialization.load_pretrained_parameters(
                    self._args.get_decoder_args().pretrained_plan_predictor_filepath(),
                    module=self._plan_predictor)

    def load_pretrained_plan_predictor(self, filepath: str, vocabulary: List[str],
                                       auxiliaries: List[auxiliary.Auxiliary]):
        assert not self._plan_predictor
        logging.info('Loading pretrained plan predictor: ' + filepath + ' with auxiliaries: %r' % auxiliaries)
        self._plan_predictor: plan_predictor_model.PlanPredictorModel = plan_predictor_model.PlanPredictorModel(
            self._args, vocabulary, auxiliaries)
        initialization.load_pretrained_parameters(filepath, module=self._plan_predictor)

    def _encode_and_expand_map_distributions(self,
                                             goal_probabilities: torch.Tensor,
                                             trajectory_distributions: torch.Tensor,
                                             obstacle_probabilities: torch.Tensor,
                                             avoid_probabilities: torch.Tensor,
                                             positions: torch.Tensor,
                                             rotations: torch.Tensor) -> torch.Tensor:
        if self._args.get_state_rep_args().full_observability():
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
                        torch.cat(
                            (batch_util.expand_flat_map_distribution(goal_probabilities, num_actions), map_to_embed),
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
        else:
            if goal_probabilities is not None:
                batch_size, num_actions, raw_height, raw_width = goal_probabilities.size()
            else:
                batch_size, num_actions, raw_height, raw_width = trajectory_distributions.size()

            # Reshape to be the expanded size.
            def reshape_to_flat(x):
                return x.view((batch_size * num_actions, 1, raw_height, raw_width))

            map_to_embed = None
            if trajectory_distributions is not None:
                map_to_embed = reshape_to_flat(trajectory_distributions)
            if goal_probabilities is not None:
                if map_to_embed is not None:
                    map_to_embed = torch.cat((reshape_to_flat(goal_probabilities), map_to_embed), dim=1)
                else:
                    map_to_embed = reshape_to_flat(goal_probabilities)
            if obstacle_probabilities is not None:
                if map_to_embed is not None:
                    map_to_embed = torch.cat((reshape_to_flat(obstacle_probabilities), map_to_embed), dim=1)
                else:
                    map_to_embed = reshape_to_flat(obstacle_probabilities)
            if avoid_probabilities is not None:
                if map_to_embed is not None:
                    map_to_embed = torch.cat((reshape_to_flat(avoid_probabilities), map_to_embed), dim=1)
                else:
                    map_to_embed = reshape_to_flat(avoid_probabilities)

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

    def _combine_distributions(self,
                               goal_probabilities: torch.Tensor,
                               trajectory_distribution: torch.Tensor,
                               obstacle_probabilities: torch.Tensor,
                               avoid_probabilities: torch.Tensor) -> torch.Tensor:
        # Assumes there is no batch size dimension.
        timestep_map = None
        if self._args.get_decoder_args().use_trajectory_distribution():
            timestep_map: torch.Tensor = trajectory_distribution.unsqueeze(0).unsqueeze(0)

        if self._args.get_decoder_args().use_goal_probabilities():
            if timestep_map is not None:
                timestep_map = torch.cat((goal_probabilities.unsqueeze(0).unsqueeze(0), timestep_map), dim=1)
            else:
                timestep_map = goal_probabilities.unsqueeze(0).unsqueeze(0)
        if self._args.get_decoder_args().use_obstacle_probabilities():
            if timestep_map is not None:
                timestep_map = torch.cat((obstacle_probabilities.unsqueeze(0).unsqueeze(0), timestep_map), dim=1)
            else:
                timestep_map = obstacle_probabilities.unsqueeze(0).unsqueeze(0)
        if self._args.get_decoder_args().use_avoid_probabilities():
            if timestep_map is not None:
                timestep_map = torch.cat((avoid_probabilities.unsqueeze(0).unsqueeze(0), timestep_map), dim=1)
            else:
                timestep_map = avoid_probabilities.unsqueeze(0).unsqueeze(0)
        return timestep_map

    def _predict_actions_full_observability(
            self, goal_probabilities: torch.Tensor, trajectory_distribution: torch.Tensor,
            obstacle_probabilities: torch.Tensor, avoid_probabilities: torch.Tensor, game_server: game.Game,
            evaluation_arguments: evaluation_args.EvaluationArgs) -> Tuple[List[agent_actions.AgentAction],
                                                                           List[state_delta.StateDelta]]:

        if evaluation_arguments.visualize_auxiliaries():
            raise NotImplementedError

        action_sequence: List[agent_actions.AgentAction] = [agent_actions.AgentAction.START]
        stopped: bool = False
        timestep: int = 0

        rnn_state: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
        if self._args.get_decoder_args().use_recurrence():
            rnn_state = self._initialize_rnn(1)

        resulting_game_state = copy.deepcopy(game_server.get_game_info())
        visited_states: List[state_delta.StateDelta] = [resulting_game_state]

        # [1] Combine the map distributions only once.
        timestep_map = self._combine_distributions(goal_probabilities, trajectory_distribution,
                                                   obstacle_probabilities, avoid_probabilities)

        while (timestep < evaluation_arguments.get_maximum_generation_length() or
               evaluation_arguments.get_maximum_generation_length() < 0) and not stopped:

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

    def _predict_actions_partial_observability(
            self, example: instruction_example.InstructionExample, game_server: game.Game,
            evaluation_arguments: evaluation_args.EvaluationArgs,
            logger: evaluation_logger.EvaluationLogger) -> Tuple[List[agent_actions.AgentAction],
                                                                 List[state_delta.StateDelta],
                                                                 partial_observation.PartialObservation]:
        if self._end_to_end and not self._plan_predictor:
            raise ValueError('Action predictor must have a plan predictor if evaluating end-to-end.')

        action_sequence: List[agent_actions.AgentAction] = [agent_actions.AgentAction.START]
        stopped: bool = False
        timestep: int = 0

        rnn_state: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
        if self._args.get_decoder_args().use_recurrence():
            rnn_state = self._initialize_rnn(1)

        resulting_game_state = copy.deepcopy(game_server.get_game_info())
        visited_states: List[state_delta.StateDelta] = [resulting_game_state]
        current_observation: partial_observation.PartialObservation = example.get_first_partial_observation()

        while (timestep < evaluation_arguments.get_maximum_generation_length() or
               evaluation_arguments.get_maximum_generation_length() < 0) and not stopped:

            visible_cards = current_observation.get_card_beliefs()
            all_card_positions = sorted(list(set([visible_card.get_position() for visible_card in visible_cards])))
            if logger.active():
                logger.log('-- #%r at position %r and rotation %r' % (
                    timestep, current_observation.get_follower().get_position(),
                    current_observation.get_follower().get_rotation()))

                logger.log('Goal cards:')
                for goal_card in example.get_touched_cards():
                    visibility: str = 'Not visible!' if goal_card.get_position() not in all_card_positions else ''
                    logger.log('\t' + str(goal_card) + '\t' + visibility)

            # Compute the updated timestep map given the most recent partial observation.
            if self._plan_predictor:
                # Call the plan predictor.
                predictions = self._plan_predictor.get_predictions(example, current_observation)

                avoid_probabilities = None
                if auxiliary.Auxiliary.AVOID_LOCS in predictions:
                    avoid_probabilities = predictions[auxiliary.Auxiliary.AVOID_LOCS].squeeze()

                goal_probabilities = None
                if auxiliary.Auxiliary.FINAL_GOALS in predictions:
                    goal_probabilities = predictions[auxiliary.Auxiliary.FINAL_GOALS].squeeze()

                    if logger.active():
                        logger.log('Card predictions:')
                        predicted_positions = sorted(list(set(plan_metrics.get_hexes_above_threshold(
                            goal_probabilities, all_card_positions))))

                        for visible_card in visible_cards:
                            if visible_card.get_position() in predicted_positions:
                                logger.log('\t' + str(visible_card))
                        logger.log('')

                obstacle_probabilities = None
                if auxiliary.Auxiliary.OBSTACLES in predictions:
                    obstacle_probabilities = predictions[auxiliary.Auxiliary.OBSTACLES].squeeze()

                trajectory_distribution = None
                if auxiliary.Auxiliary.TRAJECTORY in predictions:
                    trajectory_distribution = plan_metrics.normalize_trajectory_distribution(
                        predictions[auxiliary.Auxiliary.TRAJECTORY]).squeeze()

                if logger.active():
                    for believed_card in current_observation.get_card_beliefs():
                        card_position = believed_card.get_position()
                        logger.log(str(believed_card) + '\t' + '{0:.2f}'.format(100. * goal_probabilities[
                            card_position.x][card_position.y]) + '\t' + '{0:.2f}'.format(
                            100. * avoid_probabilities[card_position.x][card_position.y]))

            else:

                # Note: when training with gold distribution inputs, if the agent gets off the path,
                # the old path distribution isn't useful whereas when training end-to-end it should be updated wrt. the
                # agent's current path distribution.
                trajectory_distribution = torch.tensor(example.get_correct_trajectory_distribution(
                    self._args.get_decoder_args().weight_trajectory_by_time(),
                    full_observability=False,
                    observed_positions=current_observation.currently_observed_positions())).float()

                goal_probabilities = torch.zeros(environment_util.ENVIRONMENT_WIDTH, environment_util.ENVIRONMENT_DEPTH)
                avoid_probabilities = torch.zeros(environment_util.ENVIRONMENT_WIDTH,
                                                  environment_util.ENVIRONMENT_DEPTH)
                target_cards = example.get_touched_cards()
                for believed_card in current_observation.get_card_beliefs():
                    card_position = believed_card.get_position()
                    if believed_card in target_cards:
                        goal_probabilities[card_position.x][card_position.y] = 1.
                    elif card_position != example.get_initial_state().follower.get_position():
                        avoid_probabilities[card_position.x][card_position.y] = 1.

                # Obstacle probabilities
                obstacle_probabilities = np.zeros(
                    (environment_util.ENVIRONMENT_WIDTH, environment_util.ENVIRONMENT_DEPTH))
                for pos in sorted(example.get_obstacle_positions()):
                    assert pos not in example.get_visited_positions()
                    obstacle_probabilities[pos.x][pos.y] = 1.
                state_mask = np.zeros((environment_util.ENVIRONMENT_WIDTH, environment_util.ENVIRONMENT_DEPTH))
                for viewed_position in current_observation.lifetime_observed_positions():
                    state_mask[viewed_position.x][viewed_position.y] = 1.
                obstacle_probabilities = torch.tensor(obstacle_probabilities * state_mask).float()

            if evaluation_arguments.visualize_auxiliaries():
                # Send the auxiliaries
                assert isinstance(game_server, unity_game.UnityGame)
                distribution_visualizer.visualize_probabilities(goal_probabilities.numpy(),
                                                                trajectory_distribution.numpy(),
                                                                obstacle_probabilities.numpy(),
                                                                avoid_probabilities.numpy(),
                                                                game_server)

            timestep_map = self._combine_distributions(goal_probabilities, trajectory_distribution,
                                                       obstacle_probabilities,
                                                       avoid_probabilities)

            predicted_action, rnn_state, resulting_game_state = \
                self._predict_one_action(action_sequence,
                                         game_server,
                                         timestep_map.to(util.DEVICE),
                                         rnn_state)
            logger.log('Predicted action: %r' % predicted_action)
            visited_states.append(resulting_game_state)

            current_observation = partial_observation.update_observation(current_observation, resulting_game_state)

            action_sequence.append(predicted_action)
            if predicted_action == agent_actions.AgentAction.STOP or not game_server.valid_state():
                stopped = True

            timestep += 1

        return action_sequence[1:], visited_states, current_observation

    def load(self, save_file: str) -> None:
        """ Loads model parameters from a specified filename.

        Arguments:
            save_file: str. The file to load from.
        """
        self.load_state_dict(torch.load(save_file, map_location=util.DEVICE))

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
        action_lengths_tensor: torch.Tensor = None
        action_index_tensor: torch.Tensor = None

        # [0] Batch the action sequences (if applicable)
        if self._args.get_decoder_args().use_recurrence():
            action_index_tensor, action_lengths_tensor = batch_util.batch_action_sequences(examples,
                                                                                           self._action_embedder)

        # [1] Get the gold distributions
        max_action_sequence_length = max([len(example.get_state_deltas()) for example in examples]) + 1

        batched_map_components: List[torch.Tensor] = \
            batch_util.batch_map_distributions(examples,
                                               environment_util.ENVIRONMENT_WIDTH,
                                               environment_util.ENVIRONMENT_DEPTH,
                                               self._args.get_decoder_args().weight_trajectory_by_time(),
                                               self._args.get_state_rep_args().full_observability(),
                                               max_action_sequence_length)

        # [2] Get the rotations
        positions, rotations = batch_util.batch_agent_configurations(examples, max_action_sequence_length)

        tensors: List[torch.Tensor] = list(batched_map_components[:-1]) + [positions,
                                                                           rotations,
                                                                           action_lengths_tensor,
                                                                           action_index_tensor]

        # [3] If the model is end to end, also batch the environment information.
        if self._end_to_end:
            if self._args.get_state_rep_args().full_observability():
                tensors = tensors \
                          + self._plan_predictor.batch_inputs([(example, None) for example in examples], True) \
                          + [batched_map_components[-1]]
            else:
                # The first four tensors are the same regardless of the index along the action sequence. For efficiency,
                #   these shouldn't be duplicated.
                static_batched_tensors: List[torch.Tensor] = self._plan_predictor.batch_inputs(
                    [(example, None) for example in examples], True, compute_dynamic_tensors=False)[:4]

                # Stacked plan inputs stacks each plan predictor input:
                #   - Sequence length of N is the number of types of input tensors
                #   - Individual sequence length of M is the batch size
                #   - First dimension of teach tensor is K_m, the action sequence length K of the mth example. This
                #     should be action_lengths_tensor - 1 across all examples.
                # This keeps track only of inputs that will change throughout the action execution (i.e., not the first
                # four tensors returned by the plan predictor's batcher).
                stacked_plan_inputs: List[List[torch.Tensor]] = list()

                for i, example in enumerate(examples):
                    # First dimension here is the "batch size", in this case the sequence length.
                    batched_example_tensors: List[torch.Tensor] = self._plan_predictor.batch_inputs(
                        [(example, observation) for observation in example.get_partial_observations()], True,
                        compute_static_tensors=False)[4:]

                    if i == 0:
                        stacked_plan_inputs = [[tensor] for tensor in batched_example_tensors]
                    else:
                        for j in range(len(stacked_plan_inputs)):
                            stacked_plan_inputs[j].append(batched_example_tensors[j])

                concat_plan_inputs = list()
                for tensor_type in stacked_plan_inputs:
                    concat_plan_inputs.append(torch.cat(tuple(tensor_type)))

                # concat_plan_inputs is of length N, with tensors of size \sum K_m for all m examples x 25 x 25.
                assert concat_plan_inputs[0].size(0) == torch.sum(action_lengths_tensor - 1)

                tensors = tensors + static_batched_tensors + concat_plan_inputs + [batched_map_components[-1]]

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

            action_lengths = None

            # If partial observability, need to stack things so the forward pass on the plan predictor is efficient.
            if not self._args.get_state_rep_args().full_observability():
                # Subtract 1 because these are one extra due to the START token.
                action_lengths = (args[6] - 1).tolist()
                new_card_mask = list()
                for i, length in enumerate(action_lengths):
                    new_card_mask.append(card_mask[i][0:length])
                card_mask = torch.cat(tuple(new_card_mask)).unsqueeze(1)

            auxiliary_predictions = self._plan_predictor(*args[8:-1], action_sequence_lengths=action_lengths)

            # Card distributions should be put through a sigmoid and masked.
            goal_probabilities = None
            if auxiliary.Auxiliary.FINAL_GOALS in auxiliary_predictions:
                goal_probabilities = torch.sigmoid(auxiliary_predictions[auxiliary.Auxiliary.FINAL_GOALS]) * card_mask

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
            if auxiliary.Auxiliary.OBSTACLES in auxiliary_predictions:
                # Need to put this through a sigmoid.
                obstacle_probabilities = torch.sigmoid(auxiliary_predictions[auxiliary.Auxiliary.OBSTACLES])

            # Need to reshape the inputs to the next part of the model so that it is back to batch x seq_len x ...
            if action_lengths:
                def reshape_and_pad(prediction: torch.Tensor):
                    # prediction is sum of K_m x ...
                    new_tensor: List[torch.Tensor] = list()
                    start_index: int = 0
                    for action_length in action_lengths:
                        prediction_slice: torch.Tensor = prediction[start_index:start_index + action_length]

                        # Pad it with zeroes if the prediction. Add one to the padding length because there needs to
                        # be an empty dimension at the end.
                        padding: torch.Tensor = torch.zeros(tuple([max(action_lengths) - action_length + 1] + list(
                            prediction[0].size()))).to(util.DEVICE)
                        prediction_slice = torch.cat((prediction_slice, padding))
                        start_index += action_length

                        new_tensor.append(prediction_slice)
                    return torch.cat(tuple(new_tensor), 1).permute(1, 0, 2, 3).contiguous()
                goal_probabilities = reshape_and_pad(goal_probabilities)
                avoid_probabilities = reshape_and_pad(avoid_probabilities)
                trajectory_distributions = reshape_and_pad(trajectory_distributions)
                obstacle_probabilities = reshape_and_pad(obstacle_probabilities)

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
            # The last element (sequence-wise) for action_embeddings and embedded_state don't matter -- this is the
            # embedding of the STOP token and the last environment state (the same as second to last because STOP
            # results in the same environment state). Loss is not computed over the final output of the RNN.
            #
            # In other words, the ith item represents the embedding of the token generated in step i-1 and
            # the embedding of the world state at time i.

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
                        obstacle_probabilities: torch.Tensor = None,
                        avoid_probabilities: torch.Tensor = None,
                        logger: evaluation_logger.EvaluationLogger = None) -> Tuple[
                            List[agent_actions.AgentAction], Dict[auxiliary.Auxiliary, torch.Tensor],
                            List[state_delta.StateDelta], Optional[partial_observation.PartialObservation]]:
        """ Gets predictions for a model doing inference (i.e., not gold forcing).

        Arguments:
            example: Example. The example to get outputs for.
            game_server: Game. The game server to use and query during inference.
            evaluation_arguments: EvalArgs. The arguments for evaluation.
            goal_probabilities: torch.Tensor. An optional distribution over cards.
            trajectory_distribution: torch.Tensor. An optional distribution over trajectories.
            obstacle_probabilities: torch.Tensor. An optional distribution over impassable locations.
            avoid_probabilities: torch.Tensor. An optional distribution over locations to avoid.
            logger: evaluation_logger.EvaluationLogger. A logger for logging evaluation results.
        """
        if evaluation_arguments is None:
            raise ValueError('Evaluation arguments must be passed if providing a game server.')

        auxiliary_predictions: Dict[auxiliary.Auxiliary, Any] = dict()
        last_observation: partial_observation.PartialObservation = None

        if self._args.get_state_rep_args().full_observability():
            if logger:
                raise NotImplementedError

            # If full observability, first compute the distributions, then use them to compute the action sequence.
            if trajectory_distribution is None:
                if self._end_to_end:
                    raise NotImplementedError
                else:
                    (trajectory_distribution,
                     goal_probabilities,
                     obstacle_probabilities,
                     avoid_probabilities,
                     _) = batch_util.batch_map_distributions([example],
                                                             environment_util.ENVIRONMENT_WIDTH,
                                                             environment_util.ENVIRONMENT_DEPTH,
                                                             self._args.get_decoder_args().weight_trajectory_by_time())

            if evaluation_arguments.visualize_auxiliaries():
                if not isinstance(game_server, unity_game.UnityGame):
                    raise ValueError('Can only visualize auxiliaries with a Unity game.')

            action_sequence, visited_states = self._predict_actions_full_observability(
                goal_probabilities.squeeze(),
                trajectory_distribution.squeeze(),
                obstacle_probabilities.squeeze(),
                avoid_probabilities.squeeze(),
                game_server,
                evaluation_arguments)

        else:
            # If partial observability, need to recompute distributions at each step.
            action_sequence, visited_states, last_observation = self._predict_actions_partial_observability(
                example, game_server, evaluation_arguments, logger)

        return action_sequence, auxiliary_predictions, visited_states, last_observation
