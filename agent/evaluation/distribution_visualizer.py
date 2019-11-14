"""Visualizes distributions over the map in Unity."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from agent.environment import util as environment_util

if TYPE_CHECKING:
    from agent.simulation import unity_game


def _np_float_to_trunc_float(float_val: np.float32):
    """Converts an NP float to Python float and reduces the precision."""
    rounded = round(float_val.item(), 2)
    if str(rounded) == '0.0':
        return 0
    return rounded


def _normalize(x):
    if x < 0.25:
        return 0.
    return x / 2 + 0.5


def visualize_probabilities(goal_probabilities: np.array,
                            trajectory_distribution: np.array,
                            obstacle_probabilities: np.array,
                            avoid_probabilities: np.array,
                            game_server: unity_game.UnityGame):
    goal = list()
    traj = list()
    obs = list()
    avoid = list()

    max_traj = np.max(trajectory_distribution)

    for x in range(0, environment_util.ENVIRONMENT_WIDTH):
        for y in range(0, environment_util.ENVIRONMENT_DEPTH):
            card_val = _np_float_to_trunc_float(goal_probabilities[x][y])

            # Normalize the trajectory distribution by the maximum value in the whole map.
            # This makes it easier to see.
            traj_val = _np_float_to_trunc_float(np.float32(_normalize(trajectory_distribution[x][y] / max_traj)))

            impass_val = _np_float_to_trunc_float(obstacle_probabilities[x][y])
            avoid_val = _np_float_to_trunc_float(avoid_probabilities[x][y])

            # Only send non-zero values.
            if card_val > 0:
                goal.append({'p': [x, y], 'v': card_val})
            if traj_val > 0:
                traj.append({'p': [x, y], 'v': traj_val})
            if impass_val > 0:
                obs.append({'p': [x, y], 'v': impass_val})
            if avoid_val > 0:
                avoid.append({'p': [x, y], 'v': avoid_val})

    g: bool = game_server.send_goal_probabilities(goal)
    t: bool = game_server.send_trajectory_distribution(traj)
    o: bool = game_server.send_obstacle_probabilities(obs)
    a: bool = game_server.send_avoid_probabilities(avoid)

    # If any of the distributions failed to send, just run the agent without waiting
    # Waits until the user has given the go ahead
    if g and t and o and a:
        input('Press any key to continue. ')
