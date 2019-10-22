"""Utilities for laoding data."""

import logging
import os
import pickle

from agent.config import data_args
from agent.config import game_args
from agent.data import cereal_bar_game
from agent.data import dataset_split
from agent.data import game_dataset
from agent import util

from typing import Dict


PRESAVED_DIRECTORY = 'agent/preprocessed/'


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
        for filename in os.listdir(save_dir):
            pbar.update(len(examples_dict))
            if filename.endswith('.pkl') and filename != 'args.pkl':
                example_id: str = filename.split('.')[0]
                with open(os.path.join(save_dir, filename), 'rb') as infile:
                    example: cereal_bar_game.CerealBarGame = pickle.load(infile)
                examples_dict[example_id] = example

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
        # TODO: Test these functions
        raise ValueError('Loading and processing game data from raw needs to be cleaned up!')
        logging.info('Generating presaved ' + str(split))
        dataset: game_dataset.GameDataset = load_game_data(data_arguments,
                                                           game_arguments,
                                                           [split],
                                                           randomly_split_trainval=False)
        # Save the dataset per-example.
        logging.info('Saving...')
        dataset.save(split, PRESAVED_DIRECTORY)
        logging.info('Saved')
    return dataset
