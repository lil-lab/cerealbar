""" Main function for Cereal Bar experiments. """
from __future__ import absolute_import

import os
import logging
import multiprocessing

from agent import util
from agent.config import util as config_util
from agent.config import program_args
from agent.evaluation import evaluation
from agent.simulation import replay
from agent.learning import training


def main():
    """ Main function for Cereal Bar experiments. """
    multiprocessing.set_start_method('spawn')
    args: program_args.ProgramArgs = config_util.get_args()

    run_type: program_args.RunType = args.get_run_type()

#    logging.getLogger('requests').setLevel(logging.WARNING)
#    logging.getLogger('matplotlib').setLevel(logging.WARNING)
#    logging.getLogger('pyscreenshot').setLevel(logging.WARNING)
#    logging.getLogger('slack').setLevel(logging.WARNING)

    if run_type == program_args.RunType.TRAIN:
        logging.basicConfig(filename=os.path.join(args.get_training_args().get_save_directory(), 'train.log'),
                            level=logging.DEBUG)
        logging.getLogger().addHandler(logging.StreamHandler())

        logging.getLogger('urllib3').setLevel(logging.WARNING)

        logging.info(args)
        logging.info('Using device: %s', str(util.DEVICE))

        training.train(args)
    elif run_type == program_args.RunType.REPLAY:
        replay.replay(args.get_game_args(), args.get_replay_args())
    elif run_type == program_args.RunType.EVALUATE:
        logging.basicConfig(filename=os.path.join(args.get_training_args().get_save_directory(), 'eval.log'),
                            level=logging.DEBUG)
        logging.getLogger().addHandler(logging.StreamHandler())

        evaluation.evaluate_games(args)


if __name__ == '__main__':
    main()
