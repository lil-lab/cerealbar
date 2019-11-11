"""Utilities for laoding data."""

import json
import logging
import os
import pickle
from typing import Dict, List

from agent import util
from agent.config import data_args
from agent.config import game_args
from agent.data import cereal_bar_game
from agent.data import dataset_split
from agent.data import game_dataset
from agent.data import game_states
from agent.data import gameplay_action

PRESAVED_DIRECTORY = 'agent/preprocessed/'


def match_actions_with_states(game: cereal_bar_game.CerealBarGame, states: game_states.GameStates):
    """Matches the states (environment and cards) with the actions taken by both players."""
    game_info_idx: int = 0
    game.set_hexes(states.hexes)
    game.set_objects(states.objects)
    for i, action in enumerate(game.get_actions()):
        # Every time a movement is taken aligns with a game state in `states`.
        if isinstance(action, gameplay_action.MovementAction):
            game.set_action_state(i,
                                  states.state_deltas[game_info_idx],
                                  posterior_info=states.state_deltas[game_info_idx + 1])
            game_info_idx += 1
        elif isinstance(action, gameplay_action.FinishCommandAction):
            game.set_action_state(i, states.state_deltas[game_info_idx])


def load_from_raw_data(data_arguments: data_args.DataArgs,
                       game_arguments: game_args.GameArgs,
                       splits: List[dataset_split.DatasetSplit],
                       split_dir: str = "",
                       randomly_split_trainval: bool = True) -> game_dataset.GameDataset:
    """Loads games from a JSON file."""
    train_games: Dict[str, cereal_bar_game.CerealBarGame] = dict()
    dev_games: Dict[str, cereal_bar_game.CerealBarGame] = dict()
    test_games: Dict[str, cereal_bar_game.CerealBarGame] = dict()

    logging.info('Loading from json file...')
    if dataset_split.DatasetSplit.TRAIN in splits \
            or dataset_split.DatasetSplit.UPDATE in splits \
            or dataset_split.DatasetSplit.VALIDATION in splits \
            or dataset_split.DatasetSplit.SPECIFIED in splits:
        with open(data_arguments.get_split_filename(dataset_split.DatasetSplit.TRAIN)) as infile:
            logging.info('Loading train data.')
            for game_id, game in json.load(infile).items():
                assert isinstance(game, dict)
                train_games[game_id] = cereal_bar_game.CerealBarGame(game, data_arguments)
    if dataset_split.DatasetSplit.DEV in splits or dataset_split.DatasetSplit.SPECIFIED in splits:
        with open(data_arguments.get_split_filename(dataset_split.DatasetSplit.DEV)) as infile:
            logging.info('Loading development data.')
            for game_id, game in json.load(infile).items():
                assert isinstance(game, dict)
                dev_games[game_id] = cereal_bar_game.CerealBarGame(game, data_arguments)
    if dataset_split.DatasetSplit.TEST in splits:
        with open(data_arguments.get_split_filename(dataset_split.DatasetSplit.TEST)) as infile:
            logging.info('Loading test data.')
            for game_id, game in json.load(infile).items():
                assert isinstance(game, dict)
                test_games[game_id] = cereal_bar_game.CerealBarGame(game, data_arguments)

    all_game_keys: List[str] = list(train_games.keys()) + list(dev_games.keys()) + list(test_games.keys())
    logging.info('Loaded %r games' % len(all_game_keys))

    # Load the tensor information
    all_states: Dict[str, game_states.GameStates] = dict()
    state_filename = data_arguments.get_game_state_filename()

    if os.path.exists(state_filename):
        logging.info('Loading game states from %r' % state_filename)
        with open(state_filename, 'rb') as infile:
            all_states = pickle.load(infile)
        logging.info('Loaded state file with %r games' % len(all_states))

    # First, check if we need to add the games
    num_missing: int = len([game_id for game_id in all_game_keys if game_id not in all_states])

    # Match up the games that were saved
    logging.info('Matching games with states...')
    for game_id, game in train_games.items():
        if game_id in all_states:
            match_actions_with_states(game, all_states[game_id])
    for game_id, game in dev_games.items():
        if game_id in all_states:
            match_actions_with_states(game, all_states[game_id])
    for game_id, game in test_games.items():
        if game_id in all_states:
            match_actions_with_states(game, all_states[game_id])
    logging.info('Matched games with states')

    logging.info('Train games: ' + str(len(train_games)))
    logging.info('Dev games: ' + str(len(dev_games)))
    logging.info('Test games: ' + str(len(test_games)))
    logging.info(str(num_missing) + ' games are missing game info')

    if num_missing > 0:
        raise ValueError('Currently, replaying for creating the game_states.pkl file is not supported.\nInstead, '
                         'please use agent/preprocessed/game_states.pkl as provided in the original repository.')
        logging.info('Replaying these games.')
        # Start the Unity server
        server: ServerSocket = ServerSocket(game_arguments.get_ip_address(), game_arguments.get_port())
        server.start_unity()

        num_since_save: int = 0
        num_saved: int = 0
        with get_progressbar('replaying games', num_missing) as pbar:
            for game_id in all_game_keys:
                if game_id not in all_states:
                    game: cereal_bar_game.CerealBarGame = None
                    if game_id in train_games:
                        game = train_games[game_id]
                    elif game_id in dev_games:
                        game = dev_games[game_id]
                    elif game_id in test_games:
                        game = test_games[game_id]
                    if not game:
                        raise ValueError('Did not find game ID ' + game_id + ' in any split')

                    this_all_states: GameStates = get_all_states_from_replay(game, game_arguments, server)
                    all_states[game_id] = this_all_states
                    num_since_save += 1
                    pbar.update(num_saved)
                    num_saved += 1
                if num_since_save > 0:
                    # Save the game states again if we ran a new game
                    with open(state_filename, 'wb') as ofile:
                        pickle.dump(all_states, ofile)
                    num_since_save = 0

        server.close()

    # Filter games which didn't get a game state
    for game_id in list(train_games.keys()):
        if game_id not in all_states:
            train_games.pop(game_id)
    for game_id in list(dev_games.keys()):
        if game_id not in all_states:
            dev_games.pop(game_id)
    for game_id in list(test_games.keys()):
        if game_id not in all_states:
            test_games.pop(game_id)
    logging.info('After computing game states:\nTrain games: %r\nDev games: %r\nTest games: %r' % (len(train_games),
                                                                                                   len(dev_games),
                                                                                                   len(test_games)))

    # Create the dataset.
    return game_dataset.GameDataset(train_games, dev_games, test_games, data_arguments, split_dir,
                                    randomly_split_trainval)


def load_presaved_data(data_arguments: data_args.DataArgs, split: dataset_split.DatasetSplit,
                       directory: str) -> Dict[str, cereal_bar_game.CerealBarGame]:
    save_dir: str = os.path.join(directory, str(split))
    args_file = os.path.join(save_dir, 'args.pkl')
    if not os.path.exists(save_dir) or not os.path.exists(args_file):
        raise ValueError('Cannot load data and/or args from ' + str(save_dir))

    with open(args_file, 'rb') as infile:
        loaded_args: data_args.DataArgs = pickle.load(infile)
        if loaded_args != data_arguments:
            raise ValueError('Loaded args were different than specified data args.')

    examples_dict: Dict[str, cereal_bar_game.CerealBarGame] = dict()

    with util.get_progressbar('loading presaved data ', len([_ for _ in os.listdir(save_dir)])) as pbar:
        for filename in sorted(list(os.listdir(save_dir))):
            pbar.update(len(examples_dict))
            if filename.endswith('.pkl') and filename != 'args.pkl':
                if split == dataset_split.DatasetSplit.TRAIN and filename == 'dataset.pkl':
                    continue
                example_id: str = filename.split('.')[0]
                with open(os.path.join(save_dir, filename), 'rb') as infile:
                    example: cereal_bar_game.CerealBarGame = pickle.load(infile)
                examples_dict[example_id] = example

                if len(examples_dict) >= data_arguments.get_maximum_number_examples() >= 0:
                    break

    return examples_dict


def load_data(split: dataset_split.DatasetSplit, data_arguments: data_args.DataArgs,
              game_arguments: game_args.GameArgs) -> game_dataset.GameDataset:
    if data_arguments.presaved(split, PRESAVED_DIRECTORY):
        # Load the presaved data and create a new game dataset.
        logging.info('Loading from presaved ' + str(split))
        if split == dataset_split.DatasetSplit.TRAIN:
            data = load_presaved_data(data_arguments, split, PRESAVED_DIRECTORY)
            dataset = game_dataset.GameDataset(data,
                                               dict(),
                                               dict(),
                                               data_arguments,
                                               randomly_split_trainval=False,
                                               presaved=True)
        else:
            # It's faster just to load from the single pickle file if loading the whole dataset.
            with open(os.path.join(PRESAVED_DIRECTORY, str(split), 'dataset.pkl'), 'rb') as infile:
                dataset = pickle.load(infile)
    else:
        logging.info('Generating data for ' + str(split))
        dataset: game_dataset.GameDataset = load_from_raw_data(data_arguments,
                                                               game_arguments,
                                                               [split],
                                                               randomly_split_trainval=False)
        # Save the dataset per-example.
        logging.info('Saving...')

        # Only save the entire dataset as a single binary if not processing the train dataset.
        dataset.save(split, PRESAVED_DIRECTORY, save_entire_dataset=split != dataset_split.DatasetSplit.TRAIN)
        logging.info('Saved')
    return dataset


def load_vocabulary(save_dir: str) -> List[str]:
    """ Loads an already-saved vocabulary into a list of strings.

    Input:
        save_dir: str. The directory where the vocabulary is stored.

    Returns: list of strings representing the ordered vocabulary.
    """
    with open(os.path.join(save_dir, 'vocab.tsv')) as infile:
        return [line.strip().split('\t')[1] for line in infile if line.strip()]
