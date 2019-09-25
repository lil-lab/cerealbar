""" Classes and methods associated with card structures.

Classes:
    CardColor (Enum): Various card colors.
    CardCount (Enum): Various card counts (1, 2, and 3).
    CardShape (Enum): Various card shapes.
    CardSelection (Enum): Selections of cards (selected, unselected, invalid).
    Card (EnvironmentObject): A card object.

Constants:
    CARD_ROTATION (int): The expected rotation for each card.
    POSSIBLE_CARDS (List): The list of possible cards (as count, color, shape triples).

Functions:
    get_card_color: Returns a CardColor given a string value.
    get_card_count: Returns a CardCount given a string value.
    get_card_shape: Returns a CardShape given a string value.
    get_card_selection: Returns a CardSelection given a string value.

"""
from enum import Enum
from typing import List, Dict, Any, Tuple

from agent.environment import environment_objects
from agent.environment import position

CARD_ROTATION: int = 150


class CardColor(Enum):
    """ Unique card colors. """
    ORANGE: str = 'ORANGE'
    BLACK: str = 'BLACK'
    BLUE: str = 'BLUE'
    YELLOW: str = 'YELLOW'
    PINK: str = 'PINK'
    RED: str = 'RED'
    GREEN: str = 'GREEN'

    def __str__(self):
        return self.value

    def __lt__(self, other) -> bool:
        return self.value < other.value


def get_card_color(color_name: str) -> CardColor:
    """ Gets a card color from a string.

    Inputs:
        color_name (str): The name to convert.

    Returns:
        CardColor corresponding to the name.

    Raises:
        ValueError if the card color was not found.
    """
    upper_color: str = color_name.replace('(UnityEngine.Material)', '').replace('card_', '').strip().upper()

    for data in CardColor:
        if data.value == upper_color:
            return data
    raise ValueError('Card color not found: %r' % upper_color)


class CardCount(Enum):
    ONE: str = '1'
    TWO: str = '2'
    THREE: str = '3'

    def __str__(self):
        return self.value

    def __lt__(self, other) -> bool:
        return self.value < other.value


def get_card_count(count_int: int) -> CardCount:
    for data in CardCount:
        if data.value == str(count_int):
            return data
    raise ValueError('Card count not found: %r' % count)


class CardShape(Enum):
    TORUS: str = 'TORUS'
    PLUS: str = 'PLUS'
    STAR: str = 'STAR'
    CUBE: str = 'CUBE'
    HEART: str = 'HEART'
    DIAMOND: str = 'DIAMOND'
    TRIANGLE: str = 'TRIANGLE'

    def __str__(self):
        return self.value

    def __lt__(self, other) -> bool:
        return self.value < other.value


def get_card_shape(shape_name: str) -> CardShape:
    upper_shape: str = shape_name.replace('(UnityEngine.GameObject)', '').strip().upper()

    for data in CardShape:
        if data.value == upper_shape:
            return data
    raise ValueError('Card shape not found: %r' % upper_shape)


class CardSelection(Enum):
    UNSELECTED: str = 'UNSELECTED'
    SELECTED: str = 'SELECTED'
    INVALID: str = 'INVALID'

    def __str__(self):
        return self.value

    def __lt__(self, other) -> bool:
        return self.value < other.value


def get_card_selection(is_selected: bool, invalid_set: bool) -> CardSelection:
    if is_selected:
        if invalid_set:
            return CardSelection.INVALID
        return CardSelection.SELECTED
    return CardSelection.UNSELECTED


class Card(environment_objects.EnvironmentObject):
    def __init__(self,
                 card_position: position.Position,
                 rot_degree: int,
                 card_color: CardColor,
                 card_count: CardCount,
                 card_shape: CardShape,
                 selection: CardSelection):
        super(Card, self).__init__(card_position, environment_objects.ObjectType.CARD)

        self._color: CardColor = card_color
        self._count: CardCount = card_count
        self._shape: CardShape = card_shape
        self._selection: CardSelection = selection

        if rot_degree != CARD_ROTATION:
            raise ValueError('Card is not rotated %r degrees; was %r' % (CARD_ROTATION, rot_degree))

    def update_position(self, new_position: position.Position) -> None:
        self._position = new_position

    def update_selection(self, selection: CardSelection) -> None:
        self._selection = selection

    def get_selection(self) -> CardSelection:
        return self._selection

    def get_shape(self) -> CardShape:
        return self._shape

    def get_count(self) -> CardCount:
        return self._count

    def get_color(self) -> CardColor:
        return self._color

    def to_dict(self) -> Dict[str, Any]:
        card_dict: Dict[str, Any] = dict()
        card_dict['color'] = str(self.get_color()).lower()
        card_dict['shape'] = str(self.get_shape()).lower()
        card_dict['count'] = int(str(self.get_count()))
        card_dict['sel'] = self.get_selection() != CardSelection.UNSELECTED

        # The position is a JSON encoded list of integers
        card_dict['pos'] = [self.get_position().x, self.get_position().y]
        return card_dict

    def __eq__(self, other) -> bool:
        """ For equality of cards, don't care whether selection is the same, but other properties should not change. """
        if isinstance(other, self.__class__):
            return self._position == other.get_position() \
                   and self._color == other._color \
                   and self._count == other._count \
                   and self._shape == other._shape
        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __str__(self):
        return super(Card, self).__str__() + '\t' + str(self._count) + '\t' + \
               str(self._color) + '\t' + str(self._shape) + '\t' + str(self._selection)

    def __lt__(self, other) -> bool:
        return (self._position.x, self._position.y) < (other.get_position().x, other.get_position().y)


POSSIBLE_CARDS: List[Tuple[CardCount, CardColor, CardShape]] = []
for count in sorted([count for count in CardCount]):
    for color in sorted([color for color in CardColor]):
        for shape in sorted([shape for shape in CardShape]):
            POSSIBLE_CARDS.append((count, color, shape))
