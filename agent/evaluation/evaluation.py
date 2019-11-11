"""Functions for evaluating a trained model."""
from __future__ import annotations

from typing import TYPE_CHECKING

import logging
import os
import torch

from agent import util
from agent.config import model_args
from agent.config import program_args
from agent.data import dataset_split
from agent.data import loading
from agent.evaluation import plan_metrics
from agent.model.model_wrappers import create_model_wrapper

if TYPE_CHECKING:
    from typing import Dict, List
    from agent.data import cereal_bar_game
    from agent.data import instruction_example


def evaluate_games(args: program_args.ProgramArgs):
    program_args.check_args(args, True)
    logging.info(args)

    logging.info('Using device: ' + str(util.DEVICE))

    training_args = args.get_training_args()
    data_args = args.get_data_args()
    evaluation_args = args.get_evaluation_args()

    save_directory: str = training_args.get_save_directory()

    split: dataset_split.DatasetSplit = evaluation_args.get_split()

    # To keep results consistent, don't randomly split between training and validation data.
    # The validation set should already be a random sample of games given how the data was split in the first place.
    dataset = loading.load_data(split, data_args, args.get_game_args())

    logging.info('Loaded ' + str(len(dataset)) + ' games')

    vocabulary: List[str] = loading.load_vocabulary(save_directory)

    if torch.cuda.device_count() > 1:
        raise ValueError('Inference is not supported with multiple GPUs.')

    model = create_model_wrapper.get_model_wrapper(
        args.get_model_args(), training_args, vocabulary, load_pretrained=False)

    model.load(os.path.join(save_directory, evaluation_args.get_save_file()))
    model.eval()

    task: model_args.Task = args.get_model_args().get_task()

    with torch.no_grad():
        if task in {model_args.Task.ACTION_GENERATOR, model_args.Task.SEQ2SEQ}:

            if split == dataset_split.DatasetSplit.SPECIFIED:
                raise NotImplementedError

                examples: Dict[str, instruction_example.InstructionExample] = dataset.get_examples(
                    split, evaluation_args.get_examples_filename())

                logging.info('Evaluting ' + str(len(examples)) + ' specified examples')

                run_examples(model, examples, args.get_game_args(), eval_args)
            else:
                games: Dict[str, cereal_bar_game.CerealBarGame] = dataset.get_games(split)

                logging.info('Evaluating %r games from split %r' % (len(games), split))

                # TODO: Logging of results
                # TODO: Evaluation

        elif task == model_args.Task.PLAN_PREDICTOR:
            print(plan_metrics.plan_metric_results(model, dataset.get_examples()))
