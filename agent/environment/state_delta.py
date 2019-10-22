"""Contains the StateDelta class for keeping track of differences between game states after taking actions."""
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

from agent.environment import agent
from agent.environment import agent_actions
from agent.environment import card
from agent.environment import environment_objects
from agent.environment import position
from agent.environment import rotation
from agent.environment import util as environment_util


@dataclass
class StateDelta:
    """ Saves the information about a state change, which only includes player info and card info."""
    leader: agent.Agent
    follower: agent.Agent
    cards: List[card.Card]

    def to_dict(self):
        # Leader and follower information: string to integer for rotation and x/y pos
        leader_info: Dict[str, int] = {'rot': int(self.leader.get_rotation()),
                                       'pos': [self.leader.get_position().x, self.leader.get_position().y]}
        follower_info: Dict[str, int] = {'rot': int(self.follower.get_rotation()),
                                         'pos': [self.follower.get_position().x, self.follower.get_position().y]}

        # card.Card info is a list of dictionaries mapping from string to string
        cards_info: List[Dict[str, Any]] = []
        for delta_card in self.cards:
            cards_info.append(delta_card.to_dict())

        # Top-level dictionary: string to JSON-encoded string
        final_rep: Dict[str, Any] = dict()
        final_rep['lead'] = leader_info
        final_rep['follow'] = follower_info
        final_rep['cards'] = cards_info

        return final_rep

    def __eq__(self, other) -> bool:
        leader_same: bool = self.leader.get_position() == other.leader.get_position() \
                            and self.leader.get_rotation() == other.leader.get_rotation()
        follower_same: bool = (self.follower.get_position() == other.follower.get_position()
                               and self.follower.get_rotation() == other.follower.get_rotation())
        cards_same = card_states_equal(self.cards, other.cards)

        return leader_same and cards_same and follower_same


def set_exists(cards: List[card.Card]) -> bool:
    """Returns whether there is a possible set in the list of cards."""
    if len(cards) != 21:
        return False
    onecards: List[card.Card] = [test_card for test_card in cards if test_card.get_count() == card.CardCount.ONE]
    twocards: List[card.Card] = [test_card for test_card in cards if test_card.get_count() == card.CardCount.TWO]
    threecards: List[card.Card] = [test_card for test_card in cards if test_card.get_count() == card.CardCount.THREE]

    for card1 in onecards:
        for card2 in twocards:
            for card3 in threecards:
                if len({card1.get_shape(), card2.get_shape(), card3.get_shape()}) == 3 and \
                        len({card1.get_count(), card2.get_count(), card3.get_count()}) == 3:
                    return True
    return False


def set_made(prev_cards: List[card.Card], current_cards: List[card.Card]) -> List[card.Card]:
    """Returns the set of cards that were cleared from prev_cards (i.e., don't exist in current_cards)."""
    # Returns the cards missing from prev_state
    if len(current_cards) == len(prev_cards) - 3:
        # A set was made
        # Find the cards that are missing
        detected_set: List[card.Card] = card_list_difference(prev_cards, current_cards)
        if not len(detected_set) == 3:
            raise ValueError('Detected three fewer cards, but got the following cards different: '
                             + '\n'.join([str(detected_card) for detected_card in detected_set]))
        return detected_set

    elif len(current_cards) == len(prev_cards):
        for card1, card2 in zip(sorted(current_cards), sorted(prev_cards)):
            if card1 != card2 and card1.get_selection() != card2.get_selection():
                raise ValueError('Got the same number of cards, but cards did not match: \n %r vs. %r' % (card1, card2))
    else:
        raise ValueError('Not a 3-card difference between card sets: %r vs. %r' % (len(current_cards), len(prev_cards)))

    return []


def card_list_difference(cards1: List[card.Card], cards2: List[card.Card]) -> List[card.Card]:
    """Returns the cards that were in one set but not in another."""
    in_cards2: List[bool] = []
    for card1 in cards1:
        remained: bool = False
        for card2 in cards2:
            if card1 == card2:
                remained = True
                break
        in_cards2.append(not remained)
    return [test_card for i, test_card in enumerate(cards1) if in_cards2[i]]


def card_states_equal(card_list_1: List[card.Card], card_list_2: List[card.Card]) -> bool:
    """Compares lists of cards and returns whether they are the same."""
    if len(card_list_1) != len(card_list_2):
        return False
    for card1, card2 in zip(sorted(card_list_1), sorted(card_list_2)):
        if card1 != card2 or card1.get_selection() != card2.get_selection():
            return False
    return True


def state_delta_from_dict(dict_rep: Dict) -> StateDelta:
    """Creates a StateDelta from a specified dictionary representation."""
    leader: agent.Agent = agent.Agent(agent_type=environment_objects.ObjectType.LEADER,
                                      agent_position=position.v3_pos_to_position(
                                          eval(dict_rep['leader']['position']),
                                          environment_util.HEX_WIDTH,
                                          environment_util.HEX_DEPTH),
                                      agent_rotation=rotation.degree_to_rotation(
                                          int(eval(dict_rep['leader']['rotation'])[1])))
    follower: agent.Agent = agent.Agent(agent_type=environment_objects.ObjectType.FOLLOWER,
                                        agent_position=position.v3_pos_to_position(
                                            eval(dict_rep['follower']['position']),
                                            environment_util.HEX_WIDTH,
                                            environment_util.HEX_DEPTH),
                                        agent_rotation=rotation.degree_to_rotation(
                                            int(eval(dict_rep['follower']['rotation'])[1])))
    card_list: List[card.Card] = environment_util.interpret_card_info(dict_rep['cards'], environment_util.HEX_WIDTH,
                                                                      environment_util.HEX_DEPTH, False)

    return StateDelta(leader, follower, card_list)


def outdated_info(previous_state_delta: StateDelta,
                  new_state_delta: StateDelta,
                  character: environment_objects.ObjectType,
                  action: agent_actions.AgentAction,
                  need_new_set_cards: bool = False) -> Tuple[bool, str]:
    """Checks whether the new state delta contains outdated information according to the action taken in the previous
    state delta.

    Args:
        previous_state_delta: The previous state.
        new_state_delta: The current state to check.
        character: The character that took an action.
        action: The action taken.
        need_new_set_cards: Whether the new state must contain new cards if a set is made.
    """
    prev_leader_position: position.Position = previous_state_delta.leader.get_position()
    prev_follower_position: position.Position = previous_state_delta.follower.get_position()
    prev_leader_rotation: rotation.Rotation = previous_state_delta.leader.get_rotation()
    prev_follower_rotation: rotation.Rotation = previous_state_delta.follower.get_rotation()

    new_leader_position: position.Position = new_state_delta.leader.get_position()
    new_follower_position: position.Position = new_state_delta.follower.get_position()
    new_leader_rotation: rotation.Rotation = new_state_delta.leader.get_rotation()
    new_follower_rotation: rotation.Rotation = new_state_delta.follower.get_rotation()

    # Get the leader and follower positions changing
    leader_same_position: bool = prev_leader_position == new_leader_position
    leader_same_rotation: bool = prev_leader_rotation == new_leader_rotation
    follower_same_position: bool = prev_follower_position == new_follower_position
    follower_same_rotation: bool = prev_follower_rotation == new_follower_rotation

    # Get the cards that were different between the two sets
    previous_cards: List[card.Card] = previous_state_delta.cards
    new_cards: List[card.Card] = new_state_delta.cards
    removed_cards: List[card.Card] = card_list_difference(previous_cards, new_cards)
    added_cards: List[card.Card] = card_list_difference(new_cards, previous_cards)

    correct_player_config: bool = True
    correct_card_config: bool = True
    reason: str = 'For agent %r moving %r\n' % (character, action)

    if action in {agent_actions.AgentAction.MF, agent_actions.AgentAction.MB}:
        # Need to check the position and make sure rotation is the same.
        if character == environment_objects.ObjectType.LEADER:
            correct_player_config = not leader_same_position and leader_same_rotation \
                                    and follower_same_position and follower_same_rotation
            if not correct_player_config:
                reason += 'Leader position should change; got leader position: %r; leader rotation: %r; follower ' \
                          'position: %r; follower rotation: %r' % (leader_same_position, leader_same_rotation,
                                                                   follower_same_position, follower_same_rotation)
            player_position: position.Position = new_leader_position
        else:
            correct_player_config = leader_same_position and leader_same_rotation \
                                    and not follower_same_position and follower_same_rotation
            if not correct_player_config:
                reason += 'Follower position should change; got leader position: %r; leader rotation: %r; follower ' \
                          'position: %r; follower rotation: %r' % (leader_same_position, leader_same_rotation,
                                                                   follower_same_position, follower_same_rotation)
            player_position: position.Position = new_follower_position

        # Now check to make sure that the cards changed appropriately
        # First, find what card they stepped on (if any)
        stepped_on_card: card.Card = None
        for previous_card in previous_cards:
            if previous_card.get_position() == player_position:
                stepped_on_card = previous_card
                break
        if stepped_on_card:
            # First, determine whether a set should have been made with the previous set of cards
            selected_cards: List[card.Card] = []
            for previous_card in previous_cards:
                if previous_card.get_selection() != card.CardSelection.UNSELECTED:
                    selected_cards.append(previous_card)
            if stepped_on_card in selected_cards:
                # If it was already selected, remove it
                selected_cards.remove(stepped_on_card)
            else:
                # Otherwise, add it -- it's selected now
                selected_cards.append(stepped_on_card)

            if (len(selected_cards) == 3 and len(set([selected_card.get_count() for selected_card in selected_cards]))
                    == 3 and
                    len(set([selected_card.get_color() for selected_card in selected_cards])) == 3 and
                    len(set([selected_card.get_shape() for selected_card in selected_cards])) == 3):
                # Made a set! Make sure that (1) the cards that were removed were the ones comprising the set,
                # and there were three new cards added.
                removed_correct_cards = card_states_equal(selected_cards, removed_cards)

                correct_card_config = removed_correct_cards
                if need_new_set_cards:
                    correct_card_config = correct_card_config and len(added_cards) == 3
                if not correct_card_config:
                    reason += 'Should have made a set, but got the following cards:\ndetected set:\n' \
                              + '\n'.join([str(selected_card) for selected_card in sorted(selected_cards)]) \
                              + '\nUnity removed cards:\n' \
                              + '\n'.join([str(removed_card) for removed_card in sorted(removed_cards)]) \
                              + '\nUnity added cards:\n' + '\n'.join([str(added_card) for added_card in added_cards]) \
                              + '\n'
            else:
                # Make sure that all of the cards are the same, except that the selection of the stepped-on card
                # has changed.
                same_cards: bool = True
                different_selection: bool = None
                for card1, card2 in zip(sorted(previous_cards), sorted(new_cards)):
                    if card1 != card2:
                        same_cards = False
                        reason += 'Agent stepped onto card that did not make a set, but cards changed: %r vs. %r\n' % (
                            card1, card2)
                        break
                    if card1 == stepped_on_card:
                        different_selection = card1.get_selection() != card2.get_selection()

                correct_card_config = not removed_cards and not added_cards and same_cards and different_selection
                if not correct_card_config:
                    reason += 'Should not have made a set; found %r removed cards and %r aded cards, and selection ' \
                              'between selected card changed: %r' % (len(removed_cards),
                                                                     len(added_cards),
                                                                     different_selection)
        else:
            # Make sure that no cards changed
            correct_card_config = True
            for card1, card2 in zip(sorted(previous_cards), sorted(new_cards)):
                if card1 != card2 or card1.get_selection() != card2.get_selection():
                    correct_card_config = False
                    reason += 'Agent did not step on a card but cards changed from last time: %r vs. %r\n' % (card1,
                                                                                                              card2)
                    break

    elif action in {agent_actions.AgentAction.RR, agent_actions.AgentAction.RL}:
        # Need to make sure the rotation changed but the position stayed the same.
        if character == environment_objects.ObjectType.LEADER:
            correct_player_config = leader_same_position and not leader_same_rotation \
                                    and follower_same_position and follower_same_rotation
            if not correct_player_config:
                reason += 'Leader rotation should change; got leader position: %r; leader rotation: %r; follower ' \
                          'position: %r; follower rotation: %r' % (leader_same_position, leader_same_rotation,
                                                                   follower_same_position, follower_same_rotation)
        else:
            correct_player_config = leader_same_position and leader_same_rotation \
                                    and follower_same_position and not follower_same_rotation
            if not correct_player_config:
                reason += 'Follower rotation should change; got leader position: %r; leader rotation: %r; follower ' \
                          'position: %r; follower rotation: %r' % (leader_same_position, leader_same_rotation,
                                                                   follower_same_position, follower_same_rotation)

        # Make sure that the cards' values did not change
        correct_card_config = True
        for card1, card2 in zip(sorted(previous_cards), sorted(new_cards)):
            if card1 != card2 or card1.get_selection() != card2.get_selection():
                correct_card_config = False
                reason += 'Agent rotated but cards changed from last time: %r vs. %r' % (card1, card2)
                break

    outdated = not correct_player_config or not correct_card_config
    return outdated, reason
