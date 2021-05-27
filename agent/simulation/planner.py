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

FOLLOWER_BACKWARDS_COST: int = 3.5

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


def follower_action_cost(actions: List[agent_actions.AgentAction]) -> int:
    cost: int = 0
    for action in actions:
        if action == agent_actions.AgentAction.MB:
            cost += FOLLOWER_BACKWARDS_COST
        else:
            cost += 1

    return cost


class PositionRotationQueue:
    def __init__(self):
        self.elem: List[Tuple[int, Tuple[position.Position,
                                         rotation.Rotation]]] = []

    def is_empty(self) -> bool:
        return len(self.elem) == 0

    def put(self, pos: position.Position, rot: rotation.Rotation,
            pri: int) -> None:
        heapq.heappush(self.elem, (pri, (pos, rot)))

    def get(self) -> Tuple[position.Position, rotation.Rotation]:
        return heapq.heappop(self.elem)[1]


def find_path_between_positions(
    avoid_locations: List[position.Position],
    start_config: agent.Agent,
    target_config: agent.Agent,
    ignore_target_rotation: bool = False
) -> Optional[List[Tuple[agent.Agent, agent_actions.AgentAction]]]:
    """Finds a path between two positions in the map.

    Args:
        avoid_locations: A list of locations to avoid, including obstacles and cards that should not be touched.
        start_config: The starting configuration (position/rotation) of the agent.
        target_config: The target configuration (position/rotation) of the agent.
        ignore_target_rotation: Whether the final rotation of the agent matters.
    """
    queue: PositionRotationQueue = PositionRotationQueue()
    queue.put(start_config.get_position(), start_config.get_rotation(), 0)
    paths: Dict[Tuple[position.Position, rotation.Rotation],
                Optional[Tuple[Tuple[position.Position, rotation.Rotation],
                               List[agent_actions.AgentAction]]]] = dict()
    paths[(start_config.get_position(), start_config.get_rotation())] = None

    total_dist: Dict[Tuple[position.Position, rotation.Rotation], int] = dict()
    total_dist[(start_config.get_position(), start_config.get_rotation())] = 0

    has_ended: bool = False
    current_pos_and_rot: Tuple[Optional[position.Position],
                               Optional[rotation.Rotation]] = (None, None)

    while not queue.is_empty():
        current_pos_and_rot: Tuple[position.Position,
                                   rotation.Rotation] = queue.get()
        current_position: position.Position = current_pos_and_rot[0]
        current_rotation: rotation.Rotation = current_pos_and_rot[1]
        if current_position == target_config.get_position():
            has_ended = True
            break

        for next_position in position.get_neighbors(
                current_position, environment_util.ENVIRONMENT_WIDTH,
                environment_util.ENVIRONMENT_DEPTH):
            if next_position not in avoid_locations:
                action_rot_pairs: List[Tuple[
                    List[agent_actions.AgentAction], rotation.
                    Rotation]] = rotation_planner.rotation_possibilities(
                        current_position, next_position, current_rotation)

                # There could be several ways to get from one hex to another by rotation. Iterate through all of them,
                # considering the cost of backwards moves.
                for move_possibility in action_rot_pairs:
                    actions: List[
                        agent_actions.AgentAction] = move_possibility[0]
                    resulting_rotation: rotation.Rotation = move_possibility[1]

                    new_dist: int = total_dist[
                        current_pos_and_rot] + follower_action_cost(actions)

                    move_pair: Tuple[position.Position,
                                     rotation.Rotation] = (next_position,
                                                           resulting_rotation)
                    if new_dist < total_dist.get(move_pair, sys.maxsize):
                        total_dist[move_pair] = new_dist
                        paths[move_pair] = (current_pos_and_rot, actions)
                        priority: int = new_dist + metric.manhattan_distance(
                            target_config.get_position(), next_position)
                        queue.put(next_position, resulting_rotation, priority)

    if not has_ended:
        return None

    final_rotation: rotation.Rotation = current_pos_and_rot[1]
    path_positions: List[position.Position] = []
    actions: List[agent_actions.AgentAction] = []

    while current_pos_and_rot != (start_config.get_position(),
                                  start_config.get_rotation()):
        segment_actions = paths[current_pos_and_rot][1]
        segment_actions.reverse()
        actions += segment_actions
        path_positions.append(current_pos_and_rot[0])
        current_pos_and_rot = paths[current_pos_and_rot][0]

    actions.reverse()
    path_positions.reverse()

    if not ignore_target_rotation and target_config.get_rotation(
    ) != final_rotation:
        num_right: int = 0
        temp_right_rotation: rotation.Rotation = final_rotation
        while temp_right_rotation != target_config.get_rotation():
            num_right += 1
            temp_right_rotation = rotation.rotate_clockwise(
                temp_right_rotation)

        if num_right <= 3:
            actions.extend(
                [agent_actions.AgentAction.RR for _ in range(num_right)])
        else:
            actions.extend(
                [agent_actions.AgentAction.RL for _ in range(6 - num_right)])

    path_positions = [start_config.get_position()] + path_positions

    # Now create an actual list of states and actions
    position_action_list: List[Tuple[agent.Agent,
                                     agent_actions.AgentAction]] = list()
    pos_idx: int = 0
    current_rotation: rotation.Rotation = start_config.get_rotation()
    for action in actions:
        position_action_list.append(
            (agent.Agent(environment_objects.ObjectType.FOLLOWER,
                         path_positions[pos_idx], current_rotation), action))
        if action in {
                agent_actions.AgentAction.MF, agent_actions.AgentAction.MB
        }:
            pos_idx += 1
        elif action in {
                agent_actions.AgentAction.RR, agent_actions.AgentAction.RL
        }:
            if action == agent_actions.AgentAction.RR:
                current_rotation = rotation.rotate_clockwise(current_rotation)
            else:
                current_rotation = rotation.rotate_counterclockwise(
                    current_rotation)
        else:
            raise ValueError('Action should not be generated: ' + str(action))

    # Should end up in the expected rotation.
    if not ignore_target_rotation:
        assert current_rotation == target_config.get_rotation()

    return position_action_list

