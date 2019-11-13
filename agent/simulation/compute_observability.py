"""Computes observable locations from each location/rotation in the environment."""
from __future__ import annotations

import json
import pickle

from typing import TYPE_CHECKING

from agent.config import util
from agent.environment import agent
from agent.environment import environment_objects
from agent.environment import position
from agent.environment import rotation
from agent.simulation import server
from agent.simulation import unity_game

if TYPE_CHECKING:
    from agent.config import program_args
    from agent.environment import state_delta


# SCOPE VARIABLES:
# pos = (0, -5, 24.5)
# rot = (0, 180, 0)
# scale = (0.48, 1, 0.22)


# Start a game
def main():
    args: program_args.ProgramArgs = util.get_args()
    server_socket: server.ServerSocket = server.ServerSocket('localhost', 3706)
    server_socket.start_unity()

    game_server: unity_game.UnityGame = unity_game.UnityGame(args.get_game_args(), server_socket)

    # TODO: may need to get hexes/obstacles because the intersections may not happen if the elevation is wrong
    game_info: state_delta.StateDelta = game_server.get_game_info(True)

    # Then, for each possible position, reset the state
    pos_rot_dict = dict()
    for x in range(25):
        for y in range(25):
            for rot in rotation.Rotation:
                agent_pos: position.Position = position.Position(x, y)
                game_info.follower = agent.Agent(environment_objects.ObjectType.FOLLOWER, agent_pos, rot)
                game_server.reset_state([], game_info, 0, [], allow_exceptions=True)

                # Get the visible hexes
                game_server._connection.send_data('status agent')
                data: bytes = game_server._connection.receive_data()
                json_data = json.loads(data.decode('utf-8'))

                visible_positions = []
                for obj in json_data['eyesightInfo']:
                    if obj['prop'].endswith('cell'):
                        pos = position.v3_pos_to_position(eval(obj['propPosV3']), 17.321, 15.)
                        visible_positions.append(pos)

                pos_rot_dict[(agent_pos, rot)] = visible_positions

    server_socket.close()

    with open("agent/preprocessed/visible_positions.pkl", 'wb') as ofile:
        pickle.dump(pos_rot_dict, ofile)


if __name__ == '__main__':
    main()
