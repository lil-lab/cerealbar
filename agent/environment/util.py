"""Contains utilities for creating and using the environment.

Functions:
    interpret_card_info: Maps from a dictionary of raw card representations to a list of Card objects.
"""

from typing import List, Any, Tuple, Set

from agent.environment import agent
from agent.environment import card
from agent.environment import environment_objects
from agent.environment import hut
from agent.environment import plant
from agent.environment import position
from agent.environment import rotation
from agent.environment import structures
from agent.environment import tree

# The size of the hexes in Unity.
HEX_WIDTH: float = 17.321
HEX_DEPTH: float = 15.

# The number of hexes (width and depth) in the Unity game.
ENVIRONMENT_WIDTH: int = 25
ENVIRONMENT_DEPTH: int = 25


def interpret_card_info(raw_dict: List[Any],
                        hex_width: float,
                        hex_depth: float,
                        dict_format=True) -> List[card.Card]:
    """ Constructs a list of dictionaries, interpreting the card information and decides whether the currently selected
        set is valid.

    Inputs:
        raw_dict (List[Dict[str, Any]]): The raw card information dictionary from Unity.
        hex_width (float): The width of the hexes in the environment.
        hex_depth (float): The depth of the hexes in the environment.
        dict_format (bool): Whether the card representation is in a dictionary or a string form.

    Returns
        A list of dictionaries representing all of the cards.

    Raises:
        ValueError, if only one card is invalid.
    """
    card_info: List[card.Card] = []
    for card_rep in raw_dict:
        # Can assume that all cards from the initial info have the correct rotation.
        if dict_format:
            card_info.append(card.Card(position.v3_pos_to_position(eval(card_rep['posV3']), hex_width, hex_depth),
                                       card.CARD_ROTATION,
                                       card.get_card_color(card_rep['color']),
                                       card.get_card_count(card_rep['num']),
                                       card.get_card_shape(card_rep['shape']),
                                       card.get_card_selection(not card_rep['notSelected'], False)))
        else:
            split: List[str] = card_rep.split("(")
            pos: Tuple[float] = eval("( " + split[1])
            property_split: List[str] = split[0].split(" ")
            card_info.append(card.Card(position.v3_pos_to_position(pos, hex_width, hex_depth),
                                       card.CARD_ROTATION,
                                       card.get_card_color(property_split[2]),
                                       card.get_card_count(int(property_split[1])),
                                       card.get_card_shape(property_split[3]),
                                       card.get_card_selection(property_split[0] == 'selected', False)))

    # Now update all of the selection given whether the selected set is invalid
    selected_cards: List[card.Card] = \
        [card_rep for card_rep in card_info if card_rep.get_selection() in {card.CardSelection.SELECTED,
                                                                            card.CardSelection.INVALID}]

    # The set is invalid if more than three cards are selected.
    invalid_set: bool = len(selected_cards) > 3

    if not invalid_set:
        # It's also invalid if any of the properties appear more than once.
        selected_colors: Set[card.CardColor] = set()
        selected_shapes: Set[card.CardShape] = set()
        selected_counts: Set[card.CardCount] = set()

        for card_rep in selected_cards:
            invalid_set = card_rep.get_color() in selected_colors or card_rep.get_shape() in selected_shapes \
                          or card_rep.get_count() in selected_counts
            if not invalid_set:
                selected_colors.add(card_rep.get_color())
                selected_shapes.add(card_rep.get_shape())
                selected_counts.add(card_rep.get_count())
            else:
                break

    num_invalid: int = 0
    if invalid_set:
        for card_rep in card_info:
            if card_rep.get_selection() == card.CardSelection.SELECTED:
                card_rep.update_selection(card.CardSelection.INVALID)
                num_invalid += 1

    if num_invalid == 1:
        for card_rep in card_info:
            print(card_rep)
        raise ValueError('A single card is invalid!')

    return card_info


def construct_object(prop_name: str,
                     object_position: position.Position,
                     object_rotation: Tuple[str],
                     card_info: List[card.Card]) -> environment_objects.EnvironmentObject:
    """ Constructs an environment_objects.EnvironmentObject.

    Inputs:
        prop_name (str): The name of the prop (from Unity)
        position (position.Position): The hex (x,y) position of the object.
        rotation (Tuple[str]): The rotation object (from Unity)
        card_info (List[Card]): A list of cards on the board.

    Returns:
        environment_objects.EnvironmentObject representing the object.

    Raises:
        ValueError, if the prop name does not end with '(Clone)' (as all props in Unity should) or the prop name did not
        match any of the expected object types.
    """
    if not prop_name.endswith('(Clone)'):
        raise ValueError('Prop name should end with the string \'(Clone\'); was ' + prop_name)
    upper_prop_name: str = prop_name.replace('(Clone)', '').upper()

    rot_degree = int(float(object_rotation[1]))

    # Iterate through tree and plant types first.
    for tree_type in tree.TreeType:
        if tree_type.value == upper_prop_name:
            return tree.Tree(object_position, rot_degree, tree_type)
    for plant_type in plant.PlantType:
        if plant_type.value == upper_prop_name:
            return plant.Plant(object_position, rot_degree, plant_type)

    if upper_prop_name.startswith('CARDBASE'):
        # Find the card that is in card_info
        for card_rep in card_info:
            if card_rep.get_position() == object_position:
                return card_rep

    elif upper_prop_name.startswith(environment_objects.ObjectType.HUT.value):
        return hut.Hut(object_position, rotation.degree_to_rotation(rot_degree), hut.get_hut_color(upper_prop_name))
    elif upper_prop_name.startswith(environment_objects.ObjectType.LAMPPOST.value):
        return structures.Lamppost(object_position, rot_degree)
    elif upper_prop_name.startswith(environment_objects.ObjectType.WINDMILL.value):
        return structures.Windmill(object_position, rotation.degree_to_rotation(rot_degree))
    elif upper_prop_name.startswith(environment_objects.ObjectType.TOWER.value):
        return structures.Tower(object_position, rotation.degree_to_rotation(rot_degree))
    elif upper_prop_name.startswith(environment_objects.ObjectType.TENT.value):
        return structures.Tent(object_position, rotation.degree_to_rotation(rot_degree))
    elif upper_prop_name == 'AGENT_HUMAN':
        return agent.Agent(environment_objects.ObjectType.LEADER, agent_position=object_position,
                           agent_rotation=rotation.degree_to_rotation(rot_degree))
    elif upper_prop_name.startswith('AGENT_A'):
        return agent.Agent(environment_objects.ObjectType.FOLLOWER, agent_position=object_position,
                           agent_rotation=rotation.degree_to_rotation(rot_degree))

    raise ValueError('Could not construct object: ' + upper_prop_name)
