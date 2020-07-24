from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from agent.environment import agent_actions
from agent.environment import rotation
from agent.simulation import planner

if TYPE_CHECKING:
    from typing import List, Tuple
    from agent.environment import position


def rotation_possibilities(start_position: position.Position,
                           end_position: position.Position,
                           agent_rotation: rotation.Rotation) -> List[Tuple[List[agent_actions.AgentAction],
                                                                            rotation.Rotation]]:
    current_rotation: rotation.Rotation = copy.deepcopy(agent_rotation)

    num_rotations: int = get_num_rotations(start_position, end_position, current_rotation)

    if num_rotations == 0:
        return [([agent_actions.AgentAction.MF], current_rotation)]
    elif num_rotations == 1:
        return [([agent_actions.AgentAction.RR, agent_actions.AgentAction.MF],
                 rotation.rotate_clockwise(current_rotation)),
                ([agent_actions.AgentAction.RL, agent_actions.AgentAction.RL, agent_actions.AgentAction.MB],
                 rotation.rotate_counterclockwise(rotation.rotate_counterclockwise(current_rotation)))]
    elif num_rotations == 2:
        return [([agent_actions.AgentAction.RR, agent_actions.AgentAction.RR, agent_actions.AgentAction.MF],
                 rotation.rotate_clockwise(rotation.rotate_clockwise(current_rotation))),
                ([agent_actions.AgentAction.RL, agent_actions.AgentAction.MB],
                 rotation.rotate_counterclockwise(current_rotation))]
    elif num_rotations == 3:
        return [([agent_actions.AgentAction.MB], current_rotation),
                ([agent_actions.AgentAction.RR,
                  agent_actions.AgentAction.RR,
                  agent_actions.AgentAction.RR,
                  agent_actions.AgentAction.MF],
                 rotation.rotate_clockwise(rotation.rotate_clockwise(rotation.rotate_clockwise(current_rotation))))]
    elif num_rotations == 4:
        return [([agent_actions.AgentAction.RR, agent_actions.AgentAction.MB],
                 rotation.rotate_clockwise(current_rotation)),
                ([agent_actions.AgentAction.RL, agent_actions.AgentAction.RL, agent_actions.AgentAction.MF],
                 rotation.rotate_counterclockwise(rotation.rotate_counterclockwise(current_rotation)))]
    elif num_rotations == 5:
        return [([agent_actions.AgentAction.RL, agent_actions.AgentAction.MF],
                 rotation.rotate_counterclockwise(current_rotation)),
                ([agent_actions.AgentAction.RR, agent_actions.AgentAction.RR, agent_actions.AgentAction.MB],
                 rotation.rotate_clockwise(rotation.rotate_clockwise(current_rotation)))]
    else:
        raise ValueError('Can\'t rotate ' + str(num_rotations) + ' times.')


def get_num_rotations(start_position: position.Position,
                      end_position: position.Position,
                      start_rotation: rotation.Rotation) -> int:
    num_rotations: int = 0

    start_depth = start_position.y

    move_vector: Tuple[int, int] = (end_position.x - start_position.x,
                                    end_position.y - start_position.y)

    temp_rot: rotation.Rotation = copy.deepcopy(start_rotation)

    if start_depth % 2 == 0:
        while not temp_rot == planner.EVEN_ROTATIONS[move_vector]:
            num_rotations += 1
            temp_rot = rotation.rotate_clockwise(temp_rot)
    else:
        while not temp_rot == planner.ODD_ROTATIONS[move_vector]:
            num_rotations += 1
            temp_rot = rotation.rotate_clockwise(temp_rot)

    return num_rotations
