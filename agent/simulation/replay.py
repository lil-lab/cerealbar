"""Contains functionality for loading and replaying recorded games. """
import json
import os
import time
from datetime import datetime
from typing import Dict, Any

from agent.config import game_args
from agent.config import replay_args
from agent.environment import agent_actions
from agent.simulation import server
from agent.simulation import unity_game

DATE_FORMAT: str = '%Y-%m-%d %H:%M:%S.%f'


def load_games(directory: str):
    games = {}
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            print('Loading games from file: %r' % filename)
            with open(os.path.join(directory, filename)) as infile:
                games_dict = json.load(infile)
                for game_id, game_info in games_dict.items():
                    assert game_id not in games, 'Game ID %r appeared more than once in directory %r' % (game_id,
                                                                                                         directory)
                    games[game_id] = game_info

    return games


def replay_game(game_data: Dict, game_arguments: game_args.GameArgs, game_server: server.ServerSocket,
                replay_arguments: replay_args.ReplayArgs):
    """Replays a game's actions."""
    actions = game_data['actions']

    # Start the game
    game = unity_game.UnityGame(game_arguments,
                                game_server,
                                auto_end_turn=False,
                                seed=game_data['seed'],
                                number_of_cards=game_data['num_cards'])
    prev_time: datetime = datetime.strptime(actions[0]['time'], DATE_FORMAT)

    for action in actions:
        if replay_arguments.is_realtime():
            action_time: datetime = datetime.strptime(action['time'], DATE_FORMAT)
            sleep_time = replay_arguments.get_playback_speed() * (action_time - prev_time).total_seconds()
            if sleep_time > 0:
                sleep_time = min(sleep_time, 0.5)
                time.sleep(sleep_time)
            prev_time = action_time

        if action['type'] == 'instruction':
            game.send_command(action['instruction'])
        elif action['type'] == 'movement':
            if action['move_id'] >= 0:
                if action['character'] == 'Leader':
                #if action['character'] == 'Human':
                    game.execute_leader_action(agent_actions.AgentAction(action['action']))
                elif action['character'] == 'Follower':
                #elif action['character'] == 'Agent':
                    game.execute_follower_action(agent_actions.AgentAction(action['action']))
                else:
                    #raise ValueError('Unrecognized player type: ' + action['player'])
                    raise ValueError('Unrecognized player type: ' + action['character'])
        elif action['type'] == 'finish command':
            game.execute_follower_action(agent_actions.AgentAction.STOP)
        elif action['type'] == 'end turn':
            game.end_turn()
    return game.get_score()


def replay(game_arguments: game_args.GameArgs, replay_arguments: replay_args.ReplayArgs) -> None:
    """ Replays recorded games.

    TODO: Expand this into a data browser.
    """
    # Start the server
    game_server: server.ServerSocket = server.ServerSocket(game_arguments.get_ip_address(), game_arguments.get_port())
    game_server.start_unity()

    # Load games
    game_id: str = replay_arguments.get_game_id()
    all_games = load_games(replay_arguments.get_game_directory())

    print('Loaded %r games' % len(all_games))
    game_data: Dict[str, Any] = all_games[game_id]
    replay_game(game_data, game_arguments, game_server, replay_arguments)

    game_server.close()
