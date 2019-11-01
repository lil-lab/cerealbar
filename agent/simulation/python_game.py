from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING

from agent.environment import agent
from agent.environment import agent_actions
from agent.environment import card
from agent.environment import environment_objects
from agent.environment import state_delta
from agent.simulation import game
from agent.simulation import planner

if TYPE_CHECKING:
    from agent.config import game_args
    from agent.data import gameplay_action
    from agent.environment import position
    from agent.environment import terrain
    from typing import List, Tuple


class PythonGame(game.Game):
    def __init__(self,
                 args: game_args.GameArgs,
                 hexes: List[Tuple[terrain.Terrain, position.Position]],
                 env_objects: List[environment_objects.EnvironmentObject],
                 initial_state_delta: state_delta.StateDelta,
                 leader_actions: List[List[gameplay_action.GameplayAction]] = None,
                 expected_sets: List[Tuple[List[card.Card], List[card.Card]]] = None,
                 auto_end_turn: bool = True,
                 verbose: bool = False,
                 check_valid_state: bool = True):
        super(PythonGame, self).__init__(args, leader_actions, expected_sets, auto_end_turn, verbose, check_valid_state)

        self._hexes: List[Tuple[terrain.Terrain, position.Position]] = hexes
        self._objects: List[environment_objects.EnvironmentObject] = env_objects
        self._set_obstacles()
        self._current_state_delta: state_delta.StateDelta = copy.deepcopy(initial_state_delta)
        self._score: int = 0

        self._selected_cards: List[card.Card] = []
        for current_card in self._current_state_delta.cards:
            if current_card.get_selection() != card.CardSelection.UNSELECTED:
                self._selected_cards.append(current_card)

        if self._leader_actions:
            self._execute_leader_actions()

    def _detect_invalid_set(self,
                            selected_shapes: List[card.CardShape],
                            selected_colors: List[card.CardColor],
                            selected_counts: List[card.CardCount]):
        # It's invalid if there are multiple values, or more than 3 cards; i.e., the set is not the same size
        # as the list.
        invalid_selection: bool = len(self._selected_cards) > 3 \
                                  or len(set(selected_colors)) != len(selected_colors) \
                                  or len(set(selected_counts)) != len(selected_counts) \
                                  or len(set(selected_shapes)) != len(selected_shapes)

        # If invalid, then just update the selection of all of the cards.
        if invalid_selection:
            for current_card in self._current_state_delta.cards:
                if current_card.get_selection() == card.CardSelection.SELECTED:
                    current_card.update_selection(card.CardSelection.INVALID)
        else:
            # If valid now, then update so that the state is just selected.
            for current_card in self._current_state_delta.cards:
                if current_card.get_selection() == card.CardSelection.INVALID:
                    current_card.update_selection(card.CardSelection.SELECTED)

    def _update_card_with_move(self, new_position: position.Position):
        # First, if it stepped on any cards, then select or unselect the card
        changed_card: bool = False
        for current_card in self._current_state_delta.cards:
            if current_card.get_position() == new_position:
                if self._verbose:
                    logging.info('Stepped on card ' + str(current_card))
                if current_card.get_selection() == card.CardSelection.UNSELECTED:
                    current_card.update_selection(card.CardSelection.SELECTED)
                    self._selected_cards.append(current_card)
                else:
                    current_card.update_selection(card.CardSelection.UNSELECTED)
                    if current_card not in self._selected_cards:
                        raise ValueError('Card ' + str(current_card) + ' is selected but not in selected cards set!')
                    self._selected_cards.remove(current_card)
                changed_card = True

        if changed_card:
            # Check whether a set was made, or update the selection of the selected cards.
            selected_colors: List[card.CardColor] = [current_card.get_color() for current_card in self._selected_cards]
            selected_counts: List[card.CardCount] = [current_card.get_count() for current_card in self._selected_cards]
            selected_shapes: List[card.CardShape] = [current_card.get_shape() for current_card in self._selected_cards]

            made_set: bool = (len(set(selected_colors)) == 3
                              and len(set(selected_counts)) == 3
                              and len(set(selected_shapes)) == 3
                              and len(self._selected_cards) == 3)

            # If made a set, then remove the cards. Don't add in cards -- the superclass will handle it.
            if made_set:
                self._score += 1
                prev_len: int = len(self._current_state_delta.cards)
                for selected_card in self._selected_cards:
                    self._current_state_delta.cards.remove(selected_card)
                if len(self._current_state_delta.cards) != prev_len - 3:
                    raise ValueError('Should have removed three cards from the current state delta!')

                self._selected_cards = []

            else:
                self._detect_invalid_set(selected_shapes, selected_colors, selected_counts)

    def _execute_follower(self, action: agent_actions.AgentAction):
        follower: agent.Agent = self._current_state_delta.follower

        new_position, new_rotation = planner.get_new_player_orientation(follower, action, self._obstacle_positions)

        # Set the follower's state
        self._current_state_delta.follower = agent.Agent(environment_objects.ObjectType.FOLLOWER, new_position,
                                                         new_rotation)

        if action in {agent_actions.AgentAction.MB, agent_actions.AgentAction.MF}:
            self._update_card_with_move(new_position)

    def _execute_leader(self, action: agent_actions.AgentAction):
        leader: agent.Agent = self._current_state_delta.leader
        new_position, new_rotation = planner.get_new_player_orientation(leader, action, self._obstacle_positions)

        # Set the leader's state
        self._current_state_delta.leader = agent.Agent(environment_objects.ObjectType.LEADER, new_position,
                                                       new_rotation)

        if action in {agent_actions.AgentAction.MB, agent_actions.AgentAction.MF}:
            self._update_card_with_move(new_position)

    def send_command(self, command: str):
        pass

    def _add_cards(self, new_cards: List[card.Card]):
        raise NotImplementedError

    def get_score(self) -> int:
        raise NotImplementedError

    def get_game_info(self, force_update: bool = False) -> state_delta.StateDelta:
        return self._current_state_delta

    def get_most_recent_game_info(self,
                                  prev_state_delta: state_delta.StateDelta,
                                  action: agent_actions.AgentAction,
                                  character: environment_objects.ObjectType,
                                  need_new_set_cards: bool = False) -> state_delta.StateDelta:
        # Doesn't need to be force-updated, but just assert that it's correct
        outdated, outdated_reason = state_delta.outdated_info(prev_state_delta,
                                                              self._current_state_delta,
                                                              character,
                                                              action,
                                                              need_new_set_cards)
        if outdated:
            raise ValueError('State delta is outdated: Reason: ' + outdated_reason)

        return self._current_state_delta
