"""Defines how the environment should be represented as a vector."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import torch

from agent.environment import agent
from agent.environment import card
from agent.environment import environment_objects
from agent.environment import hut
from agent.environment import plant
from agent.environment import position
from agent.environment import rotation
from agent.environment import structures
from agent.environment import terrain
from agent.environment import tree
from agent.environment import util as environment_util

if TYPE_CHECKING:
    from agent.config import state_representation_args
    from agent.data import instruction_example
    from agent.environment import state_delta
    from typing import List, Tuple, Union

EMPTY_STR: str = '_NONE'


class StateRepresentation:
    """" This class only defines what's basically a vocabulary over all object types. It does not contain parameters
        for embedding environment properties.
    """

    def __init__(self, args: state_representation_args.StateRepresentationArgs):
        # Unsupported settings for args
        if not args.full_observability():
            raise ValueError('Need to adapt for partial observability')

        # Indices for dynamic states
        self._card_color_indices: List[Union[card.CardColor, str]] = [EMPTY_STR] + sorted(
            [color for color in card.CardColor])
        self._card_shape_indices: List[Union[card.CardShape, str]] = [EMPTY_STR] + sorted(
            [shape for shape in card.CardShape])
        self._card_count_indices: List[Union[card.CardCount, str]] = [EMPTY_STR] + sorted(
            [count for count in card.CardCount])

        # TODO: partial observability?
        self._card_selection_indices: List[Union[card.CardSelection, str]] = \
            [EMPTY_STR] + sorted([selection for selection in card.CardSelection])

        self._leader_rotation_indices: List[Union[rotation.Rotation, str]] = \
            [EMPTY_STR] + sorted([rot for rot in rotation.Rotation])

        self._follower_rotation_indices: List[Union[rotation.Rotation, str]] = \
            [EMPTY_STR] + sorted([rot for rot in rotation.Rotation])

        # Indices for static states
        # terrain.Terrain does not have a zero state because all hexes have terrain.
        # TODO partial observability
        self._terrain_indices: List[terrain.Terrain] = sorted([ter for ter in terrain.Terrain])
        self._hut_color_indices: List[Union[str, hut.HutColor]] = [EMPTY_STR] + sorted(
            [color for color in hut.HutColor])
        self._hut_rotation_indices: List[Union[str, rotation.Rotation]] = [EMPTY_STR] + sorted(
            [rot for rot in rotation.Rotation])
        self._tree_type_indices: List[Union[str, tree.TreeType]] = [EMPTY_STR] + sorted(
            [obj for obj in tree.TreeType])
        self._plant_type_indices: List[Union[str, plant.PlantType]] = [EMPTY_STR] + sorted(
            [obj for obj in plant.PlantType])
        self._windmill_rotation_indices: List[Union[str, rotation.Rotation]] = [EMPTY_STR] + sorted(
            [rot for rot in rotation.Rotation])
        self._tower_rotation_indices: List[Union[str, rotation.Rotation]] = [EMPTY_STR] + sorted(
            [rot for rot in rotation.Rotation])
        self._tent_rotation_indices: List[Union[str, rotation.Rotation]] = [EMPTY_STR] + sorted(
            [rot for rot in rotation.Rotation])
        self._prop_type_indices: List[Union[str, environment_objects.ObjectType]] = \
            ([EMPTY_STR] + [
                environment_objects.ObjectType.TREE,
                environment_objects.ObjectType.HUT,
                environment_objects.ObjectType.WINDMILL,
                environment_objects.ObjectType.TOWER,
                environment_objects.ObjectType.PLANT,
                environment_objects.ObjectType.LAMPPOST,
                environment_objects.ObjectType.TENT])

    def get_card_colors(self) -> List[Union[card.CardColor, str]]:
        return self._card_color_indices

    def get_card_shapes(self) -> List[Union[card.CardShape, str]]:
        return self._card_shape_indices

    def get_card_counts(self) -> List[Union[card.CardCount, str]]:
        return self._card_count_indices

    def get_card_selection(self) -> List[Union[card.CardSelection, str]]:
        return self._card_selection_indices

    def get_leader_rotation(self) -> List[Union[rotation.Rotation, str]]:
        return self._leader_rotation_indices

    def get_follower_rotation(self) -> List[Union[rotation.Rotation, str]]:
        return self._follower_rotation_indices

    def get_terrains(self) -> List[Union[terrain.Terrain, str]]:
        return self._terrain_indices

    def get_hut_colors(self) -> List[Union[hut.HutColor, str]]:
        return self._hut_color_indices

    def get_hut_rotations(self) -> List[Union[rotation.Rotation, str]]:
        return self._hut_rotation_indices

    def get_windmill_rotations(self) -> List[Union[rotation.Rotation, str]]:
        return self._windmill_rotation_indices

    def get_tower_rotations(self) -> List[Union[rotation.Rotation, str]]:
        return self._tower_rotation_indices

    def get_tent_rotations(self) -> List[Union[rotation.Rotation, str]]:
        return self._tent_rotation_indices

    def get_tree_types(self) -> List[Union[tree.TreeType, str]]:
        return self._tree_type_indices

    def get_plant_types(self) -> List[Union[plant.PlantType, str]]:
        return self._plant_type_indices

    def get_prop_types(self) -> List[Union[environment_objects.ObjectType, str]]:
        return self._prop_type_indices

    def get_prop_indices(self, props: List[environment_objects.EnvironmentObject]):
        prop_type_indices = \
            [[self._prop_type_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _ in
             range(environment_util.ENVIRONMENT_WIDTH)]
        hut_color_indices = \
            [[self._hut_color_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _ in
             range(environment_util.ENVIRONMENT_WIDTH)]
        hut_rotation_indices = \
            [[self._hut_rotation_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _ in
             range(environment_util.ENVIRONMENT_WIDTH)]
        tree_type_indices = \
            [[self._tree_type_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _ in
             range(environment_util.ENVIRONMENT_WIDTH)]
        plant_type_indices = \
            [[self._plant_type_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _ in
             range(environment_util.ENVIRONMENT_WIDTH)]
        windmill_rotation_indices = \
            [[self._windmill_rotation_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for
             _ in range(environment_util.ENVIRONMENT_WIDTH)]
        tower_rotation_indices = \
            [[self._tower_rotation_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _
             in range(environment_util.ENVIRONMENT_WIDTH)]
        tent_rotation_indices = \
            [[self._tent_rotation_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _ in
             range(environment_util.ENVIRONMENT_WIDTH)]

        for prop in props:
            x: int = prop.get_position().x
            y: int = prop.get_position().y
            prop_type_indices[x][y] = self._prop_type_indices.index(prop.get_type())
            if prop.get_type() == environment_objects.ObjectType.HUT:
                assert isinstance(prop, hut.Hut)
                hut_color_indices[x][y] = self._hut_color_indices.index(prop.get_color())
                hut_rotation_indices[x][y] = self._hut_rotation_indices.index(prop.get_rotation())
            elif prop.get_type() == environment_objects.ObjectType.TREE:
                assert isinstance(prop, tree.Tree)
                tree_type_indices[x][y] = self._tree_type_indices.index(prop.get_tree_type())
            elif prop.get_type() == environment_objects.ObjectType.PLANT:
                assert isinstance(prop, plant.Plant)
                plant_type_indices[x][y] = self._plant_type_indices.index(prop.get_plant_type())
            elif prop.get_type() == environment_objects.ObjectType.WINDMILL:
                assert isinstance(prop, structures.Windmill)
                windmill_rotation_indices[x][y] = self._windmill_rotation_indices.index(prop.get_rotation())
            elif prop.get_type() == environment_objects.ObjectType.TOWER:
                assert isinstance(prop, structures.Tower)
                tower_rotation_indices[x][y] = self._tower_rotation_indices.index(prop.get_rotation())
            elif prop.get_type() == environment_objects.ObjectType.TENT:
                assert isinstance(prop, structures.Tent)
                tent_rotation_indices[x][y] = self._tent_rotation_indices.index(prop.get_rotation())
            else:
                assert isinstance(prop, structures.Lamppost)
        indices = [prop_type_indices,
                   hut_color_indices,
                   hut_rotation_indices,
                   tree_type_indices,
                   plant_type_indices,
                   windmill_rotation_indices,
                   tower_rotation_indices,
                   tent_rotation_indices]
        np_indices: List[np.array] = [np.array(index_list) for index_list in indices]
        return np_indices

    def get_card_indices(self, cards: List[card.Card]) -> Tuple[np.array, np.array, np.array, np.array]:
        count_indices = \
            [[self._card_count_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _ in
             range(environment_util.ENVIRONMENT_WIDTH)]
        color_indices = \
            [[self._card_color_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _ in
             range(environment_util.ENVIRONMENT_WIDTH)]
        shape_indices = \
            [[self._card_shape_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _ in
             range(environment_util.ENVIRONMENT_WIDTH)]
        selection_indices = \
            [[self._card_selection_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _
             in range(environment_util.ENVIRONMENT_WIDTH)]

        for card_emb in cards:
            count_index = self._card_count_indices.index(card_emb.get_count())
            color_index = self._card_color_indices.index(card_emb.get_color())
            shape_index = self._card_shape_indices.index(card_emb.get_shape())
            selection_index = self._card_selection_indices.index(card_emb.get_selection())

            card_position: position.Position = card_emb.get_position()

            count_indices[card_position.x][card_position.y] = count_index
            color_indices[card_position.x][card_position.y] = color_index
            shape_indices[card_position.x][card_position.y] = shape_index
            selection_indices[card_position.x][card_position.y] = selection_index

        return np.array(count_indices), np.array(color_indices), np.array(shape_indices), np.array(selection_indices)

    def batch_state_delta_indices(self, state_deltas: List[state_delta.StateDelta]) -> List[torch.Tensor]:
        card_count_arrays: List[np.array] = []
        card_color_arrays: List[np.array] = []
        card_shape_arrays: List[np.array] = []
        card_selection_arrays: List[np.array] = []
        leader_rotation_arrays: List[np.array] = []
        follower_rotation_arrays: List[np.array] = []

        # TODO: this is just getting indices for the first initial state only

        for example in state_deltas:
            card_count_indices, card_color_indices, card_shape_indices, card_selection_indices = \
                self.get_card_indices(example.cards)
            card_count_arrays.append(card_count_indices)
            card_color_arrays.append(card_color_indices)
            card_shape_arrays.append(card_shape_indices)
            card_selection_arrays.append(card_selection_indices)

            leader_rotations = \
                [[self._leader_rotation_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)]
                 for _ in range(environment_util.ENVIRONMENT_WIDTH)]
            leader: agent.Agent = example.leader
            leader_rotations[leader.get_position().x][leader.get_position().y] = \
                self._leader_rotation_indices.index(leader.get_rotation())
            leader_rotation_arrays.append(leader_rotations)

            follower_rotations = \
                [[self._follower_rotation_indices.index(EMPTY_STR) for __ in range(environment_util.ENVIRONMENT_DEPTH)]
                 for _ in
                 range(environment_util.ENVIRONMENT_WIDTH)]
            follower: agent.Agent = example.follower
            follower_rotations[follower.get_position().x][follower.get_position().y] = \
                self._follower_rotation_indices.index(follower.get_rotation())
            follower_rotation_arrays.append(follower_rotations)

        card_count_tensor = torch.tensor(np.stack(card_count_arrays))
        card_color_tensor = torch.tensor(np.stack(card_color_arrays))
        card_shape_tensor = torch.tensor(np.stack(card_shape_arrays))
        card_selection_tensor = torch.tensor(np.stack(card_selection_arrays))
        leader_rotation_tensor = torch.tensor(np.stack(leader_rotation_arrays))
        follower_rotation_tensor = torch.tensor(np.stack(follower_rotation_arrays))

        return [card_count_tensor,
                card_color_tensor,
                card_shape_tensor,
                card_selection_tensor,
                leader_rotation_tensor,
                follower_rotation_tensor]

    def static_indices(self, example) -> List[np.array]:
        prop_indices = self.get_prop_indices(example.get_objects())

        terrain_array = \
            [[-1 for __ in range(environment_util.ENVIRONMENT_DEPTH)] for _ in
             range(environment_util.ENVIRONMENT_WIDTH)]
        for ter, location in example.get_hexes():
            terrain_array[location.x][location.y] = self._terrain_indices.index(ter)

        return prop_indices + [terrain_array]

    def batch_static_indices(self, examples: List[instruction_example.InstructionExample]) -> List[torch.Tensor]:
        prop_arrays: List[np.array] = []
        hut_color_arrays: List[np.array] = []
        hut_rotation_arrays: List[np.array] = []
        tree_type_arrays: List[np.array] = []
        plant_type_arrays: List[np.array] = []
        windmill_rotation_arrays: List[np.array] = []
        tower_rotation_arrays: List[np.array] = []
        tent_rotation_arrays: List[np.array] = []

        terrain_arrays: List[np.array] = []

        for example in examples:
            (prop_array,
             hut_color_array,
             hut_rotation_array,
             tree_type_array,
             plant_type_array,
             windmill_rotation_array,
             tower_rotation_array,
             tent_rotation_array,
             terrain_array) = example.get_static_indices(self)
            prop_arrays.append(prop_array)
            hut_color_arrays.append(hut_color_array)
            hut_rotation_arrays.append(hut_rotation_array)
            tree_type_arrays.append(tree_type_array)
            plant_type_arrays.append(plant_type_array)
            windmill_rotation_arrays.append(windmill_rotation_array)
            tower_rotation_arrays.append(tower_rotation_array)
            tent_rotation_arrays.append(tent_rotation_array)
            terrain_arrays.append(terrain_array)

        prop_tensor = torch.tensor(np.stack(prop_arrays))
        hut_color_tensor = torch.tensor(np.stack(hut_color_arrays))
        hut_rotation_tensor = torch.tensor(np.stack(hut_rotation_arrays))
        tree_type_tensor = torch.tensor(np.stack(tree_type_arrays))
        plant_type_tensor = torch.tensor(np.stack(plant_type_arrays))
        windmill_rotation_tensor = torch.tensor(np.stack(windmill_rotation_arrays))
        tower_rotation_tensor = torch.tensor(np.stack(tower_rotation_arrays))
        tent_rotation_tensor = torch.tensor(np.stack(tent_rotation_arrays))
        terrain_tensor = torch.tensor(np.stack(terrain_arrays))

        return [prop_tensor,
                hut_color_tensor,
                hut_rotation_tensor,
                tree_type_tensor,
                plant_type_tensor,
                windmill_rotation_tensor,
                tower_rotation_tensor,
                tent_rotation_tensor,
                terrain_tensor]
