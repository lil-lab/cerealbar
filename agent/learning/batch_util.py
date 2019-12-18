"""Utilities for batching data."""
from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING

import numpy as np
import torch

from agent.environment import agent_actions
from agent.model.modules import word_embedder

if TYPE_CHECKING:
    from agent.data import instruction_example
    from agent.data import partial_observation
    from agent.environment import position
    from agent.environment import rotation
    from agent.environment import state_delta


def batch_instructions(examples: List[instruction_example.InstructionExample],
                       instruction_embedder: word_embedder.WordEmbedder) -> Tuple[torch.Tensor, torch.Tensor]:
    """Batches instructions for a list of examples given a word embedder with a set vocabulary."""

    instructions: List[List[str]] = [example.get_instruction() for example in examples]
    instruction_batch_indices: List[List[int]] = [[instruction_embedder.get_index(tok) for tok in seq]
                                                  for seq in instructions]
    instruction_lengths: List[int] = [len(instruction) for instruction in instructions]

    instruction_index_tensor: torch.Tensor = torch.zeros((len(instructions),
                                                          max(instruction_lengths)), dtype=torch.long)
    for idx, (sequence, sequence_length) in enumerate(zip(instruction_batch_indices, instruction_lengths)):
        instruction_index_tensor[idx, :sequence_length] = torch.tensor(sequence, dtype=torch.long)
    instruction_lengths_tensor: torch.Tensor = torch.tensor(instruction_lengths, dtype=torch.long)

    return instruction_index_tensor, instruction_lengths_tensor


def bhwc_to_bchw(tensor: torch.Tensor) -> torch.Tensor:
    return tensor.permute(0, 3, 1, 2)


def batch_action_sequences(examples: List[instruction_example.InstructionExample],
                           action_embedder: word_embedder.WordEmbedder) -> Tuple[torch.Tensor, torch.Tensor]:

    action_sequence_lengths: List[int] = [len(example.get_action_sequence()) + 1 for example in examples]
    max_action_length: int = max(action_sequence_lengths)

    # [0] Batch the action sequences (if applicable)
    action_batch_indices: List[List[int]] = [[action_embedder.get_index(str(agent_actions.AgentAction.START))] +
                                             [action_embedder.get_index(tok)
                                              for tok in example.get_action_sequence()] for example in examples]
    action_lengths_tensor: torch.Tensor = torch.tensor(action_sequence_lengths, dtype=torch.long)

    # The tensor containng the indices for tokens in the output sequence
    action_index_tensor: torch.Tensor = torch.zeros((len(examples), max_action_length), dtype=torch.long)
    for idx, (seq, seq_len) in enumerate(zip(action_batch_indices, action_sequence_lengths)):
        action_index_tensor[idx, :seq_len] = torch.tensor(seq, dtype=torch.long)
    action_index_tensor = action_index_tensor

    return action_index_tensor, action_lengths_tensor


def get_partial_observability_distributions(example: instruction_example.InstructionExample,
                                            current_observation: partial_observation.PartialObservation,
                                            weight_trajectory_by_time,
                                            environment_width, environment_depth):
    timestep_distribution = torch.from_numpy(example.get_correct_trajectory_distribution(
        weight_trajectory_by_time,
        full_observability, i)).float()

    # Find the target cards visible to the agent
    card_beliefs = example.get_partial_observations()[i].get_card_beliefs()
    target_cards = example.get_touched_cards()

    for believed_card in card_beliefs:
        card_position = believed_card.get_position()
        # Add probability of 1 for believed target cards
        if believed_card in target_cards:
            example_goal_probabilities[i][card_position.x][card_position.y] = 1.
        # And avoid probabiltiy of 1 for believed non-target cards (except the initial card if the agent
        # is on it)
        elif card_position != example.get_initial_state().follower.get_position():
            example_avoid_probabilities[i][card_position.x][card_position.y] = 1.

    state_mask = np.zeros((environment_width, environment_depth))
    for viewed_position in example.get_partial_observations()[i].lifetime_observed_positions():
        state_mask[viewed_position.x][viewed_position.y] = 1.

    # Append a masked
    example_obstacle_probabilities.append(torch.from_numpy(full_obstacle_probability * state_mask))


def batch_map_distributions(examples: List[instruction_example.InstructionExample],
                            environment_width: int,
                            environment_depth: int,
                            weight_trajectory_by_time: bool,
                            full_observability: bool = True,
                            max_action_sequence_length: int = 0) -> Tuple[torch.Tensor,
                                                                          torch.Tensor,
                                                                          torch.Tensor,
                                                                          torch.Tensor,
                                                                          torch.Tensor]:
    # TODO: This can be more efficient if it's not padded
    trajectory_distributions: List[torch.Tensor] = []
    goal_probabilities: List[torch.Tensor] = []
    goal_masks: List[torch.Tensor] = []
    obstacle_probabilities: List[torch.Tensor] = []
    avoid_probabilities: List[torch.Tensor] = []

    if full_observability:
        for example in examples:
            # Each distribution is N x N
            trajectory_distribution: torch.Tensor = torch.from_numpy(
                example.get_correct_trajectory_distribution(weight_by_time=weight_trajectory_by_time)).float()

            avoid_probability = torch.zeros(environment_width, environment_depth).float()
            goal_probability = torch.zeros(environment_width, environment_depth).float()

            for pos, score in example.get_card_scores().items():
                goal_probability[pos.x][pos.y] = score

            # Doesn't count the card the agent was currently on.
            cards_to_reach = [card.get_position() for card in example.get_touched_cards(include_start_position=True)]
            for card in example.get_initial_cards():
                if card.get_position() not in cards_to_reach:
                    avoid_probability[card.get_position().x][card.get_position().y] = 1.

            trajectory_distributions.append(trajectory_distribution)
            goal_probabilities.append(goal_probability)
            avoid_probabilities.append(avoid_probability)

            this_goal_mask = torch.zeros(goal_probability.size())
            for card in example.get_initial_cards():
                this_goal_mask[card.get_position().x][card.get_position().y] = 1.
            goal_masks.append(this_goal_mask)

            obstacle_probability = torch.zeros(environment_width, environment_depth).float()
            for pos in sorted(example.get_obstacle_positions()):
                assert pos not in example.get_visited_positions()
                obstacle_probability[pos.x][pos.y] = 1.
            obstacle_probabilities.append(obstacle_probability)

        return (torch.stack(tuple(trajectory_distributions)).unsqueeze(1),
                torch.stack(tuple(goal_probabilities)).unsqueeze(1),
                torch.stack(tuple(obstacle_probabilities)).unsqueeze(1),
                torch.stack(tuple(avoid_probabilities)).unsqueeze(1),
                torch.stack(tuple(goal_masks)).unsqueeze(1))
    else:
        for example in examples:
            # Each distribution is max_action_sequence_length x N x N
            example_trajectory_distributions: List[torch.Tensor] = list()

            example_goal_probabilities = torch.zeros(max_action_sequence_length, environment_width, environment_depth)
            example_avoid_probabilities = torch.zeros(max_action_sequence_length, environment_width, environment_depth)
            example_goal_masks = torch.zeros(max_action_sequence_length, environment_width, environment_depth)

            full_obstacle_probability = np.zeros((environment_width, environment_depth))
            for pos in sorted(example.get_obstacle_positions()):
                assert pos not in example.get_visited_positions()
                full_obstacle_probability[pos.x][pos.y] = 1.

            example_obstacle_probabilities: List[torch.Tensor] = list()

            for i in range(max_action_sequence_length):
                state_mask = np.zeros((environment_width, environment_depth))
                if i < len(example.get_state_deltas()):
                    timestep_distribution = torch.from_numpy(example.get_correct_trajectory_distribution(
                        weight_trajectory_by_time,
                        full_observability, example.get_partial_observations()[i])).float()

                    # Find the target cards visible to the agent
                    card_beliefs = example.get_partial_observations()[i].get_card_beliefs()
                    target_cards = example.get_touched_cards()

                    for believed_card in card_beliefs:
                        card_position = believed_card.get_position()
                        # Add probability of 1 for believed target cards
                        if believed_card in target_cards:
                            example_goal_probabilities[i][card_position.x][card_position.y] = 1.
                        # And avoid probabiltiy of 1 for believed non-target cards (except the initial card if the agent
                        # is on it)
                        elif card_position != example.get_initial_state().follower.get_position():
                            example_avoid_probabilities[i][card_position.x][card_position.y] = 1.

                        example_goal_masks[i][card_position.x][card_position.y] = 1.

                    for viewed_position in example.get_partial_observations()[i].lifetime_observed_positions():
                        state_mask[viewed_position.x][viewed_position.y] = 1.

                    example_obstacle_probabilities.append(torch.from_numpy(full_obstacle_probability * state_mask))
                else:
                    example_obstacle_probabilities.append(torch.from_numpy(full_obstacle_probability * state_mask))
                    timestep_distribution = torch.zeros(environment_width, environment_depth).float()

                example_trajectory_distributions.append(timestep_distribution.unsqueeze(0))

            trajectory_distributions.append(torch.stack(tuple(example_trajectory_distributions)))
            goal_probabilities.append(example_goal_probabilities)
            avoid_probabilities.append(example_avoid_probabilities)
            obstacle_probabilities.append(torch.stack(tuple(example_obstacle_probabilities)))
            goal_masks.append(torch.stack(tuple(example_goal_masks)))

        return (torch.stack(tuple(trajectory_distributions)).squeeze().float(),
                torch.stack(tuple(goal_probabilities)).float(),
                torch.stack(tuple(obstacle_probabilities)).float(),
                torch.stack(tuple(avoid_probabilities)).float(),
                torch.stack(tuple(goal_masks)).float())


def batch_agent_configurations(examples: List[instruction_example.InstructionExample],
                               max_action_length: int) -> Tuple[torch.Tensor, torch.Tensor]:
    # TODO: This can be more efficient if it's not padded
    positions: List[torch.Tensor] = []
    rotations: List[torch.Tensor] = []

    for example in examples:
        state_deltas: List[state_delta.StateDelta] = example.get_state_deltas()
        delta = state_deltas[0]
        example_positions = []
        example_rotations = []
        for i in range(max_action_length):
            if i < len(example.get_state_deltas()):
                delta = state_deltas[i]

            pos: position.Position = delta.follower.get_position()
            rot: rotation.Rotation = delta.follower.get_rotation()
            example_positions.append(torch.tensor([float(pos.x), float(pos.y)]))
            example_rotations.append(torch.tensor(rot.to_radians()))
        positions.append(torch.stack(tuple(example_positions)))
        rotations.append(torch.stack(tuple(example_rotations)))

    return torch.stack(tuple(positions)), torch.stack(tuple(rotations))


def expand_flat_map_distribution(distribution: torch.Tensor, num_timesteps: int) -> torch.Tensor:
    batch_size, _, raw_height, raw_width = distribution.size()
    expanded_cards = \
        distribution.unsqueeze(4).expand((batch_size, 1, raw_height, raw_width, num_timesteps))
    return expanded_cards.permute(0, 4, 1, 2, 3).contiguous().view(batch_size * num_timesteps,
                                                                   1,
                                                                   raw_height,
                                                                   raw_width)
