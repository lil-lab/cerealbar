""" Main function for Cereal Bar experiments. """
from __future__ import absolute_import

import os
import logging
import multiprocessing
import torch

from agent.config import util
from agent.config import program_args
from agent.simulation import replay
from agent.learning import training

if torch.cuda.device_count() >= 1:
    DEVICE: torch.device = torch.device('cuda')
else:
    DEVICE: torch.device = torch.device('cpu')


def main():
    """ Main function for Cereal Bar experiments. """
    multiprocessing.set_start_method('spawn')
    args: program_args.ProgramArgs = util.get_args()

    run_type: program_args.RunType = args.get_run_type()

    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('pyscreenshot').setLevel(logging.WARNING)
    logging.getLogger('slack').setLevel(logging.WARNING)

    logging.info(args)
    if run_type == program_args.RunType.TRAIN:
        logging.basicConfig(filename=os.path.join(args.get_training_args().get_save_directory(), 'train.log'),
                            level=logging.DEBUG)
        logging.getLogger().addHandler(logging.StreamHandler())
        logging.info('Using device: %s', str(DEVICE))

        training.train(args)
    elif run_type == program_args.RunType.REPLAY:
        replay.replay(args.get_game_args(), args.get_replay_args())
    elif run_type == program_args.RunType.EVAL:
        logging.basicConfig(filename=os.path.join(args.get_training_args().get_save_directory(), 'eval.log'),
                            level=logging.DEBUG)
        logging.getLogger().addHandler(logging.StreamHandler())

        evaluate_games(args)


if __name__ == '__main__':
    main()
