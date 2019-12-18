""" Various model initializations.

Classes:
    Initialization (Enum): Enumerates the possible ways to initialize parameters in a model.
"""

from enum import Enum
import logging
import torch
from torch import nn

from agent import util


class Initialization(Enum):
    XAVIER_NORMAL: str = 'XAVIER_NORMAL'
    KAIMING_UNIFORM: str = 'KAIMING_UNIFORM'
    NONE: str = 'NONE'

    def __str__(self) -> str:
        return self.value

    def initialize(self, param):
        if self == Initialization.XAVIER_NORMAL:
            nn.init.xavier_normal_(param)
        elif self == Initialization.KAIMING_UNIFORM:
            nn.init.kaiming_uniform_(param)


def initialize_rnn(rnn: nn.RNN) -> None:
    """ Initializes an RNN so that biases have values of 0 and weights are Xavier normalized.

    Args:
        rnn: nn.RNN. The RNN to initialize.
    """
    for name, param in rnn.named_parameters():
        # Set biases to zero
        if 'bias' in name:
            nn.init.constant_(param, 0.0)
        elif 'weight' in name:
            # Otherwise do Xavier initialization
            nn.init.xavier_normal_(param)


def load_pretrained_parameters(filepath: str, freeze: bool = False, module: nn.Module = None):
    logging.info('Loading parameters for action predictor from %s', filepath)

    # The loaded parameters are an ordered dictionary.
    for name, param in torch.load(filepath, map_location=util.DEVICE).items():
        if name not in module.state_dict():
            logging.warn('WARNING! !!!!!!!!! Loaded action predictor contained an unrecognized parameter: ' + name)
            continue
        if freeze:
            logging.info('Loading and freezing parameter %s', name)
        else:
            logging.info('Loading parameter %s', name)
        module.state_dict()[name].copy_(param)
        if freeze:
            froze: bool = False
            for my_name, my_param in module.named_parameters():
                if name == my_name:
                    my_param.requires_grad = False
                    froze = True
            if not froze:
                raise ValueError('Could not freeze parameters ' + name)
