"""Functions for training an agent."""
import logging
from typing import List

import numpy as np
import pycrayon

from agent.config import model_args
from agent.config import program_args
from agent.config import training_args
from agent.data import dataset_split
from agent.learning import util

SLACK_CHANNEL: str = ''


def train(args: program_args.ProgramArgs) -> None:
    """ Trains the model to generate sequences of actions using direct supervision on action sequences.

    Inputs:
        args (program_args.ProgramArgs): The arguments to training and running the program.
    """
    # Set up the simulator depending on whichever type of simulator is described by the arguments.
    training_arguments: training_args.TrainingArgs = args.get_training_args()

    crayon_client: pycrayon.CrayonClient = pycrayon.CrayonClient(hostname='localhost')
    logging.info('Starting experiment: ' + training_arguments.get_experiment_name())

    # Create a new experiment
    experiment: pycrayon.crayon.CrayonExperiment = crayon_client.create_experiment(
        training_arguments.get_experiment_name())

    if training_arguments.log_with_slack():
        util.send_slack_message(username=training_arguments.get_experiment_name(),
                                message='Starting!',
                                channel=SLACK_CHANNEL)

    # Save the arguments to the specified directory.
    program_args.save_args(args, training_arguments.get_save_directory())

    # Load the data.
    train_dataset = load_data(dataset_split.DatasetSplit.TRAIN, training_arguments, args.get_game_args())
    dev_dataset = load_data(dataset_split.DatasetSplit.DEV, training_arguments, args.get_game_args())

    dataset = GameDataset(train_dataset.get_games(dataset_split.DatasetSplit.TRAIN),
                          dev_dataset.get_games(dataset_split.DatasetSplit.DEV),
                          dict(),
                          args.get_data_args(),
                          randomly_split_trainval=False,
                          presaved=True)

    logging.info('Loaded ' + str(len(dataset)) + ' games')

    # Save the validation split in a separate file so it can be reloaded later
    dataset.save_val_split(training_arguments.get_save_directory())
    task: model_args.Task = args.get_model_args().get_task()

    if args.get_model_args().get_decoder_args().pretrained_plan_predictor():
        # Load the vocabulary if the plan predictor was pretrianed.
        logging.info('Loading vocabulary from ')
        vocab_file: str = \
            '/'.join(args.get_model_args().get_decoder_args().pretrained_plan_predictor_filepath().split('/')[:-1])
        vocabulary = \
            load_vocabulary(vocab_file)
    else:
        # Otherwise, create and save the vocabulary.
        vocabulary: List[str] = dataset.get_instruction_vocabulary()
        dataset.save_vocabulary(training_arguments.get_save_directory())

    logging.info('Vocabulary contains ' + str(len(vocabulary)) + ' word types')

    model: ModelWrapper = get_model_wrapper(args.get_model_args(),
                                            training_arguments,
                                            vocabulary)
    logging.info('Created model:')
    logging.info(model)

    # Run the training part
    best_epoch_filename = model.train_loop(dataset,
                                           args.get_game_args(),
                                           args.get_evaluation_args(),
                                           training_arguments,
                                           experiment)
    model.load(best_epoch_filename)
    if training_arguments.log_with_slack():
        util.send_slack_message(username=training_arguments.get_experiment_name(),
                                message='Model finished training! Best epoch filename: ' + best_epoch_filename,
                                channel=SLACK_CHANNEL)

    if task == model_args.Task.PLAN_PREDICTOR:
        logging.info('Running on dev after training for plan prediction...')
        final_goal_acc = evaluate_goal_predictions(model,
                                                   dataset.get_examples(dataset_split.DatasetSplit.DEV),
                                                   args.get_game_args(),
                                                   args.get_evaluation_args())
        if training_arguments.log_with_slack():
            util.send_slack_message(username=training_arguments.get_experiment_name(),
                                    message='Final goal-prediction accuracy: ' + '{0:.2f}'.format(
                                        100. * final_goal_acc) + '%',
                                    channel=SLACK_CHANNEL)

    elif task == model_args.Task.ACTION_GENERATOR:
        logging.info('Running on dev after training for action prediction...')
        dict_results = evaluate_action_prediction(model,
                                                  dataset,
                                                  args,
                                                  'final',
                                                  True,
                                                  full_game=args.get_model_args().get_decoder_args().end_to_end())
        if training_arguments.log_with_slack():
            for metric_name, list_results in dict_results.items():
                util.send_slack_message(username=training_arguments.get_experiment_name(),
                                        message=str(metric_name) + ' after training: ' + str(
                                            np.mean(np.array(list_results))),
                                        channel=SLACK_CHANNEL)
