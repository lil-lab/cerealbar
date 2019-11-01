from __future__ import annotations

from agent.environment import agent_actions, position, rotation
from agent.environment import rotation
from agent.environment import util as environment_util
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from agent.environment import agent
    from agent.environment import position
    from agent.simulation import game
    from typing import Dict, List, Tuple


ODD_ROTATIONS: Dict[Tuple[int, int], rotation.Rotation] = {
    (1, 1): rotation.Rotation.NORTHEAST,
    (1, 0): rotation.Rotation.EAST,
    (1, -1): rotation.Rotation.SOUTHEAST,
    (0, -1): rotation.Rotation.SOUTHWEST,
    (-1, 0): rotation.Rotation.WEST,
    (0, 1): rotation.Rotation.NORTHWEST
}

EVEN_ROTATIONS: Dict[Tuple[int, int], rotation.Rotation] = {
    (0, 1): rotation.Rotation.NORTHEAST,
    (1, 0): rotation.Rotation.EAST,
    (0, -1): rotation.Rotation.SOUTHEAST,
    (-1, -1): rotation.Rotation.SOUTHWEST,
    (-1, 0): rotation.Rotation.WEST,
    (-1, 1): rotation.Rotation.NORTHWEST
}


def get_new_player_orientation(player: agent.Agent,
                               action: agent_actions.AgentAction,
                               obstacle_positions: List[position.Position]) -> Tuple[position.Position,
                                                                                     rotation.Rotation]:
    new_position: position.Position = player.get_position()
    new_rotation: rotation.Rotation = player.get_rotation()
    if action == agent_actions.AgentAction.MF:
        facing_position: position.Position = get_neighbor_move_position(player.get_position(), player.get_rotation())[0]
        if facing_position in obstacle_positions:
            raise ValueError('Cannot MF ' + str(player.get_type()) + ' from ' + str(player.get_position())
                             + ' rotating ' + str(player.get_rotation()) + ' to position ' + str(facing_position))
        new_position = facing_position
    elif action == agent_actions.AgentAction.MB:
        behind_position: position.Position = get_neighbor_move_position(player.get_position(), player.get_rotation())[1]
        if behind_position in obstacle_positions:
            raise ValueError('Cannot MB ' + str(player.get_type()) + ' from ' + str(player.get_position())
                             + ' rotating ' + str(player.get_rotation()) + ' to position ' + str(behind_position))
        new_position = behind_position
    elif action == agent_actions.AgentAction.RR:
        new_rotation = rotation.rotate_clockwise(player.get_rotation())
    elif action == agent_actions.AgentAction.RL:
        new_rotation = rotation.rotate_counterclockwise(player.get_rotation())

    return new_position, new_rotation


def get_neighbor_move_position(current_position: position.Position,
                               current_rotation: rotation.Rotation) -> Tuple[position.Position,
                                                                             position.Position]:
    back_rotation: rotation.Rotation = rotation.rotate_clockwise(rotation.rotate_clockwise(rotation.rotate_clockwise(
        current_rotation)))

    facing_position: position.Position = None
    behind_position: position.Position = None

    if current_position.y % 2 == 0:
        for offset, rot in EVEN_ROTATIONS.items():
            if rot == current_rotation:
                facing_position = position.Position(current_position.x + offset[0], current_position.y + offset[1])
            elif rot == back_rotation:
                behind_position = position.Position(current_position.x + offset[0], current_position.y + offset[1])
    else:
        for offset, rot in ODD_ROTATIONS.items():
            if rot == current_rotation:
                facing_position = position.Position(current_position.x + offset[0], current_position.y + offset[1])
            elif rot == back_rotation:
                behind_position = position.Position(current_position.x + offset[0], current_position.y + offset[1])
    return facing_position, behind_position


def get_possible_actions(game_server: game.Game,
                         player: agent.Agent) -> List[agent_actions.AgentAction]:
    possible_actions: List[agent_actions.AgentAction] = [agent_actions.AgentAction.STOP,
                                                         agent_actions.AgentAction.RR,
                                                         agent_actions.AgentAction.RL]

    player_position: position.Position = player.get_position()
    player_rotation: rotation.Rotation = player.get_rotation()

    facing_position, behind_position = get_neighbor_move_position(player_position, player_rotation)

    if facing_position not in game_server.get_obstacle_positions() \
            and facing_position.x >= 0 and facing_position.y >= 0 \
            and facing_position.x < environment_util.ENVIRONMENT_WIDTH \
            and facing_position.y < environment_util.ENVIRONMENT_DEPTH:
        possible_actions.append(agent_actions.AgentAction.MF)
    if behind_position not in game_server.get_obstacle_positions() \
            and behind_position.x >= 0 and behind_position.y >= 0 \
            and behind_position.x < environment_util.ENVIRONMENT_WIDTH \
            and behind_position.y < environment_util.ENVIRONMENT_DEPTH:
        possible_actions.append(agent_actions.AgentAction.MB)

    return possible_actions

