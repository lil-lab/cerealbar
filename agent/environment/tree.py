""" Contains various types of tree objects.

Classes:
    TreeType (Enum): Types of trees. See below for description of the tree types.
    Tree (environment_objects.EnvironmentObject): A tree object.
"""

from enum import Enum

from agent.environment import environment_objects
from agent.environment import position


class TreeType(Enum):
    """ Tree type. Combination of shape and color. """
    PINE_TREE_CRV: str = "PINE_TREE_CRV"  # Pine tree with bright green leaves. Not completely straight (curvy).
    GREEN_PINE_TREE: str = "PINE_TREE"  # Light green pine tree. Completely straight.

    GREEN_ROUND_TREE: str = "TREE"  # Tree with a single bump that's green.
    TREE_RD: str = "TREE_RD"  # Same as tree, but red.
    PALM_TREE: str = "PALM_TREE"  # Palm tree.
    OAK_TREE_LM: str = "OAK_TREE_LM"  # Kind of a bouldery looking tree. Short with yellow leaves.

    PT_TREE: str = "PT_TREE"  # Similar to the green round tree; single bump, but different orientation.
    PT_TREE_LM: str = "PT_TREE_LM"  # Yellow colored PT_TREE.

    # Bush-like trees -- different small bumps.
    MULTI_TREE: str = "MULTI_TREE"  # Multicolored tree with different bumps to it. Yellow/red color.
    BUSH_TREE_BR: str = "BUSH_TREE_BR"  # Multiple bumps; brown color; shortish.
    BUSH_TREE: str = "BUSH_TREE"  # Multiple bumps; various shades of green; shortish.
    RED_BUSH_TREE: str = "BUSH_TREE_RD"  # Red bush tree.

    # Tall trees: larger bumps than the bush trees.
    TALL_TREE: str = "TALL_TREE"  # Tall green bumpy tree.
    TALL_TREE_RD: str = "TALL_TREE_RD"  # Tree with a single bump that's red.

    # "Clean" trees -- tall and skinny; conical shaped.
    CLEAN_TREE_BR: str = "CLEAN_TREE_BR"  # Tall smooth conical tree (brown color).
    CLEAN_TREE: str = "CLEAN_TREE"  # Green clean tree.
    RED_PINE_TREE: str = "CLEAN_TREE_RD"  # Red tree that's shaped like a pine tree.

    def __str__(self):
        return self.value

    def __lt__(self, other) -> bool:
        return self.value < other.value


class Tree(environment_objects.EnvironmentObject):
    """ A tree object. Constructor ensures that the rotation is expected.

    Attributes:
        _tree_type (TreeType): The type of tree.
    """

    def __init__(self,
                 object_position: position.Position,
                 rot_degree: int,
                 tree_type: TreeType):
        super(Tree, self).__init__(object_position, environment_objects.ObjectType.TREE)

        if not rot_degree == 0:
            raise ValueError("Expected a tree to be rotated with 0 degrees, but got " + str(rot_degree))

        self._tree_type: TreeType = tree_type

    def get_tree_type(self) -> TreeType:
        """ Returns the tree type."""
        return self._tree_type

    def __str__(self):
        return super(Tree, self).__str__() + "\t" + str(self._tree_type)

    def __eq__(self, other) -> bool:
        """ The tree is the same object if the type is the same (and all other properties are the same)"""
        if isinstance(other, self.__class__):
            return super(Tree, self).__eq__(other) and self._tree_type == other.get_tree_type()
        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)
