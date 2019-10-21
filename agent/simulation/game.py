"""Contains the superclass for a game."""
import copy
import logging
import random
from abc import ABC, abstractmethod
from typing import List, Tuple, Set

from agent.config import game_args
from agent.data import gameplay_action
from agent.environment import agent_actions, state_delta
from agent.environment import card
from agent.environment import environment_objects
from agent.environment import terrain
from agent.environment import position
from agent.environment import util as environment_util


class Game(ABC):
    def __init__(self,
                 args: game_args.GameArgs,
                 leader_actions: List[List[gameplay_action.GameplayAction]] = None,
                 expected_sets: List[Tuple[List[card.Card], List[card.Card]]] = None,
                 auto_end_turn: bool = True,
                 verbose: bool = False,
                 check_valid_state: bool = True):
        """Abstract class for games.

        Args:
            args: Arguments for configuring the game.
            leader_actions: Pre-specified actions the leader should take (e.g., when interleaving with sent follower
                actions).
            expected_sets: Sets of cards that should be made (in order) during the game.
            auto_end_turn: Whether turns should be automatically ended when players run out of moves.
            verbose: Whether to log actions taken in the game to the console.
            check_valid_state: Whether to check that expected sets are made.
        """
        self._args: game_args.GameArgs = args
        self._verbose = verbose
        self._check_valid_state = check_valid_state

        # Initialize the environment information as null for now
        self._hexes: List[Tuple[terrain.Terrain, position.Position]] = []
        self._obstacle_positions: Set[position.Position] = set()
        self._objects: List[environment_objects.EnvironmentObject] = []
        self._env_width: int = environment_util.ENVIRONMENT_WIDTH
        self._env_depth: int = environment_util.ENVIRONMENT_DEPTH
        self._current_state_delta: state_delta.StateDelta = None
        self._obstacle_positions: List[position.Position] = []

        # Initialize the game playing logistics
        self._current_turn_index: int = 0
        self._turns_left: int = self._args.get_initial_number_of_turns()
        self._is_leader_turn: bool = True
        self._num_moves_left: int = self._args.get_leader_moves_per_turn()
        self._score: int = 0

        self._instruction_buffer: List[str] = list()

        self._keep_track_of_turns: bool = args.keep_track_of_turns()
        self._auto_end_turn: bool = auto_end_turn

        # Expected sets
        self._expected_sets: List[Tuple[List[card.Card], List[card.Card]]] = copy.deepcopy(expected_sets)
        self._expected_states: List[List[card.Card]] = None
        self._current_state_index: int = 0
        self._current_set_index: int = 0 if expected_sets is not None else None

        # Whether the game is currently in a valid state (i.e., expected cards values)
        self._valid_state: bool = True

        self._leader_actions: List[List[gameplay_action.GameplayAction]] = leader_actions

        self._move_id = 0
        self._num_completed_instructions = 0
        self._turn_id = 0

    @abstractmethod
    def _execute_follower(self, action: agent_actions.AgentAction) -> None:
        pass

    @abstractmethod
    def _execute_leader(self, action: agent_actions.AgentAction) -> None:
        pass

    @abstractmethod
    def _add_cards(self, new_cards: List[card.Card]) -> None:
        pass

    @abstractmethod
    def send_command(self, command: str) -> None:
        pass

    def add_instruction(self, instruction: str):
        """Adds an instruction to the queue."""
        self._instruction_buffer.append(instruction)
        self._move_id += 1
        if self._verbose:
            logging.info('Added instruction: ' + str(instruction))
            logging.info('There are now ' + str(len(self._instruction_buffer)) + ' instructions.')

    def get_instruction_index(self):
        """Gets the current instruction index."""
        return self._num_completed_instructions

    def _execute_leader_actions(self) -> None:
        if self._leader_actions is None:
            raise ValueError('Cannot execute leader actions when none are provided')
        if self._current_turn_index < len(self._leader_actions):
            for action in self._leader_actions[self._current_turn_index]:
                # Stop executing leader actions.
                if not self._valid_state:
                    return

                if isinstance(action, gameplay_action.MovementAction):
                    self.execute_leader_action(action.get_action())
                    if not self._valid_state:
                        break
                elif isinstance(action, gameplay_action.InstructionAction):
                    self.send_command(action.get_instruction())
                    self._instruction_buffer.append(action.get_instruction())
                    if self._verbose:
                        logging.info('Adding instruction ' + str(action.get_instruction()))
            self._current_turn_index += 1
        else:
            if self._verbose:
                logging.info('Not more leader actions to execute')

        if self._verbose:
            logging.info('Done with executing leader actions, so ending the turn')
        self.end_turn()

    def _set_obstacles(self) -> None:
        for hex_terrain, hex_position in self._hexes:
            if hex_terrain in terrain.OBSTACLE_TERRAINS:
                self._obstacle_positions.append(hex_position)
        for obj in self._objects:
            assert obj.get_type() != environment_objects.ObjectType.CARD
            self._obstacle_positions.append(obj.get_position())

    def _check_for_new_set(self, prev_state_delta: state_delta.StateDelta, action: agent_actions.AgentAction,
                           character: environment_objects.ObjectType) -> None:
        """ Checks whether a set was made after the provided state with the action taken."""
        self._current_state_delta = self.get_most_recent_game_info(prev_state_delta, action, character, False)

        # Then check to see if a set was made
        if self._expected_sets is not None:
            new_set: List[card.Card] = state_delta.set_made(prev_state_delta.cards, self._current_state_delta.cards)
            if new_set:
                # Check that this was the expected set
                new_cards: List[card.Card] = []
                if self._current_set_index >= len(self._expected_sets):
                    was_expected_set = False
                else:
                    expected_set: List[card.Card] = self._expected_sets[self._current_set_index][0]
                    new_cards: List[card.Card] = self._expected_sets[self._current_set_index][1]
                    was_expected_set = state_delta.compare_card_states(expected_set, new_set)

                if was_expected_set:
                    self._add_cards(new_cards)
                    self._current_state_delta.cards.extend(new_cards)
                    self._current_set_index += 1
                else:
                    if self._check_valid_state:
                        self._valid_state = False

                    if self._args.generate_new_cards():
                        # Now, generate random new cards...
                        new_generated_cards: List[card.Card] = list()

                        while not state_delta.set_exists(self._current_state_delta.cards + new_generated_cards):
                            # Generate new cards.
                            new_generated_cards = list()
                            for _ in range(3):
                                new_generated_cards.append(card.generate_random_card_properties())

                        # Place the cards
                        updated_generated_cards: List[card.Card] = list()
                        non_obstacle_positions: Set[position.Position] = set()
                        for x in range(environment_util.ENVIRONMENT_DEPTH):
                            for y in range(environment_util.ENVIRONMENT_WIDTH):
                                if position.Position(x, y) not in self._obstacle_positions:
                                    non_obstacle_positions.add(position.Position(x, y))

                        for new_card in new_generated_cards:
                            # Possible locations are all places in the map except those with obstacles, and where other
                            # cards are now.
                            possible_locations: Set[position.Position] = \
                                non_obstacle_positions \
                                - set([current_card.get_position() for current_card in self._current_state_delta.cards])

                            chosen_location: position.Position = random.choice(list(possible_locations))
                            new_card.update_position(chosen_location)

                            # Add the card here now so that it won't place later cards on top of it (unlikely,
                            # but possible)
                            self._current_state_delta.cards.append(new_card)
                            updated_generated_cards.append(new_card)
                        self._add_cards(updated_generated_cards)

    @abstractmethod
    def get_score(self) -> int:
        pass

    @abstractmethod
    def get_game_info(self, force_update: bool = False) -> state_delta.StateDelta:
        pass

    @abstractmethod
    def get_most_recent_game_info(self,
                                  prev_state_delta: state_delta.StateDelta,
                                  action: agent_actions.AgentAction,
                                  character: environment_objects.ObjectType,
                                  need_new_set_cards: bool = False) -> state_delta.StateDelta:
        pass

    def get_hexes(self) -> List[Tuple[terrain.Terrain, position.Position]]:
        return self._hexes

    def get_objects(self) -> List[environment_objects.EnvironmentObject]:
        return self._objects

    def is_leader_turn(self) -> bool:
        return self._is_leader_turn

    def get_num_moves_left(self) -> int:
        return self._num_moves_left

    def valid_state(self) -> bool:
        return self._valid_state

    def get_obstacle_positions(self) -> List[position.Position]:
        return self._obstacle_positions

    def get_remaining_leader_actions(self) -> List[List[gameplay_action.GameplayAction]]:
        """Gets the leader actions remaining in the prespecified leader actions."""
        if self._current_turn_index < len(self._leader_actions):
            return self._leader_actions[self._current_turn_index:]
        return []

    def instruction_buffer_size(self) -> int:
        return len(self._instruction_buffer)

    def get_current_instruction(self) -> str:
        return self._instruction_buffer[0]

    def get_env_width(self) -> int:
        return self._env_width

    def get_env_depth(self) -> int:
        return self._env_depth

    def get_turns_left(self) -> int:
        return self._turns_left

    def get_move_id(self):
        return self._move_id

    def get_turn_index(self):
        return self._turn_id

    def finish_all_leader_actions(self) -> None:
        """Finishes all specified leader actions at once."""
        self._is_leader_turn = True
        while self._current_turn_index < len(self._leader_actions):
            for action in self._leader_actions[self._current_turn_index]:
                if isinstance(action, gameplay_action.MovementAction):
                    self.execute_leader_action(action.get_action())
                if not self._valid_state:
                    return
            self._current_turn_index += 1

    def end_turn(self) -> None:
        """Ends the current player's turn."""
        self._turn_id += 1
        if self._is_leader_turn:
            if self._verbose:
                logging.info('Ending leader turn')
            # If it was the leader's turn, change to the follower's turn.
            self._is_leader_turn = False
            self._num_moves_left = self._args.get_follower_moves_per_turn()

            # But if there aren't any instructions left now, return to the leader's turn.
            if not self._instruction_buffer and \
                    (not self._auto_end_turn or
                     (self._leader_actions is not None and self._current_turn_index < len(self._leader_actions))) and \
                    self._auto_end_turn:
                if self._verbose:
                    logging.info('Automatically ending follower turn because there are no instructions left!')
                self.end_turn()
        else:
            if self._verbose:
                logging.info('Ending follower turn')
            # Only decrease number of turns when the follower has finished.
            self._turns_left -= 1
            self._is_leader_turn = True
            self._num_moves_left = self._args.get_leader_moves_per_turn()

            if self._leader_actions is not None:
                self._execute_leader_actions()

    def reset_state(self,
                    leader_actions: List[List[gameplay_action.GameplayAction]],
                    state: state_delta.StateDelta,
                    num_steps_remaining: int,
                    expected_sets: List[Tuple[List[card.Card], List[card.Card]]],
                    num_instructions: int = 1,
                    expected_states: List[List[card.Card]] = None) -> None:
        """Resets the game state to a specified state."""
        # Reset the internal values in the simulator

        self._expected_states = expected_states
        self._current_state_index: int = 0
        self._current_state_delta = copy.deepcopy(state)

        # The current turn index is wrt. the set of leader actions to take, so reset to zero
        self._current_turn_index: int = 0

        # Reset the number of turns remaining in the game.
        self._turns_left: int = self._args.get_initial_number_of_turns()
        self._instruction_buffer = ['[placeholder]' for _ in range(num_instructions)]

        # Assuming that it's not starting with the leader turn.
        # End turn if it's the leader's turn.
        if self._is_leader_turn:
            self.end_turn()
        self._is_leader_turn: bool = False
        self._num_moves_left: int = num_steps_remaining

        # Set, but do not execute, the leader actions.
        self._leader_actions: List[List[gameplay_action.GameplayAction]] = leader_actions
        self._expected_sets = copy.deepcopy(expected_sets)
        self._current_set_index = 0

        self._valid_state = True

    def _check_if_state_expected(self, card_list: List[card.Card]):
        card_set_same = \
            self._current_state_index < len(self._expected_states) and \
            state_delta.compare_card_states(self._expected_states[self._current_state_index], card_list)
        if not card_set_same:
            # Compare with the next one -- maybe it triggered a card or made a set.
            self._current_state_index += 1

            next_card_set_same = \
                self._current_state_index < len(self._expected_states) \
                and state_delta.compare_card_states(self._expected_states[self._current_state_index], card_list)
            if not next_card_set_same:
                self._valid_state = False

    def execute_follower_action(self, action: agent_actions.AgentAction) -> state_delta.StateDelta:
        if self._verbose:
            logging.info('Executing follower action ' + str(action))
        if action != agent_actions.AgentAction.STOP and len(self._current_state_delta.cards) != 21:
            raise ValueError('There are not 21 cards in the current state!')
        assert isinstance(action, agent_actions.AgentAction)
        if self.is_leader_turn() and self._keep_track_of_turns:
            raise ValueError('Can\'t execute agent action when it\'s the leader\'s turn.')
        if not self._instruction_buffer and self._leader_actions is not None:
            raise ValueError('Should not be able to execute actions when there are '
                             + str(len(self._instruction_buffer))
                             + ' instructions available')

        prev_state_delta: state_delta.StateDelta = copy.deepcopy(self._current_state_delta)

        # Internal execute MUST set the current state delta.
        self._execute_follower(action)

        resulting_state: state_delta.StateDelta = prev_state_delta

        if action != agent_actions.AgentAction.START and action != agent_actions.AgentAction.STOP:
            self._move_id += 1
            self._check_for_new_set(prev_state_delta, action, environment_objects.ObjectType.FOLLOWER)
            resulting_state = copy.deepcopy(self._current_state_delta)

            if self._expected_states:
                # Check that it's in the current state.
                self._check_if_state_expected(resulting_state.cards)

            self._num_moves_left -= 1

            if self._num_moves_left == 0 and self._valid_state and self._auto_end_turn:
                if self._verbose:
                    logging.info('Ending turn because there are no steps left.')
                self.end_turn()
        elif action == agent_actions.AgentAction.STOP:
            self._instruction_buffer = self._instruction_buffer[1:]
            self._num_completed_instructions += 1
            if self._verbose:
                logging.info(str(len(self._instruction_buffer)) + ' in buffer')
            if not self._instruction_buffer and self._auto_end_turn:
                if self._verbose:
                    logging.info('Ending follower turn because there are no instructions left.')
                self.end_turn()

        del prev_state_delta
        return resulting_state

    def execute_leader_action(self, action: agent_actions.AgentAction) -> None:
        if self._verbose:
            logging.info('Executing leader action ' + str(action))
        if len(self._current_state_delta.cards) != 21:
            raise ValueError('There are not 21 cards in the current state!')
        assert isinstance(action, agent_actions.AgentAction)
        if not self.is_leader_turn() and self._keep_track_of_turns:
            raise ValueError('Can\'t execute leader action when it\'s the agent\'s turn.')

        self._move_id += 1

        prev_state_delta: state_delta.StateDelta = copy.deepcopy(self._current_state_delta)

        self._execute_leader(action)

        self._check_for_new_set(prev_state_delta, action, environment_objects.ObjectType.LEADER)

        if self._expected_states:
            self._check_if_state_expected(self._current_state_delta.cards)

        self._num_moves_left -= 1

        if self._num_moves_left == 0 and self._leader_actions is None and self._auto_end_turn:
            self.end_turn()

        del prev_state_delta

