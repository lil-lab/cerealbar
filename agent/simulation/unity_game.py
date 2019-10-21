"""Interface for the Unity game."""
from __future__ import annotations

import json
import logging
import random
import time
from typing import TYPE_CHECKING

from agent.config import game_args
from agent.data import gameplay_action
from agent.environment import agent, state_delta
from agent.environment import agent_actions
from agent.environment import card
from agent.environment import environment_objects
from agent.environment import position
from agent.environment import terrain
from agent.environment import util as environment_util
from agent.simulation import game
from agent.simulation import server

if TYPE_CHECKING:
    from typing import List, Tuple, Dict, Any

MAX_SEED: int = 100000000
MAX_NUM_ATTEMPTS: int = 10


class UnityGame(game.Game):
    """Game class maintains the connection to the Unity game and allows executing
    actions and getting environment information."""

    def __init__(self,
                 args: game_args.GameArgs,
                 connection: server.ServerSocket,
                 seed: int = -1,
                 number_of_cards: int = 21,
                 auto_end_turn: bool = True,
                 leader_actions: List[List[gameplay_action.GameplayAction]] = None,
                 expected_sets: List[Tuple[List[card.Card], List[card.Card]]] = None):
        """Starts a Unity game.

        Args:
            args: Arguments for configuring the game.
            connection: Connection to the standalone.
            seed: Seed for the game.
            number_of_cards: The number of cards to put on the board.
            auto_end_turn: Whether turns should be automatically ended when players run out of moves.
            leader_actions: Pre-specified actions the leader should take (e.g., when interleaving with sent follower
                actions).
            expected_sets: Sets of cards that should be made (in order) during the game.
        """
        # Initialize the superclass, setting everything as null
        super(UnityGame, self).__init__(args, leader_actions, expected_sets, auto_end_turn=auto_end_turn)

        # Then start up the game (maybe compute a seed if one wasn't given)
        self._connection: server.ServerSocket = connection

        # Randomly set the seed if not specified.
        self._seed: int = random.randint(0, MAX_SEED) if seed < 0 else seed

        self._num_cards: int = number_of_cards

        # Start a new game and set the environment state.
        self._connection.start_new_game(self._seed, self._num_cards)
        self._set_environment_info(json.loads(self._connection.receive_data().decode('utf-8')))
        self._set_obstacles()

        # Execute the leader actions for their first turn if they were provided.
        if self._leader_actions:
            self._execute_leader_actions()

    def _execute_follower(self, action: agent_actions.AgentAction) -> None:
        """ Executes the specified action for the follower in the environment.

        Inputs:
            action (str): The action that the follower should take.

        Returns:
            Whether it was still the Follower's turn when the action finished.

        Raises:
            ValueError if it's not the follower's turn.
        """
        time.sleep(self._args.get_action_delay())

        if action != agent_actions.AgentAction.START and action != agent_actions.AgentAction.STOP:
            self._connection.send_data('agent, ' + str(action))

            self._current_state_delta = state_delta.state_delta_from_dict(
                json.loads(self._connection.receive_data().decode('utf-8')))

        if action == agent_actions.AgentAction.STOP:
            # The STOP action maps to finishing a command for the follower.
            self._connection.send_data('finishcommand')
            _ = self._connection.receive_data()

    def _execute_leader(self, action: agent_actions.AgentAction) -> None:
        """ Executes an action taken by the leader.

        Input:
            action (agent_actions.AgentAction): The action taken by the leader.

        Returns:
            Whether the action increased the score (collected a card).

        Raises:
            ValueError if it's not the leader's turn.
        """
        time.sleep(self._args.get_action_delay())

        self._connection.send_data('human, ' + str(action))
        self._current_state_delta = state_delta.state_delta_from_dict(
            json.loads(self._connection.receive_data().decode('utf-8')))

    def _set_environment_info(self, dictionary_representation: Dict[str, Any]) -> None:
        if self._hexes:
            raise ValueError('Already set the hex information.')
        for hex_cell in dictionary_representation['hexCellInfo']:
            hex_position: position.Position = position.v3_pos_to_position(eval(hex_cell['posV3']),
                                                                          environment_util.HEX_WIDTH,
                                                                          environment_util.HEX_DEPTH)
            hex_terrain: terrain.Terrain = terrain.cell_name_to_terrain(hex_cell['lType'], float(eval(hex_cell[
                                                                                                          'posV3'])[1]))

            self._hexes.append((hex_terrain, hex_position))

        card_list: List[card.Card] = \
            environment_util.interpret_card_info(dictionary_representation['cardInfo'],
                                                 environment_util.HEX_WIDTH,
                                                 environment_util.HEX_DEPTH)
        leader: agent.Agent = None
        follower: agent.Agent = None

        for environment_object in dictionary_representation['propPlacementInfo']:
            prop_name: str = environment_object['pName']
            object_position: position.Position = position.v3_pos_to_position(eval(environment_object['posV3']),
                                                                             environment_util.HEX_WIDTH,
                                                                             environment_util.HEX_DEPTH)

            constructed_object = environment_util.construct_object(prop_name,
                                                                   object_position,
                                                                   eval(environment_object['rotV3']),
                                                                   card_list)
            if not isinstance(constructed_object, agent.Agent):
                self._objects.append(constructed_object)
            elif constructed_object.get_type() == environment_objects.ObjectType.LEADER:
                leader = constructed_object
            elif constructed_object.get_type() == environment_objects.ObjectType.FOLLOWER:
                follower = constructed_object
            else:
                raise ValueError('Unrecognized object type with Agent object: %r' % constructed_object.get_type())

        if not leader or not follower:
            raise ValueError('Didn\'t find leader or follower in the object list.')

        self._current_state_delta: state_delta.StateDelta = state_delta.StateDelta(leader, follower, card_list)

    def _add_cards(self, new_cards: List[card.Card]) -> None:
        self._connection.send_data('newcards,' + json.dumps({'cards': [new_card.to_dict() for new_card in new_cards]}))
        _ = self._connection.receive_data()

    def reset_state(self,
                    leader_actions: List[List[gameplay_action.GameplayAction]],
                    state: state_delta.StateDelta,
                    num_steps_remaining: int,
                    expected_sets: List[Tuple[List[card.Card], List[card.Card]]],
                    allow_exceptions: bool = False,
                    num_instructions: int = 1,
                    expected_states: List[List[card.Card]] = None) -> None:
        """ Resets the state of the game board to a new state delta, and resets the gameplay. Assumes that the first
        turn is the Follower's, and that the state passed in represents the world state after the last leader's
        action (or any actions the follower executed before starting on this instruction.)

        Inputs:
            leader_actions: List[List[agent_actions.AgentAction]]. The sequence of actions for each turn completed by
                this leader during and after this instruction
            state: StateDelta. The state of the world to reset, including the configurations of both players and the
                cards.
            num_steps_remaining: int. The number of steps remaining in the current turn.
            expected_sets: The new expected sets to be made.
            num_instructions: The number of instructions in the queue when the game is reset.
            allow_exceptions: Whether exceptions should be raised or ignored.
            expected_states: The expected card states.
        """
        super(UnityGame, self).reset_state(leader_actions,
                                           state,
                                           num_steps_remaining,
                                           expected_sets,
                                           num_instructions,
                                           expected_states=expected_states)

        # Update the Unity game to reflect the new info, and make sure that it was actually reset.
        self._connection.set_game_state(state)

        new_info: state_delta.StateDelta = self.get_game_info(force_update=True)

        if self._current_state_delta != new_info and not allow_exceptions:
            logging.error('Player information:')
            if self._current_state_delta.leader != new_info.leader:
                print('%r vs. %r' % (self._current_state_delta.leader, new_info.leader))
            if self._current_state_delta.follower != new_info.follower:
                print('%r vs. %r' % (self._current_state_delta.follower, new_info.follower))
            logging.error('Card information:')
            for card1, card2 in zip(sorted(self._current_state_delta.cards), sorted(new_info.cards)):
                if card1 != card2 or card1.get_selection() != card2.get_selection():
                    print('%r vs. %r' % (card1, card2))
            raise ValueError('Did not properly reset the state')

    def get_score(self) -> int:
        """Gets the game's score."""
        self._connection.send_data('score')
        return int(self._connection.receive_data())

    def send_command(self, command: str) -> None:
        """ Sends a command to the game to display it in the interface. """
        self._connection.send_data('grammer, ' + command)

        _ = self._connection.receive_data()

    def send_goal_probabilities(self, probabilities) -> bool:
        """Sends distributions over hexes to the Unity game for display."""
        str_val = json.dumps({'hexInfo': probabilities})

        # Don't send the message if it's too long.
        if len(str_val) > 4081:
            return False

        self._connection.send_data('goaldist,' + str_val)
        _ = self._connection.receive_data()

        return True

    def send_trajectory_distribution(self, distribution) -> bool:
        """Sends distribution over hexes to the Unity game for display."""
        str_val = json.dumps({'hexInfo': distribution})

        # Don't send the message if it's too long.
        if len(str_val) > 4081:
            return False

        self._connection.send_data('trajdist,' + str_val)
        _ = self._connection.receive_data()

        return True

    def send_obstacle_probabilities(self, probabilities) -> bool:
        """Sends probabilities over hexes to the Unity game for display."""
        str_val = json.dumps({'hexInfo': probabilities})

        # Don't send the message if it's too long.
        if len(str_val) > 4081:
            return False

        self._connection.send_data('obsdist,' + str_val)
        _ = self._connection.receive_data()

        return True

    def send_avoid_probabilities(self, probabilities) -> bool:
        """Sends probabilities over hexes to the Unity game for display."""
        str_val = json.dumps({'hexInfo': probabilities})

        # Don't send the message if it's too long.
        if len(str_val) > 4081:
            return False

        self._connection.send_data('avoiddist,' + str_val)
        _ = self._connection.receive_data()

        return True

    def get_game_info(self, force_update: bool = False) -> state_delta.StateDelta:
        """ Queries the game for all of the information on the board."""
        if force_update or self._current_state_delta is None:
            self._connection.send_data('info')

            data: bytes = self._connection.receive_data()

            # TODO: Should this also set the current state delta?
            return state_delta.state_delta_from_dict(json.loads(data.decode('utf-8')))

        return self._current_state_delta

    def end_turn(self) -> None:
        """Ends the current player's turn."""
        self._connection.send_data('turn')
        _ = self._connection.receive_data()

        return super(UnityGame, self).end_turn()

    def get_most_recent_game_info(self,
                                  previous_state_delta: state_delta.StateDelta,
                                  action: agent_actions.AgentAction,
                                  character: environment_objects.ObjectType,
                                  need_new_set_cards: bool = False) -> state_delta.StateDelta:
        """Gets game information with extra checks to make sure the information is recent according to the agent
        action taken.

        Args:
            previous_state_delta: The previous state delta before the action was taken.
            action: An action taken by an agent.
            character: The action that was taken by the agent.
            need_new_set_cards: Whether the new state must contain new cards if a set is made.
        """
        new_game_state: state_delta.StateDelta = self.get_game_info()

        outdated: bool = True

        num_attempts: int = 0
        reason: str = ''
        while outdated and num_attempts < MAX_NUM_ATTEMPTS:
            num_attempts += 1

            outdated, reason = state_delta.outdated_info(previous_state_delta, new_game_state, character, action,
                                                         need_new_set_cards)

            if outdated:
                new_game_state: state_delta.StateDelta = self.get_game_info(force_update=True)

        if outdated:
            raise ValueError('Could not retrieve updated info. Reason: ' + reason)

        return new_game_state
