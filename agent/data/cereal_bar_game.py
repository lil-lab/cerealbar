"""Saves all information about a recorded Cereal Bar game."""
from __future__ import annotations

from typing import TYPE_CHECKING

from agent.data import gameplay_action
from agent.environment import state_delta

if TYPE_CHECKING:
    from agent.data import instruction_example
    from typing import Any, Dict, List, Tuple
    from agent.environment import environment_objects
    from agent.config import data_args
    from agent.environment import card
    from agent.environment import position
    from agent.environment import terrain


class CerealBarGame:
    def __init__(self, json_obj: Dict[str, Any], data_arguments: data_args.DataArgs):
        self._game_id: str = json_obj['game_id']
        self._split: str = json_obj['split'] if 'split' in json_obj else ''
        self._seed: int = json_obj['seed']
        self._num_cards: int = json_obj['num_cards']
        self._score: int = json_obj['score']

        if self._score > 0 and len(json_obj['actions']) < 2:
            print(self._game_id)

        self._actions: List[gameplay_action.GameplayAction] = gameplay_action.process_actions(json_obj['actions'],
                                                                                              data_arguments)

        self._hex_info: List[Tuple[terrain.Terrain, position.Position]] = None
        self._object_info: List[environment_objects.EnvironmentObject] = None
        self._examples: List[instruction_example.InstructionExample] = None
        self._expected_sets: List[Tuple[int, List[card.Card], List[card.Card]]] = None

    def get_initial_state(self) -> state_delta.StateDelta:
        """Gets the game's initial state (cards and player positions/rotations)."""
        for action in self._actions:
            if isinstance(action, gameplay_action.MovementAction) or isinstance(action,
                                                                                gameplay_action.FinishCommandAction):
                return action.get_prior_game_info()

    def get_id(self) -> str:
        return self._game_id

    def get_seed(self) -> int:
        return self._seed

    def is_in_split(self) -> bool:
        return self._split != ''

    def is_train(self) -> bool:
        return self._split == 'train'

    def is_dev(self) -> bool:
        return self._split == 'dev'

    def is_test(self) -> bool:
        return self._split == 'test'

    def get_num_cards(self) -> int:
        return self._num_cards

    def get_score(self) -> int:
        return self._score

    def get_actions(self) -> List[gameplay_action.GameplayAction]:
        return self._actions

    def get_instructions(self) -> List[gameplay_action.InstructionAction]:
        """Gets all the completed instructions in the game."""
        return [action for action in self._actions if
                isinstance(action, gameplay_action.InstructionAction) and action.completed()]

    def get_hexes(self) -> List[Tuple[terrain.Terrain, position.Position]]:
        """Gets all the hexes in the game board (position and terrain information)."""
        if not self._hex_info:
            raise ValueError('Hexes were not set')
        return self._hex_info

    def get_objects(self) -> List[environment_objects.EnvironmentObject]:
        """Gets all the objects in the game board (permanent objects like trees or houses)."""
        if not self._object_info:
            raise ValueError('Objects were not set')
        return self._object_info

    def set_action_state(self, index: int, game_info: state_delta.StateDelta,
                         posterior_info: state_delta.StateDelta = None):
        """Sets the states associated with a movement or finish-command action."""
        assert (isinstance(self._actions[index], gameplay_action.MovementAction)
                or isinstance(self._actions[index], gameplay_action.FinishCommandAction))
        if isinstance(self._actions[index], gameplay_action.MovementAction):
            self._actions[index].set_game_info(game_info, posterior_info)
        else:
            self._actions[index].set_prior_game_info(game_info)

    def set_hexes(self, hex_info: List[Tuple[terrain.Terrain, position.Position]]) -> None:
        self._hex_info = hex_info

    def set_objects(self, object_info: List[environment_objects.EnvironmentObject]) -> None:
        self._object_info = object_info

    def get_leader_actions(self,
                           first_turn: int = 0,
                           last_turn: int = -1,
                           use_all_actions: bool = False) -> List[List[gameplay_action.GameplayAction]]:
        """Gets a list of movement actions taken by a leader, segmented by turn.

        Args:
            first_turn: The first turn that should be included in the returned list.
            last_turn: The last turn that should be included in the returned list.
            use_all_actions: Whether all actions in the entire game should be returneed.

        """
        leader_actions: List[List[gameplay_action.GameplayAction]] = []
        current_leader_seq: List[gameplay_action.GameplayAction] = []

        for i, action in enumerate(self._actions):
            if (isinstance(action,
                           gameplay_action.MovementAction) and action.get_agent() ==
                    environment_objects.ObjectType.LEADER):
                current_leader_seq.append(action)
            elif (isinstance(action,
                             gameplay_action.EndTurnAction) and action.get_agent() ==
                  environment_objects.ObjectType.LEADER):
                leader_actions.append(current_leader_seq)
                current_leader_seq = []
            elif isinstance(action, gameplay_action.InstructionAction) and action.completed():
                current_leader_seq.append(action)

        if not use_all_actions:
            if last_turn >= 0:
                return leader_actions[first_turn:last_turn]
            return leader_actions[first_turn:]

        # If using all actions, resegment so it's in sequences of 5 actions. This is necessary for evaluation.
        segmented_seqs: List[List[gameplay_action.GameplayAction]] = [[]]
        for action_seq in leader_actions[first_turn:]:
            for action in action_seq:
                segmented_seqs[-1].append(action)

                if len([action for action in segmented_seqs[-1] if
                        isinstance(action, gameplay_action.MovementAction)]) == 5 \
                        and isinstance(action, gameplay_action.MovementAction):
                    segmented_seqs.append(list())
        return segmented_seqs

    def set_examples(self, examples: List[instruction_example.InstructionExample]) -> None:
        if self._examples is not None:
            raise ValueError('There are already examples saved for this game.')
        self._examples = examples

    def set_sets_made(self, sets_made: List[Tuple[int, List[card.Card], List[card.Card]]]) -> None:
        if self._expected_sets is not None:
            raise ValueError('There are already expected sets saved for this game.')
        self._expected_sets = sets_made

    def get_expected_sets(self, first_instruction: int = 0) -> List[Tuple[List[card.Card], List[card.Card]]]:
        """Gets the sets that are expected to be made during and after an instruction.

        Args:
            first_instruction: The index of the instruction to start in for getting expected sets.
        """
        i: int = 0
        found_set = False
        for i, (instr_idx, _, _) in enumerate(self._expected_sets):
            if instr_idx >= first_instruction:
                found_set = True
                break
        if found_set:
            return [(t[1], t[2]) for t in self._expected_sets[i:]]
        return []

    def get_examples(self) -> List[instruction_example.InstructionExample]:
        return self._examples

    def get_expected_card_states(self, first_instruction: int = 0) -> List[List[card.Card]]:
        """Gets the expected resulting cards after a given instruction. """
        i: int = 0
        num_instructions: int = 0

        # Find the first movement or finish-command action after that instruction.
        for i, action in enumerate(self._actions):
            if isinstance(action, gameplay_action.FinishCommandAction):
                if num_instructions == first_instruction:
                    break
                num_instructions += 1
            if isinstance(action, gameplay_action.MovementAction) \
                    and action.get_agent() == environment_objects.ObjectType.FOLLOWER \
                    and num_instructions == first_instruction:
                break

        assert (isinstance(self._actions[i], gameplay_action.FinishCommandAction)
                or isinstance(self._actions[i], gameplay_action.MovementAction))

        prev_cards: List[card.Card] = self._actions[i].get_prior_game_info().cards
        unique_states: List[List[card.Card]] = [prev_cards]
        for action in self._actions[i:]:
            if isinstance(action, gameplay_action.MovementAction) or isinstance(action,
                                                                                gameplay_action.FinishCommandAction):
                resulting_cards: List[card.Card] = action.get_prior_game_info().cards

                # See if it changed
                if not state_delta.card_states_equal(unique_states[-1], resulting_cards):
                    unique_states.append(resulting_cards)
        return unique_states
