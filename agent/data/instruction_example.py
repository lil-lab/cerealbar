"""Example of an instruction paired with agent actions."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from agent import util
from agent.data import gameplay_action
from agent.data import partial_observation
from agent.environment import agent_actions
from agent.environment import environment_objects
from agent.environment import state_delta
from agent.environment import terrain
from agent.environment import util as environment_util

if TYPE_CHECKING:
    from typing import Dict, List, Optional, Set, Tuple
    from agent.data import cereal_bar_game
    from agent.environment import card
    from agent.environment import position


class InstructionExample:
    def __init__(self,
                 instruction: List[str],
                 target_action_sequence: List[Tuple[state_delta.StateDelta, agent_actions.AgentAction,
                                                    partial_observation.PartialObservation]],
                 paired_game: cereal_bar_game.CerealBarGame,
                 example_idx_in_interaction: int,
                 leader_actions: List[List[gameplay_action.GameplayAction]],
                 index_of_first_leader_turn: int,
                 sets_made_during_instruction: List[Tuple[List[card.Card], List[card.Card]]],
                 number_of_steps_in_first_turn: int,
                 number_of_instructions_when_starting: int):
        self._instruction: List[str] = instruction
        self._target_action_sequence: List[
            Tuple[state_delta.StateDelta, agent_actions.AgentAction,
                  partial_observation.PartialObservation]] = target_action_sequence
        self._paired_game: cereal_bar_game.CerealBarGame = paired_game
        self._example_idx_in_interaction: int = example_idx_in_interaction
        self._leader_actions: List[List[gameplay_action.GameplayAction]] = leader_actions
        self._index_of_first_leader_turn: int = index_of_first_leader_turn
        self._sets_made_during_instruction: List[Tuple[List[card.Card], List[card.Card]]] = sets_made_during_instruction
        self._number_of_steps_in_first_turn: int = number_of_steps_in_first_turn
        self._number_of_instructions_when_starting: int = number_of_instructions_when_starting

        self._static_indices = None

    def hash_representation(self) -> str:
        str_hash: str = self.get_id() + '/' + \
                        ' '.join([str(action) for action in self.get_action_sequence()]) + '/' + \
                        str(self.get_initial_state().follower.get_position()) + '/' + \
                        str(self.get_initial_state().follower.get_rotation()) + '/'
        for initial_card in self.get_initial_state().cards:
            str_hash += str(initial_card) + '/'
        return str_hash

    def get_seed(self) -> int:
        return self._paired_game.get_seed()

    def get_id(self) -> str:
        return self._paired_game.get_id() + '-' + str(self._example_idx_in_interaction)

    def get_instruction(self) -> List[str]:
        return self._instruction

    def get_action_sequence(self) -> List[str]:
        return [str(x[1]) for x in self._target_action_sequence]

    def get_state_deltas(self) -> List[state_delta.StateDelta]:
        return [x[0] for x in self._target_action_sequence]

    def get_initial_cards(self) -> List[card.Card]:
        return self.get_initial_state().cards

    def get_initial_state(self) -> state_delta.StateDelta:
        return self._target_action_sequence[0][0]

    def get_static_indices(self, state_representation) -> np.array:
        if self._static_indices is None:
            self._static_indices = state_representation.static_indices(self)
        return self._static_indices

    def get_objects(self) -> List[environment_objects.EnvironmentObject]:
        return self._paired_game.get_objects()

    def get_obstacle_positions(self) -> List[position.Position]:
        obstacle_positions: List[position.Position] = list()
        for ter, hexp in self.get_hexes():
            if ter in terrain.OBSTACLE_TERRAINS:
                obstacle_positions.append(hexp)
        for obj in self.get_objects():
            assert obj.get_type() != environment_objects.ObjectType.CARD
            obstacle_positions.append(obj.get_position())
        return obstacle_positions

    def get_hexes(self) -> List[Tuple[terrain.Terrain, position.Position]]:
        return self._paired_game.get_hexes()

    def get_visited_positions(self, include_start: bool = True, start_idx: int = 0) -> List[position.Position]:
        """Gets an ordered list of positions visited by the agent along the gold trajectory.
        
        Args:
            include_start: Whether to include the start position in the list.
            start_idx: The action index to start from.
        
        """
        if include_start:
            return list(set([delta.follower.get_position() for delta in self.get_state_deltas()[start_idx:]]))

        state: state_delta.StateDelta = self.get_state_deltas()[start_idx]
        original_position: position.Position = state.follower.get_position()
        pos_list: List[position.Position] = []
        has_moved: bool = False
        for delta in self.get_state_deltas()[start_idx:]:
            current_position = delta.follower.get_position()
            if current_position == original_position and not has_moved:
                continue
            else:
                has_moved = True
            pos_list.append(current_position)

        return list(set(pos_list))

    def get_partial_observations(self) -> List[partial_observation.PartialObservation]:
        return [x[2] for x in self._target_action_sequence]

    def get_leader_actions(self,
                           limit_to_instruction: bool = True,
                           use_all_actions: bool = False) -> List[List[gameplay_action.GameplayAction]]:
        """Returns the leader actions aligning to this instruction.

        Args:
            limit_to_instruction: Whether to only return actions that occurred during the execution of this instruction.
            use_all_actions: TODO: What does this mean?
        """
        if limit_to_instruction:
            return self._leader_actions
        actions_from_game: List[List[gameplay_action.GameplayAction]] = self._paired_game.get_leader_actions(
            first_turn=self._index_of_first_leader_turn,
            use_all_actions=use_all_actions)
        if use_all_actions:
            return actions_from_game

        for action1, action2 in zip(self._leader_actions, actions_from_game):
            if action1 != action2:
                raise ValueError('Actions not the same!')
        return actions_from_game

    def get_expected_sets(self) -> List[Tuple[List[card.Card], List[card.Card]]]:
        """Gets the sets that should be made during this instruction and afterwards."""
        return self._paired_game.get_expected_sets(first_instruction=self._example_idx_in_interaction)

    def get_number_of_moves_in_first_turn(self) -> int:
        return self._number_of_steps_in_first_turn

    def get_final_state(self) -> state_delta.StateDelta:
        if self._target_action_sequence[-1][1] != agent_actions.AgentAction.STOP:
            raise ValueError('Final action was not STOP')

        # The final state is the prior state for the last action, which is the STOP action.
        return self._target_action_sequence[-1][0]

    def get_touched_cards(self,
                          start_idx: int = 0,
                          include_start_position: bool = False,
                          allow_duplicates: bool = True) -> List[card.Card]:
        """Gets all cards touched along the gold trajectory.

        Args:
            start_idx: The first index along the trajectory to consider when computing which cards were touched.
            include_start_position: Whether to include any cards that are in the initial position.
            allow_duplicates: TODO: Not sure what this setting does actually.

        """
        if allow_duplicates:
            state: state_delta.StateDelta = self.get_state_deltas()[start_idx]
            original_card_positions: List[position.Position] = [state_card.get_position() for state_card in state.cards]

            agent_positions: List[position.Position] = self.get_visited_positions(
                include_start=include_start_position, start_idx=start_idx)
            reached_card_positions = set(original_card_positions) & set(agent_positions)

            reached_cards: List[card.Card] = list()
            for state_card in state.cards:
                if state_card.get_position() in reached_card_positions:
                    reached_cards.append(state_card)
            return reached_cards
        else:
            return get_changed_cards_along_trajectory(self.get_state_deltas())

    def get_card_scores(self) -> Dict[position.Position, float]:
        # TODO: Partial observability
        scores: Dict[position.Position, float] = dict()
        for initial_card in self.get_initial_cards():
            scores[initial_card.get_position()] = 1. if initial_card in self.get_touched_cards() else 0.
        return scores

    def get_correct_trajectory_distribution(self,
                                            weight_by_time: bool,
                                            full_observability: bool = True,
                                            observation: partial_observation.PartialObservation = None,
                                            observed_positions: Set[position.Position] = None) -> np.array:

        if full_observability and observation:
            raise ValueError('If using full observability, do not need to provide an observation object.')

        distribution: np.array = np.zeros((environment_util.ENVIRONMENT_WIDTH, environment_util.ENVIRONMENT_DEPTH))
        if weight_by_time:
            path: List[position.Position] = [delta.follower.get_position() for delta in self.get_state_deltas()]

            if not full_observability:
                # Remove things from the path that were not observed at this point.
                if not observed_positions:
                    observed_positions = observation.currently_observed_positions()
                new_path: List[position.Position] = list()
                for pos in path:
                    if pos in observed_positions:
                        new_path.append(pos)
                path = new_path

            # The weight is one over the path length, rather than the number of unique locations.
            # The weight is zero if the path is empty (e.g., if the agent is off the path during inference).
            if len(path) == 0:
                weight_per_hex = 0.
            else:
                weight_per_hex: float = 1. / len(path)

            for location in path:
                # Add the weight rather than setting it.
                distribution[location.x][location.y] += weight_per_hex
        else:
            correct_trajectory: List[position.Position] = self.get_visited_positions()

            if not full_observability:
                # Limit by positions visible _right now_. The distribution won't include hexes that aren't currently
                # visible.
                if not observed_positions:
                    observed_positions = observation.currently_observed_positions()
                correct_trajectory = list(set(correct_trajectory) & observed_positions)

            if len(correct_trajectory) == 0:
                weight_per_hex = 0.
            else:
                weight_per_hex: float = 1. / len(correct_trajectory)

            for location in correct_trajectory:
                distribution[location.x][location.y] = weight_per_hex

        return distribution


def construct_game_examples(game: cereal_bar_game.CerealBarGame, max_instruction_index: int):
    # First, segment the actions by instruction.
    all_sets: List[Tuple[int, List[card.Card], List[card.Card]]] = list()

    # Segments actions into instructions
    segmented_actions: List[List[gameplay_action.GameplayAction]] = list(list())
    current_action_sequence: List[gameplay_action.GameplayAction] = list()
    instructions: List[gameplay_action.InstructionAction] = list()

    for action in game.get_actions():
        current_action_sequence.append(action)
        if isinstance(action, gameplay_action.FinishCommandAction):
            segmented_actions.append(current_action_sequence)
            current_action_sequence = list()
        elif isinstance(action, gameplay_action.InstructionAction) and action.completed():
            instructions.append(action)

    assert len(instructions) == len(segmented_actions) or len(instructions) == len(segmented_actions) - 1

    game_examples: List[InstructionExample] = list()
    current_leader_turn_idx: int = 0

    num_steps_remaining: int = 10
    buffer_size: int = 0

    current_observation: partial_observation.PartialObservation = game.get_first_partial_observation()

    for i, segmented_seq in enumerate(segmented_actions):
        follower_action_sequence: List[Tuple[state_delta.StateDelta, agent_actions.AgentAction,
                                             partial_observation.PartialObservation]] = list()
        current_leader_actions_dict: Dict[int, List[gameplay_action.GameplayAction]] = dict()
        current_sets: List[Tuple[List[card.Card], List[card.Card]]] = list()

        following: bool = False
        initial_num_steps_remaining = num_steps_remaining
        initial_buffer_size = buffer_size

        for action in segmented_seq:
            if isinstance(action, gameplay_action.MovementAction):
                if action.get_agent() == environment_objects.ObjectType.FOLLOWER:
                    follower_action_sequence.append((action.get_prior_game_info(), action.get_action(),
                                                     current_observation))

                    if not following:
                        initial_num_steps_remaining = num_steps_remaining
                        initial_buffer_size = buffer_size

                    following = True
                    num_steps_remaining -= 1
                else:
                    if following:
                        if current_leader_turn_idx not in current_leader_actions_dict:
                            current_leader_actions_dict[current_leader_turn_idx] = list()
                        current_leader_actions_dict[current_leader_turn_idx].append(action)

                set_result: Optional[Tuple[List[card.Card], List[card.Card]]] = \
                    state_delta.set_difference(action.get_prior_game_info().cards,
                                               action.get_posterior_game_info().cards)
                if set_result:
                    set_instr_idx = i if following else i - 1
                    all_sets.append((set_instr_idx, set_result[0], set_result[1]))
                    if following:
                        current_sets.append(set_result)

                # Update the observability
                current_observation = partial_observation.update_observation(current_observation,
                                                                             action.get_posterior_game_info())

            elif isinstance(action, gameplay_action.EndTurnAction):
                if action.get_agent() == environment_objects.ObjectType.FOLLOWER:
                    num_steps_remaining = 10
                else:
                    if following and current_leader_turn_idx not in current_leader_actions_dict:
                        current_leader_actions_dict[current_leader_turn_idx] = list()
                    current_leader_turn_idx += 1
            elif isinstance(action, gameplay_action.InstructionAction) and action.completed():
                if following:
                    if current_leader_turn_idx not in current_leader_actions_dict:
                        current_leader_actions_dict[current_leader_turn_idx] = list()
                    current_leader_actions_dict[current_leader_turn_idx].append(action)
                buffer_size += 1
            elif isinstance(action, gameplay_action.FinishCommandAction):
                if not following:
                    initial_buffer_size = buffer_size
                buffer_size -= 1
                follower_action_sequence.append((action.get_prior_game_info(), agent_actions.AgentAction.STOP,
                                                 current_observation))

        leader_actions_to_pass: List[List[gameplay_action.GameplayAction]] = list()
        if current_leader_actions_dict:
            first_leader_turn_idx: int = min(current_leader_actions_dict.keys())
            for j in range(first_leader_turn_idx, max(current_leader_actions_dict.keys()) + 1):
                if j not in current_leader_actions_dict:
                    leader_actions_to_pass.append(list())
                else:
                    leader_actions_to_pass.append((current_leader_actions_dict[j]))
        else:
            first_leader_turn_idx: int = current_leader_turn_idx

        from_game_actions = \
            game.get_leader_actions()[first_leader_turn_idx:first_leader_turn_idx + len(leader_actions_to_pass)]
        assert from_game_actions == leader_actions_to_pass

        example: InstructionExample = \
            InstructionExample(instructions[i].get_tokenized_instruction(),
                               follower_action_sequence,
                               game,
                               i,
                               leader_actions_to_pass,
                               first_leader_turn_idx,
                               current_sets,
                               initial_num_steps_remaining,
                               initial_buffer_size)

        game_examples.append(example)

        if len(game_examples) >= max_instruction_index >= 0:
            break

    return game_examples, all_sets


def construct_examples(games: Dict[str, cereal_bar_game.CerealBarGame],
                       max_instruction_index: int) -> Dict[str, InstructionExample]:
    examples: Dict[str, InstructionExample] = dict()

    with util.get_progressbar('constructing examples', len(games)) as pbar:
        for game_idx, (game_id, game) in enumerate(games.items()):
            game_examples, all_sets = construct_game_examples(game, max_instruction_index)
            game.set_examples(game_examples)
            game.set_sets_made(all_sets)
            for i, example in enumerate(game_examples):
                examples[game_id + '-' + str(i)] = example
            pbar.update(game_idx)

    return examples


def get_example_action_index_pairs(examples: Dict[str, InstructionExample],
                                   full_observability: bool,
                                   observability_refresh_rate: int) -> List[Tuple[str, int]]:
    if not full_observability:
        if observability_refresh_rate > 1:
            raise ValueError('Refreshing after more than one action is not supported.')
        ids = list()
        for example_id, example in examples.items():
            for i in range(len(example.get_action_sequence())):
                ids.append((example_id, i))
        return ids
    return [(key, -1) for key in examples.keys()]
