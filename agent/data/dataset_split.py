"""Defines different dataset splits."""

from enum import Enum


class DatasetSplit(Enum):
    TRAIN: str = 'TRAIN'
    DEV: str = 'DEV'
    TEST: str = 'TEST'

    VALIDATION: str = 'VALIDATION'

    # Used for the examples TRAIN - VALIDATION (i.e., the examples that should be used to update model parameteters.
    UPDATE: str = 'UPDATE'

    SPECIFIED: str = 'SPECIFIED'  # Specified split is ONLY for evaluation when exact example indices are given.

    def __str__(self) -> str:
        return self.value
