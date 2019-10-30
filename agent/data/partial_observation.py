"""Maintains information about a partial observation the follower has throughout a game."""

import pickle
from typing import Dict, List, Optional, Set, Tuple

from agent.environment import agent
from agent.environment import card
from agent.environment import position
from agent.environment import rotation
from agent.environment import state_delta

# To start, load the dictionary mapping positions/rotations to visible positions.
with open('agent/preprocessed/position_visibility.pkl', 'rb') as infile:
    VISIBILITY_MAP: Dict[Tuple[position.Position, rotation.Rotation], position.Position] = pickle.load(infile)


class PartialObservation:
    def __init__(self,
                 observed_state_delta: state_delta.StateDelta,
                 observed_positions: Set[position.Position]):
        """Sets the properties of this observation.

        Args:
            observed_state_delta: A state delta representing the agent's current belief about the state of the board,
                including its own position (always up-to-date), a belief about the leader's position (changes only when
                the leader is observed again), and beliefs about the cards on the board. NOTE: There might be more than
                21 cards in the list of cards, because the agent might not be able to determine which cards have been
                removed from the board while they were not observed.
            observed_positions: Set[position.Position]: All positions that the follower has seen throughout
                the entire game (not necessarily ones it observes now).
        """
        self._observed_state_delta: state_delta.StateDelta = observed_state_delta
        self._observed_positions: Set[position.Position] = observed_positions

    def get_follower(self) -> agent.Agent:
        return self._observed_state_delta.follower

    def get_leader(self) -> Optional[agent.Agent]:
        # Returns the leader of the observation -- may be None if the leader hasn't been seen in the game yet.
        return self._observed_state_delta.leader

    def get_card_beliefs(self) -> List[card.Card]:
        return self._observed_state_delta.cards

    def observed_positions(self) -> Set[position.Position]:
        """Returns all positions that the follower has seen throughout the entire game."""
        return self._observed_positions

    def get_observed_state_delta(self) -> state_delta.StateDelta:
        return self._observed_state_delta


def create_first_partial_observation(complete_state_delta: state_delta.StateDelta) -> PartialObservation:
    initial_follower = complete_state_delta.follower

    # Figure out which hexes can be seen from this configuration
    visible_positions: List[position.Position] = VISIBILITY_MAP[(initial_follower.get_position(),
                                                                 initial_follower.get_rotation())]

    # Construct a state delta with the dynamic information
    leader = complete_state_delta.leader
    if leader.get_position() not in visible_positions:
        leader = None

    card_beliefs: List[card.Card] = list()
    for state_card in complete_state_delta.cards:
        if state_card.get_position() in visible_positions:
            # Update the selection: invalid sets can't be determined!
            selection: card.CardSelection = state_card.get_selection()
            if selection == card.CardSelection.INVALID:
                selection = card.CardSelection.SELECTED

            new_card = card.Card(state_card.get_position(),
                                 card.CARD_ROTATION,
                                 state_card.get_color(),
                                 state_card.get_count(),
                                 state_card.get_shape(),
                                 selection)
            card_beliefs.append(new_card)

    return PartialObservation(state_delta.StateDelta(leader, initial_follower, card_beliefs),
                              set(visible_positions))


def update_observation(current_observation: PartialObservation,
                       complete_state_delta: state_delta.StateDelta) -> PartialObservation:
    """Given a current observation, this creates a new observation after the follower moves."""
    new_follower: agent.Agent = complete_state_delta.follower

    now_visible_positions: List[position.Position] = VISIBILITY_MAP[(new_follower.get_position(),
                                                                     new_follower.get_rotation())]

    # These positions are all the ones that have been previously observed plus the new observed ones.
    all_observed_positions = set(now_visible_positions) | current_observation.observed_positions()

    # Leader: if it's now in view, update it, otherwise it will stay where it was.
    current_leader: agent.Agent = complete_state_delta.leader
    if current_leader.get_position() not in now_visible_positions:
        current_leader = current_observation.get_leader()

    # Cards:

    # First, make sure everything in view is correct.
    actual_cards = complete_state_delta.cards
    actual_card_dict: Dict[position.Position, card.Card] = dict()
    for actual_card in actual_cards:
        actual_card_dict[actual_card.get_position()] = actual_card

    new_card_beliefs = list()
    for observed_position in now_visible_positions:
        # If the position contains a now-visible card, add it.
        if observed_position in actual_card_dict:
            actual_card = actual_card_dict[observed_position]
            selection: card.CardSelection = actual_card.get_selection()
            if selection == card.CardSelection.INVALID:
                selection = card.CardSelection.SELECTED

            new_card = card.Card(actual_card.get_position(),
                                 card.CARD_ROTATION,
                                 actual_card.get_color(),
                                 actual_card.get_count(),
                                 actual_card.get_shape(),
                                 selection)

            new_card_beliefs.append(new_card)

    # Then add all the cards that were previously observed but no longer observed.
    previously_observed_cards = current_observation.get_card_beliefs()

    for card_belief in previously_observed_cards:
        if card_belief.get_position() not in now_visible_positions:
            new_card_beliefs.append(card_belief)

    return PartialObservation(state_delta.StateDelta(current_leader, new_follower, new_card_beliefs),
                              all_observed_positions)
