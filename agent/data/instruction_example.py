"""Example of an instruction paired with agent actions."""

from typing import Dict, List, Optional, Tuple

from agent.data import cereal_bar_game
from agent.data import gameplay_action
from agent.environment import agent_actions
from agent.environment import card
from agent.environment import environment_objects
from agent.environment import state_delta


class InstructionExample:
    def __init__(self,
                 instruction: List[str],
                 target_action_sequence: List[Tuple[state_delta.StateDelta, agent_actions.AgentAction]],
                 paired_game: cereal_bar_game.CerealBarGame,
                 example_idx_in_interaction: int,
                 leader_actions: List[List[gameplay_action.GameplayAction]],
                 index_of_first_leader_turn: int,
                 sets_made_during_instruction: List[Tuple[List[card.Card], List[card.Card]]],
                 number_of_steps_in_first_turn: int,
                 number_of_instructions_when_starting: int):
        self._instruction: List[str] = instruction
        self._target_action_sequence: List[
            Tuple[state_delta.StateDelta, agent_actions.AgentAction]] = target_action_sequence
        self._paired_game: cereal_bar_game.CerealBarGame = paired_game
        self._example_idx_in_interaction: int = example_idx_in_interaction
        self._leader_actions: List[List[gameplay_action.GameplayAction]] = leader_actions
        self._index_of_first_leader_turn: int = index_of_first_leader_turn
        self._sets_made_during_instruction: List[Tuple[List[card.Card], List[card.Card]]] = sets_made_during_instruction
        self._number_of_steps_in_first_turn: int = number_of_steps_in_first_turn
        self._number_of_instructions_when_starting: int = number_of_instructions_when_starting

    def get_id(self) -> str:
        return self._paired_game.get_id() + '-' + str(self._example_idx_in_interaction)


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

    for i, segmented_seq in enumerate(segmented_actions):
        follower_action_sequence: List[Tuple[state_delta.StateDelta, agent_actions.AgentAction]] = list()
        current_leader_actions_dict: Dict[int, List[gameplay_action.GameplayAction]] = dict()
        current_sets: List[Tuple[List[card.Card], List[card.Card]]] = list()

        following: bool = False
        initial_num_steps_remaining = num_steps_remaining
        initial_buffer_size = buffer_size

        for action in segmented_seq:
            if isinstance(action, gameplay_action.MovementAction):
                if action.get_agent() == environment_objects.ObjectType.FOLLOWER:
                    follower_action_sequence.append((action.get_prior_game_info(), action.get_action()))

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
                follower_action_sequence.append((action.get_prior_game_info(), agent_actions.AgentAction.STOP))

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

    for game_id, game in games.items():
        game_examples, all_sets = construct_game_examples(game, max_instruction_index)
        game.set_examples(game_examples)
        game.set_sets_made(all_sets)
        for i, example in enumerate(game_examples):
            examples[game_id + '-' + str(i)] = example

    return examples
