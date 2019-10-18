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