""" Various model initializations.

Classes:
    Initialization (Enum): Enumerates the possible ways to initialize parameters in a model.
"""

from enum import Enum
from torch import nn


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
