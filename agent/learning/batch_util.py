"""Utilities for batching data."""
from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING
import torch
from agent.environment import agent_actions
from agent.model.modules import word_embedder

if TYPE_CHECKING:
    from agent.data import instruction_example
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


def batch_map_distributions(examples: List[instruction_example.InstructionExample],
                            environment_width: int,
                            environment_depth: int,
                            weight_trajectory_by_time: bool) -> Tuple[torch.Tensor,
                                                                      torch.Tensor,
                                                                      torch.Tensor,
                                                                      torch.Tensor,
                                                                      torch.Tensor]:
    trajectory_distributions: List[torch.Tensor] = []
    card_distributions: List[torch.Tensor] = []
    card_masks: List[torch.Tensor] = []
    impassable_distributions: List[torch.Tensor] = []
    avoid_distributions: List[torch.Tensor] = []

    # TODO: Partial observability

    for example in examples:
        correct_distribution = example.get_correct_trajectory_distribution(weight_by_time=weight_trajectory_by_time)

        trajectory_distribution: torch.Tensor = torch.from_numpy(correct_distribution).float()

        avoid_distribution = torch.zeros(environment_width, environment_depth).float()
        card_distribution = torch.zeros(environment_width, environment_depth).float()

        for pos, score in example.get_card_scores().items():
            card_distribution[pos.x][pos.y] = score

        # Doesn't count the card the agent was currently on.
        cards_to_reach = [card.get_position() for card in example.get_touched_cards(include_start_position=True)]
        for card in example.get_initial_cards():
            if card.get_position() not in cards_to_reach:
                avoid_distribution[card.get_position().x][card.get_position().y] = 1.

        trajectory_distributions.append(trajectory_distribution)
        card_distributions.append(card_distribution)
        avoid_distributions.append(avoid_distribution)

        card_mask = torch.zeros(card_distribution.size())
        for card in example.get_initial_cards():
            card_mask[card.get_position().x][card.get_position().y] = 1.
        card_masks.append(card_mask)

        impassable_distribution = torch.zeros(environment_width, environment_depth).float()
        for pos in sorted(example.get_obstacle_positions()):
            assert pos not in example.get_visited_positions()
            impassable_distribution[pos.x][pos.y] = 1.
        impassable_distributions.append(impassable_distribution)

    return (torch.stack(tuple(trajectory_distributions)),
            torch.stack(tuple(card_distributions)).unsqueeze(1),
            torch.stack(tuple(impassable_distributions)).unsqueeze(1),
            torch.stack(tuple(avoid_distributions)).unsqueeze(1),
            torch.stack(tuple(card_masks)).unsqueeze(1))


def batch_agent_configurations(examples: List[instruction_example.InstructionExample],
                               max_action_length: int) -> Tuple[torch.Tensor, torch.Tensor]:
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
