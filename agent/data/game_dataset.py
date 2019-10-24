"""The GameDataset class manages an entire dataset, including multiple splits of the data."""

import logging
import os
import pickle
import random
from typing import Dict, List, Set

from agent.config import data_args
from agent.data import cereal_bar_game
from agent.data import dataset_split
from agent.data import instruction_example
from agent import util


class GameDataset:
    def __init__(self,
                 train_games: Dict[str, cereal_bar_game.CerealBarGame],
                 dev_games: Dict[str, cereal_bar_game.CerealBarGame],
                 test_games: Dict[str, cereal_bar_game.CerealBarGame],
                 data_arguments: data_args.DataArgs,
                 split_dir: str = '',
                 randomly_split_trainval: bool = True,
                 presaved: bool = False):
        self._args: data_args.DataArgs = data_arguments

        self._train_games: Dict[str, cereal_bar_game.CerealBarGame] = train_games
        self._dev_games: Dict[str, cereal_bar_game.CerealBarGame] = dev_games
        self._test_games: Dict[str, cereal_bar_game.CerealBarGame] = test_games

        if not presaved:
            self._train_examples: Dict[str, instruction_example.InstructionExample] = \
                instruction_example.construct_examples(self._train_games,
                                                       data_arguments.get_maximum_instruction_index())
            self._dev_examples: Dict[str, instruction_example.InstructionExample] = \
                instruction_example.construct_examples(self._dev_games,
                                                       data_arguments.get_maximum_instruction_index())
            self._test_examples: Dict[str, instruction_example.InstructionExample] = \
                instruction_example.construct_examples(self._test_games,
                                                       data_arguments.get_maximum_instruction_index())
        else:
            self._train_examples: Dict[str, instruction_example.InstructionExample] = dict()
            for game_id, game in self._train_games.items():
                for example in game.get_examples():
                    self._train_examples[example.get_id()] = example
            self._test_examples: Dict[str, instruction_example.InstructionExample] = dict()
            for game_id, game in self._test_games.items():
                for example in game.get_examples():
                    self._test_examples[example.get_id()] = example
            self._dev_examples: Dict[str, instruction_example.InstructionExample] = dict()
            for game_id, game in self._dev_games.items():
                for example in game.get_examples():
                    self._dev_examples[example.get_id()] = example

        self._training_ids: Set[str] = set(self._train_games.keys())
        self._dev_ids: Set[str] = set(self._dev_games.keys())
        self._testing_ids: Set[str] = set(self._test_games.keys())

        if split_dir:
            # Load the validation/training split.
            update_id_file: str = os.path.join(split_dir, 'update_ids.txt')
            val_id_file: str = os.path.join(split_dir, 'validation_ids.txt')
            if not os.path.exists(update_id_file):
                raise ValueError('Given a split directory, expected the update ID file to exist: ' + update_id_file)
            if not os.path.exists(val_id_file):
                raise ValueError('Given a split directory, expected the val ID file to exist: ' + val_id_file)
            logging.info('Opening previously split data from directory ' + split_dir)

            with open(update_id_file) as infile:
                self._update_ids = set([line.strip() for line in infile])
            with open(val_id_file) as infile:
                self._val_ids = set([line.strip() for line in infile])
        else:
            # Create the validation/training split.
            logging.info('Resplitting validation/training with random=%r' % randomly_split_trainval)
            self._val_ids: Set[str] = set()
            self._update_ids: Set[str] = set()
            if data_arguments.get_validation_proportion() > 0:
                train_list: List[str] = sorted(list(self._training_ids))

                if randomly_split_trainval:
                    random.shuffle(train_list)

                split_idx: int = int((1 - data_arguments.get_validation_proportion()) * len(train_list))
                self._update_ids: Set[str] = set(train_list[:split_idx])
                self._val_ids: Set[str] = set(train_list[split_idx:])
            else:
                self._update_ids: Set[str] = self._training_ids

    def __len__(self) -> int:
        return len(self._train_games) + len(self._dev_games) + len(self._testing_ids)

    def get_examples(self, split: dataset_split.DatasetSplit, examples_filename: str = '',
                     max_action_length: int = -1) -> Dict[str, instruction_example.InstructionExample]:
        """Gets examples for a particular split of the data."""
        if examples_filename and split != dataset_split.DatasetSplit.SPECIFIED:
            raise ValueError('Providing a list of example IDs only supported for specified examples.')

        if split in {dataset_split.DatasetSplit.TRAIN, dataset_split.DatasetSplit.UPDATE,
                     dataset_split.DatasetSplit.VALIDATION}:
            examples: Dict[str, instruction_example.InstructionExample] = dict()
            for ex_id, example in self._train_examples.items():
                if len(example.get_action_sequence()) > max_action_length > 0:
                    continue
                split_id = ex_id.split('-')[0]
                if split == dataset_split.DatasetSplit.TRAIN:
                    examples[ex_id] = example
                elif split == dataset_split.DatasetSplit.UPDATE and split_id in self._update_ids:
                    examples[ex_id] = example
                elif split == dataset_split.DatasetSplit.VALIDATION and split_id in self._val_ids:
                    examples[ex_id] = example
            return examples
        elif split == dataset_split.DatasetSplit.DEV:
            if max_action_length > 0:
                raise ValueError('Limiting by action length not supported for this split')
            return self._dev_examples
        elif split == dataset_split.DatasetSplit.TEST:
            if max_action_length > 0:
                raise ValueError('Limiting by action length not supported for this split')
            return self._test_examples
        elif split == dataset_split.DatasetSplit.SPECIFIED:
            if max_action_length > 0:
                raise ValueError('Limiting by action length not supported for this split')
            if not examples_filename:
                raise ValueError('Must provide examples filename when specifying examples split')
            with open(examples_filename) as infile:
                examples_ids: List[str] = [line.strip() for line in infile if line.strip()]

            examples: Dict[str, instruction_example.InstructionExample] = dict()
            for ex_id, example in self._train_examples.items():
                if ex_id in examples_ids:
                    examples[ex_id] = example
            for ex_id, example in self._dev_examples.items():
                if ex_id in examples_ids:
                    examples[ex_id] = example

            return examples

    def get_games(self, split: dataset_split.DatasetSplit = None) -> Dict[str, cereal_bar_game.CerealBarGame]:
        """Gets all games for a particular split of the data (or all games in the dataset if split is None)."""
        if not split:
            all_games: Dict[str, cereal_bar_game.CerealBarGame] = dict()
            for game_id, game in self._train_games.items():
                all_games[game_id] = game
            for game_id, game in self._dev_games.items():
                all_games[game_id] = game
            for game_id, game in self._test_games.items():
                all_games[game_id] = game
            return all_games

        if split in {dataset_split.DatasetSplit.TRAIN, dataset_split.DatasetSplit.UPDATE,
                     dataset_split.DatasetSplit.VALIDATION}:
            games: Dict[str, cereal_bar_game.CerealBarGame] = dict()
            for game_id, game in self._train_games.items():
                if split == dataset_split.DatasetSplit.TRAIN:
                    games[game_id] = game
                elif split == dataset_split.DatasetSplit.UPDATE and game_id in self._update_ids:
                    games[game_id] = game
                elif split == dataset_split.DatasetSplit.VALIDATION and game_id in self._val_ids:
                    games[game_id] = game
            return games
        elif split == dataset_split.DatasetSplit.DEV:
            return self._dev_games
        elif split == dataset_split.DatasetSplit.TEST:
            return self._test_games
        else:
            raise ValueError('Getting games with specified filename is not supported')

    def get_ids(self, split: dataset_split.DatasetSplit = None) -> Set[str]:
        """Gets all IDs for a particular split of the data, or all games if the split is None."""
        if not split:
            return self._training_ids | self._dev_ids | self._testing_ids
        elif split in {dataset_split.DatasetSplit.TRAIN, dataset_split.DatasetSplit.UPDATE,
                       dataset_split.DatasetSplit.VALIDATION}:
            return self._training_ids
        elif split == dataset_split.DatasetSplit.DEV:
            return self._dev_ids
        elif split == dataset_split.DatasetSplit.TEST:
            return self._testing_ids
        else:
            raise ValueError('Getting IDs of specified games is not supported')

    def get_instruction_vocabulary(self) -> List[str]:
        """Gets the vocabulary from the instructions in the dataset."""
        vocab_dict: Dict[str, int] = {}
        for game_id, game in self._train_games.items():
            if game_id in self._update_ids:
                for example in game.get_examples():
                    for token in example.get_instruction():
                        if token not in vocab_dict:
                            vocab_dict[token] = 0
                        vocab_dict[token] += 1

        return [wordtype for wordtype, count in vocab_dict.items() if
                count >= self._args.get_minimum_wordtype_occurrence()]

    def save_vocabulary(self, save_dir: str) -> None:
        """Saves the vocabulary to a TSV file."""
        vocab_f: str = os.path.join(save_dir, 'vocab.tsv')
        with open(vocab_f, 'w') as ofile:
            for i, word_type in enumerate(self.get_instruction_vocabulary()):
                ofile.write(str(i) + '\t' + word_type + '\n')

    def save_validation_split(self, save_dir: str) -> None:
        """Saves the validation and update game IDs."""
        if not self._val_ids:
            raise ValueError('Never split between training and validation')
        update_id_f: str = os.path.join(save_dir, 'update_ids.txt')
        val_id_f: str = os.path.join(save_dir, 'validation_ids.txt')

        with open(update_id_f, 'w') as ofile:
            ofile.write('\n'.join(list(self._update_ids)))

        with open(val_id_f, 'w') as ofile:
            ofile.write('\n'.join(list(self._val_ids)))

    def save(self, split: dataset_split.DatasetSplit, directory: str, save_entire_dataset: bool = True):
        """Saves the dataset to disk."""
        directory: str = os.path.join(directory, str(split))
        if not os.path.exists(directory):
            os.mkdir(directory)
        with util.get_progressbar('Saving dataset', len(self._train_games)) as pbar:
            for game_idx, (game_id, game) in enumerate(self._train_games.items()):
                with open(os.path.join(directory, game_id + '.pkl'), 'wb') as ofile:
                    pickle.dump(game, ofile)
                    pbar.update(game_idx)
        with open(os.path.join(directory, 'args.pkl'), 'wb') as ofile:
            pickle.dump(self._args, ofile)
        if save_entire_dataset:
            with open(os.path.join(directory, 'dataset.pkl'), 'wb') as ofile:
                pickle.dump(self, ofile)
